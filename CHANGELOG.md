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
- BUG FIX (method, not threshold): TLS multiplies its duration estimate by a data "fill factor"
  (span covered / total baseline). On multi-year stitched data (~0.05) this made durations ~20x too
  short and TLS SNR ~4x too low (smoke test: L 168-9 b duration 0.07 h vs 1.45 h expected, and
  masking failed so iterations re-found the same planet). `search.py` sets the factor to 1.
- METHOD (found on the validation set, so flagged explicitly): the secondary-eclipse test now
  combines per-epoch depths robustly (drops single epochs > 5 sigma from the median when >= 5
  epochs). TOI-1450 A b (real planet, 40 sectors) was killed by a 6.4 sigma "secondary" at phase
  0.63 made by a few stray deep events belonging to a separate junk signal. A true secondary
  repeats every orbit, so clipping lone events doesn't weaken the EB test. Thresholds unchanged
  (3 sigma at 0.5, 5 sigma scan). Whole validation set re-run on this code.
- METHOD (approved by Josh 2026-10-09; found on validation, flagged): the off-phase secondary SCAN
  (phases 0.3-0.7) now scores each phase by its significance after leaving out the single most
  significant epoch. TOI-2540 b (2 sectors, 3 transits) was killed by an 8.4 sigma "eccentric secondary"
  that was one coincident dip from a separate 27.8 d event. Phase-0.5 test unchanged and strict;
  thresholds unchanged. Accepted risk: an eccentric EB with only 2 observed secondaries is no longer
  caught by this test alone (odd/even, size, shape, sector consistency still apply). Validation re-run.
- Audit default model: qwen38 with thinking disabled (qwen3vl misread statistics; qwen38 with
  thinking on spent its whole 4000-token budget thinking). Comparison vs claude -p in progress.
- METHOD: after the search, the light curve is re-detrended with all threshold-passing transits
  masked (trend fit out-of-transit, interpolated across), and kill tests + plots use that. Reason: the
  Claude audits saw the folded baseline sitting +100-400 ppm high in ~15/24 validation survivors, i.e. the
  biweight was partly fitting the transits, biasing every depth-based test. Search itself unchanged.
  NOTE: the 200-star pilot was started (Josh's call) on the code BEFORE this change.

## 2026-10-10
- THRESHOLD/METHOD (approved by Josh; found on validation, flagged): sector-consistency test now adds
  10% of the depth in quadrature to each sector's depth error (`sector_sys_floor_frac`) and drops the
  single most discrepant sector when >= 3 sectors (`sector_drop_worst`). Reason: after the masked
  re-detrend, real planets TOI-2018 b (one sector at 2x depth) and TOI-712 b (32 sectors, 3 products,
  chi2/dof 2.5) failed. Risk watched: EB TIC 202509016 was killed by this test alone.
- KNOWN LIMITATION (accepted by Josh 2026-10-10, option 1 of 3; Claude proposed): with the floor and
  worst-sector drop, EB TIC 202509016 now survives. It is a near-twin EB (both eclipses ~2.2%, P 38.60 d)
  found at P/2 = 19.30 d, so odd/even (0.4 sigma) and phase-0.5 secondary cannot see it; shape is not
  V-shaped enough; size 12.4 R_earth < 22; duration skipped (no TIC radius/mass). Only the soft `known`
  flag catches it here. Uncatalogued equal-depth EBs found at half period can therefore reach the
  survivor list; rely on review by eye and the audit. Alternatives declined: revert (kills TOI-712 b and
  TOI-2018 b) or a new deep-signal hard flag (new threshold, not added). No thresholds changed.

## 2026-10-11
- THRESHOLD (Claude proposed, Josh approved 2026-10-11): the sector-consistency test drops its worst
  sector only when a signal has >= 4 sectors with depth measurements (`sector_drop_min_sectors: 4`,
  was effectively 3). Reason: in the 200-star pilot both junk survivors (TIC 243514635, TIC 219495254)
  passed only because dropping one of 3 sectors left a 2-sector comparison with almost no power.
  Risk: a real planet with exactly 3 sectors and one discrepant sector can be killed again;
  validation run 6 measures this.
  Result (validation run 6, 2026-10-11): all 23 recovered planets still survive; EBs unchanged (8/9);
  sector-consistency fails over all passing signals 15 -> 17. No real planet was lost.

## 2026-10-12
- METHOD (approved by Josh 2026-10-12): neighbour lookups skip TIC entries that are not stars: disposition
  ARTIFACT or DUPLICATE (Paegert et al. 2021 say to ignore them) and objType EXTENDED (2MASS extended
  sources, mostly galaxies). One helper, `stellar.is_real_star`, used by the `contamination` kill test,
  `scripts/neighbour_geometry.py` and `scripts/pixel_vet.py`. Reason: eumemic found WASP-166's 5.6" neighbour
  (TIC 408310005) is a TIC artifact, which is why our contamination test failed that signal; our check then
  found TOI-913's 56.9" "neighbour" (TIC 10001766874) is 2MASX J15381760-8047167 and carried half its NFPP.
  `scripts/triceratops_fpp.py` gains `--drop` (removed after calc_depths, so their light still dilutes).
  Other re-vetted stars with non-star entries within 60": TIC 24621747 (duplicate, 11.3"), 147163875
  (galaxy + duplicate, 45"), 422677298 (artifact, 4.1", T 10.9). Each also has a real neighbour that keeps
  its verdict; the pilot's contamination results have not been rerun with the filter yet.
