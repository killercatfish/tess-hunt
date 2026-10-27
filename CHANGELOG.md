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

## 2026-10-23
- PROVENANCE (no threshold or method change; Claude proposed 10/12 as honesty upgrade n3): every output now
  says which code and settings made it. A run takes one stamp before the workers start (git commit, whether
  tracked files had uncommitted edits and which, a 12-character hash of the loaded config minus `paths`) and
  writes it to each star's `targets.provenance`, each `candidates/<tic>/sig*.json`, the systematics entry
  postprocess adds, and the header and rows of `report.html` and `VALIDATION.md`; `status` lists stars per
  stamp. The full settings behind each hash are kept in a new `configs` table. Databases made earlier gain
  the column on first open; their stars show as "unstamped". Scripts under `scripts/` are not stamped yet.
- NEGATIVES (no threshold or method change; Claude proposed 10/12 as honesty upgrade n2): `run`, `validate-run`
  and the new `negatives` command write `negatives.csv` and `negatives.md` next to the report: every signal that
  did not survive, with the tests it failed and the number that failed each (or, below threshold, the SDE, SNR
  or transit count that kept it out), plus counts per test. With the report's survivors they account for
  every signal found. Nothing is published until Josh decides where (repo or Zenodo).
- METHOD (board item n5; Claude proposed 10/18, Josh approved going ahead 10/23 as an overnight run; the values
  8 and 2 are Claude's choice, to be judged on that run): the iterative search no longer stops at the first
  signal below threshold. A signal that would pass except for having fewer than `min_transits` transits (a
  single or double deep event) is masked and the search goes on; otherwise it stops after `stop_after_weak: 2`
  below-threshold signals in a row (was effectively 1), and `max_iterations` goes 4 -> 8. Reason: on eumemic's
  re-vet list our blind search missed 8 of 17 signals (7 counting an alias): 4 behind a strong event with only
  1-2 transits (e.g. TIC 48439430: a 58,000 ppm single event at SNR 160 hid a 0.55 d signal), 1 behind a weak
  leftover of the same deep events, 3 because 4 iterations were used up on deep binary-like events. The
  `harmonic` test now compares only against earlier signals that passed threshold, as before this change
  (until now every earlier signal had). Thresholds are unchanged. Checked by `scripts/n5_check.sh` (validation
  set, the re-vet stars, the pilot) against copies of the old results; `scripts/n5_compare.py` prints both.

## 2026-10-26
- METHOD (Claude proposed after the n5 check, Josh approved 10/26; the value 3 is Claude's): new soft flag `late`.
  A survivor found after `late_max_rejected_before: 3` or more rejected signals on the same star is flagged and
  ranked lower, never rejected. Reason: searching longer (n5) let weak leftovers of masking through, the 2.58 d
  survivor behind binary TIC 1220444 (4 rejected before it) and pilot TIC 278593441 at 36.83 d (7 before it).
  A hard kill was ruled out because eumemic's 10.17 d signal on TIC 247166992 has 4 rejected before it too.
  Replayed on the n5 results (`revet/n5_check_2026-10-26.md`): exactly those 3 flagged; every other survivor,
  known planets included, had 2 or fewer.

## 2026-10-27
- RUN (Claude proposed, Josh approved): kcfgamer runs the whole calibration set (`MACHINE=all` in
  `scripts/calibration_run.sh`); Cortex no longer takes a fifth. Cortex's 559-star run is going slower than
  forecast (223 done at 1:40pm ET, 61 of them since 6am), and calibration shouldn't wait behind it. Cortex keeps
  the 559 run and its survivor checks.
- METHOD (board item n1; Josh approved 10/26; the values are Claude's): two per-survivor checks, run after a
  search with `python -m tesshunt survivor-checks` (`tesshunt/survivor_checks.py`), both soft flags (ranked
  lower, never rejected). They are items 1 and 7 of the pre-share checklist, done by hand for TOI-913 in October.
  `fap`: TLS on `survivor_checks.fap_trials: 100` copies of the light curve with 1-day blocks
  (`fap_block_d: 1.0`) shuffled within each sector, the star's earlier signals masked as the search had them;
  flagged when more than `fap_max: 0.01` of copies reach the signal's SDE anywhere in 0.5-40 d. `inversion`:
  the flux reflected about its median before prep, TLS iterated `inversion_iters: 4` times with the same masks;
  flagged when the strongest inverted peak reaches the signal's SDE.
  Checked on Cortex 10/27 against October's TOI-913 numbers (8 trials only, as a code check): with TOI-913 b,
  TOI-913.02 and the 27.3 d systematic masked, shuffled maximum SDE up to 18.2 (October, 200 trials: maximum
  18.8) against the signal's 23.6, so no copy reaches it; strongest inverted peak 16.3 at b's period (b's
  detrending shoulders; October 18.2) and 12.4 elsewhere (October 14.5). Same pass on both. The shuffled
  median is higher than October's (16.8 against 13.1), probably because October used one constant error per
  point and the pipeline uses each point's own error; not checked further. Known limit: deep events the search
  never found stay in the shuffled copies. With only b and the systematic masked (TOI-913.02 left in, as in
  the pre-n5 pilot results), one copy in 8 reached 24.1 and the signal would be flagged. Searches since n5
  mask such events as their own iterations, so they are masked here too. Cost: about 13 minutes per survivor
  for 8 trials on 2 workers beside a running search; roughly 20-40 minutes per survivor at 100 trials.
- PROVENANCE (no threshold change; Claude, after the fresh-data rerun 10/27): every star now records which
  processing of each sector's file it used, in the new `targets.data_versions` column (author, processing
  version, data release and file date per sector). Reason: MAST replaced the sector 23-25 SPOC files with a 2023
  reprocessing under the same names after Cortex cached them on 10/10. The pipeline reuses its cache, so 22
  stars kept the old files. On current data, pilot survivor TIC 219495254 (15.35 d) is gone and known planets
  TOI-2018 b (odd/even, 3.8 sigma) and TOI-1450 A b (holdout) are rejected. TOI-913 is unaffected. The cache
  still doesn't notice replaced files; until it does, runs that need current data use a fresh cache
  (`CACHE_DIR` in `scripts/calibration_run.sh`).
- CALIBRATION SET (Josh decided 10/27 to calibrate the kill tests before any new search; the set is Claude's):
  `calibration/` holds 515 confirmed planets on 350 stars, 230 TFOP false positives and false alarms, and 120
  detached binaries on cool dwarfs, plus 59 planets at 40-100 d frozen for later. See `calibration/README.md`.
