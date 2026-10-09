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
