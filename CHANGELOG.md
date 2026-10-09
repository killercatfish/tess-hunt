# CHANGELOG

Thresholds and method changes. Every change to `config.yaml` thresholds gets a line here with the reason.

## 2026-10-09
- `search.period_max_d: 40` (spec said baseline/2). Multi-year baselines (~2,600 d) make a
  baseline/2 grid cost hours per star, and >=3 transits rules out nearly all long periods anyway.
  Long-period / single-transit search is deferred to a separate mode. Approved by Josh.
- Defaults approved by Josh: workers 6, 1 thread/worker, 50 GB cache, 6 GB free-RAM guard.
- Added kill test `size` (implied radius > 22 R_earth fails): not in the original 10, cheap and
  catches stellar companions whose shapes look box-like. Reason: deep EBs are the most common FP.
- Added scripted per-survivor audit (fresh read-only model session writes "reasons this might
  not be a planet"). Requested by Josh.
- Measured on Cortex: full TLS 0.5-40 d on TOI-700 (37 sectors, 119k binned pts, 547k periods)
  = 530 s single-thread. Typical stars are ~10x cheaper, so TLS always runs the full grid (no
  windowed shortcut); BLS is a recorded cross-check only.
- Added kill test `harmonic`: a re-search iteration whose period matches (x1, x2, x1/2) an
  earlier signal on the same star fails. Catches an EB's secondary resurfacing as a "new planet".
