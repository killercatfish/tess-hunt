"""Transit fit for a multi-planet star: is the candidate's shape consistent with the host star?

One-off vetting tool, two stages (the fit needs emcee, which the pipeline venv doesn't have):
  prep (pipeline venv):  python scripts/transit_fit.py prep --tic 407126408 --out /tmp/fit/lc.npz \
                           --planet 11.099372,1636.3086,2.990 --planet 5.450098,1628.6592,2.361 \
                           --mask 1469.851,1648.0720,5.95
  fit  (venv w/ emcee):  python scripts/transit_fit.py fit --lc /tmp/fit/lc.npz --rho 2.086,0.25 --out /tmp/fit

Each planet gets P, t0, Rp/R*, impact b. Circular orbits. Two fits: one stellar density shared by all
planets ("joint"), and one density per planet ("free"). In the free fit, a candidate's density
should match the star's catalogue density and its sibling's; a blend on another star usually doesn't.
"""
import argparse, json, os, sys
import numpy as np

G = 6.674e-8
RHO_SUN = 1.408  # g/cm3


def parse(s):
    return tuple(float(x) for x in s.split(","))


def prep(a):
    sys.path.insert(0, os.path.expanduser("~/dev/tess-hunt"))
    from tesshunt import config, lightcurves, stellar
    cfg = config.load()
    star = stellar.tic_row(a.tic)
    sectors = lightcurves.fetch(cfg, a.tic)
    lc = lightcurves.prepare(cfg, sectors, lightcurves.detrend_window(cfg, star))
    sig = [dict(period=p, t0=t0, duration_h=d) for (p, t0, d) in [parse(x) for x in a.planet + a.mask]]
    lc = lightcurves.redetrend_masked(cfg, lc, sig)
    t, f, e = lc["time"], lc["flux"], lc["err"]
    keep = np.zeros(len(t), bool)
    for (p, t0, d) in [parse(x) for x in a.planet]:
        keep |= np.abs((t - t0 + 0.5 * p) % p - 0.5 * p) < 3 * d / 24
    for (p, t0, d) in [parse(x) for x in a.mask]:
        keep &= ~(np.abs((t - t0 + 0.5 * p) % p - 0.5 * p) < 1.0 * d / 24)
    ld = stellar.limb_darkening(a.tic)
    np.savez(a.out, t=t[keep], f=f[keep], e=e[keep], sector=lc["sector"][keep],
             planets=np.array([parse(x) for x in a.planet]), ld=np.array(ld))
    print(f"saved {keep.sum()} points, LD {ld}, star R={star.get('rad')} M={star.get('mass')}")


def fit(a):
    import batman, emcee
    from scipy.optimize import minimize
    d = np.load(a.lc)
    t, f, e, pl, ld = d["t"], d["f"], d["e"], d["planets"], list(d["ld"])
    rho0, rho_err = parse(a.rho)
    npl = len(pl)
    # per-planet data windows and batman setups (2-min cadence: no supersampling needed)
    win, mods, params = [], [], []
    for (P, t0, dur) in pl:
        w = np.abs((t - t0 + 0.5 * P) % P - 0.5 * P) < 3 * dur / 24
        win.append(w)
        pr = batman.TransitParams()
        pr.t0, pr.per, pr.rp, pr.a, pr.inc, pr.ecc, pr.w, pr.u, pr.limb_dark = t0, P, 0.02, 15, 89, 0, 90, ld, "quadratic"
        params.append(pr); mods.append(batman.TransitModel(pr, t))

    def a_over_r(rho, P):
        return (G * rho * RHO_SUN * (P * 86400) ** 2 / (3 * np.pi)) ** (1 / 3)

    def unpack(th, shared):
        # per planet: dP, dt0, log10 k, b ; then rho(s) ; then log jitter
        pp = th[:4 * npl].reshape(npl, 4)
        rhos = [th[4 * npl]] * npl if shared else list(th[4 * npl:4 * npl + npl])
        return pp, rhos, th[-1]

    def model(th, shared):
        pp, rhos, _ = unpack(th, shared)
        m = np.ones_like(t)
        for i in range(npl):
            P, t0 = pl[i][0] + pp[i, 0], pl[i][1] + pp[i, 1]
            k, b, rho = 10 ** pp[i, 2], pp[i, 3], rhos[i]
            ar = a_over_r(rho, P)
            if b >= ar:
                return None
            pr = params[i]
            pr.per, pr.t0, pr.rp, pr.a = P, t0, k, ar
            pr.inc = np.degrees(np.arccos(b / ar))
            m += mods[i].light_curve(pr) - 1
        return m

    def logp(th, shared):
        pp, rhos, lj = unpack(th, shared)
        if np.any(np.abs(pp[:, 0]) > 0.01) or np.any(np.abs(pp[:, 1]) > 0.1):
            return -np.inf
        if np.any(pp[:, 2] < -3) or np.any(pp[:, 2] > -0.7) or np.any(pp[:, 3] < 0) or np.any(pp[:, 3] > 1.2):
            return -np.inf
        if any(r <= 0.05 or r > 20 for r in rhos) or not (-12 < lj < -5):
            return -np.inf
        m = model(th, shared)
        if m is None:
            return -np.inf
        s2 = e**2 + np.exp(2 * lj)
        lp = -0.5 * np.sum((f - m) ** 2 / s2 + np.log(s2))
        if shared:  # catalogue density prior only in the joint fit; the free fit is the test
            lp += -0.5 * ((rhos[0] - rho0) / rho_err) ** 2
        return lp

    out = {}
    for shared in (True, False):
        k0 = [np.log10(np.sqrt(dep * 1e-6)) for dep in [1000, 191][:npl]] if npl == 2 else [-1.6] * npl
        th0 = []
        for i in range(npl):
            th0 += [0.0, 0.0, k0[i] if i < len(k0) else -1.6, 0.3]
        th0 += [rho0] if shared else [rho0] * npl
        th0 += [np.log(np.median(e) * 0.3)]
        th0 = np.array(th0)
        nll = lambda th: -logp(th, shared) if np.isfinite(logp(th, shared)) else 1e25
        th0 = minimize(nll, th0, method="Nelder-Mead", options=dict(maxiter=4000, xatol=1e-7, fatol=1e-3)).x
        ndim = len(th0); nw = max(32, 4 * ndim)
        scale = np.array(([1e-5, 1e-3, 0.02, 0.05] * npl) + [0.1] * (1 if shared else npl) + [0.1])
        p0 = th0 + scale * np.random.randn(nw, ndim)
        p0[:, 4 * npl:4 * npl + (1 if shared else npl)] = np.abs(p0[:, 4 * npl:4 * npl + (1 if shared else npl)])
        p0[:, 3:4 * npl:4] = np.abs(p0[:, 3:4 * npl:4])
        sampler = emcee.EnsembleSampler(nw, ndim, logp, args=(shared,))
        sampler.run_mcmc(p0, a.steps, progress=False)
        ch = sampler.get_chain(discard=a.steps // 2, flat=True)
        q = lambda x: [float(v) for v in np.percentile(x, [16, 50, 84])]
        res = {}
        for i, (P, t0, dur) in enumerate(pl):
            kk = 10 ** ch[:, 4 * i + 2]
            rho = ch[:, 4 * npl] if shared else ch[:, 4 * npl + i]
            ar = a_over_r(rho, P + ch[:, 4 * i])
            bb = ch[:, 4 * i + 3]
            T14 = (P / np.pi) * np.arcsin(np.sqrt(np.clip((1 + kk) ** 2 - bb**2, 0, None)) / ar / np.sin(np.arccos(bb / ar))) * 24
            res[f"P{P:.4f}"] = dict(period=q(P + ch[:, 4 * i]), t0=q(t0 + ch[:, 4 * i + 1]), k=q(kk),
                                    depth_ppm=q(1e6 * kk**2), b=q(bb), rho=q(rho), a_over_r=q(ar), T14_h=q(T14))
        res["acceptance"] = float(np.mean(sampler.acceptance_fraction))
        out["joint" if shared else "free"] = res
        print(("JOINT (shared density, catalogue prior)" if shared else "FREE (density per planet, no prior)"))
        for kname, r in res.items():
            if kname == "acceptance":
                print(f"  acceptance {r:.2f}"); continue
            print(f"  {kname}: depth {r['depth_ppm'][1]:.0f} (+{r['depth_ppm'][2]-r['depth_ppm'][1]:.0f}/-{r['depth_ppm'][1]-r['depth_ppm'][0]:.0f}) ppm  "
                  f"b {r['b'][1]:.2f} [{r['b'][0]:.2f},{r['b'][2]:.2f}]  rho {r['rho'][1]:.2f} [{r['rho'][0]:.2f},{r['rho'][2]:.2f}] rho_sun  "
                  f"T14 {r['T14_h'][1]:.2f} h")
    out["catalogue_rho"] = [rho0, rho_err]
    json.dump(out, open(os.path.join(a.out, "transit_fit.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep"); p.add_argument("--tic", type=int, required=True); p.add_argument("--out", required=True)
    p.add_argument("--planet", action="append", default=[]); p.add_argument("--mask", action="append", default=[])
    p = sub.add_parser("fit"); p.add_argument("--lc", required=True); p.add_argument("--rho", required=True)
    p.add_argument("--out", required=True); p.add_argument("--steps", type=int, default=6000)
    a = ap.parse_args()
    prep(a) if a.cmd == "prep" else fit(a)
