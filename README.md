# tess-hunt

Searches public NASA TESS light curves for transit-like signals, then tries hard to **kill** every
signal with automated false-positive tests. Output is a ranked short list of **candidates** for
human review. Nothing here is a discovery.

Code is written on the Mac and pushed to `github.com/killercatfish/tess-hunt` (public). It runs on Cortex at
`~/dev/tess-hunt` (`git pull` there; Cortex has a read-only deploy key). Run data (`data/`,
`results.db`, `candidates/`, `report.html`, `validation/out/`, `logs/`) stays on Cortex and is gitignored.

## Setup (Cortex, once)
    cd ~/dev/tess-hunt && ./setup.sh        # uv + Python 3.12 venv (numba-based TLS/wotan aren't safe on 3.14 yet)

## Everyday use
    ./run.sh                    # process queued stars; writes report.html at the end
    ./status.sh                 # done / queued / errors / signal verdicts / paused?
    ./pause.sh / ./resume.sh    # workers finish their current star, then idle until resumed
    scripts/overnight_tmux.sh   # same as run.sh, detached in tmux session "tess"
    scripts/serve.sh            # http://192.168.1.161:8765/report.html from any LAN device
    .venv/bin/python -m tesshunt audit      # skeptic notes for survivors -> report
    .venv/bin/python -m tesshunt requeue    # retry stars that errored (e.g. MAST outage)

Everything runs under `nice -n 19` / `ionice -c3`, with 1 thread per worker. Ctrl-C or a crash loses at
most the stars in progress: `running` rows go back to `queued` on the next start. Workers also
wait while free RAM is below `resources.min_free_ram_gb`.

## Changing things
All knobs live in **`config.yaml`**. **Any threshold change gets a line in `CHANGELOG.md` with the reason.**

- **Workers / resources:** `resources.workers`, `threads_per_worker`, `min_free_ram_gb`, `cache_max_gb`.
- **Target list:** the `targets:` block (Teff range, distance, Tmag, dwarfs only, sample size, seed).
  Then `python -m tesshunt targets --refresh` rebuilds the TIC pool (`data/catalogs/target_pool.csv`)
  and queues a new random sample. To queue your own list, call `db.add_targets(con, [{"tic": ...}], "mylist")`
  and run `./run.sh --labels mylist`.
- **Search:** `search.period_min_d / period_max_d` (capped at 40 d, see CHANGELOG), `bin_minutes`, `max_iterations`.
- **Pass threshold:** `thresholds.sde_min / snr_min / min_transits`.
- **Kill tests:** `kill_tests.*`. `hard_fail` lists tests whose failure rejects a signal. `soft_flag`
  tests (known object, bright neighbour) only flag.

## Pipeline
1. **Targets:** TIC M/K dwarfs (Teff < 5200 K, d < 100 pc, Tmag < 13), random sample.
2. **Data:** every sector (SPOC 2-min preferred, else TESS-SPOC, else QLP), cached in `data/cache/<TIC>/`.
   Upward-only sigma clip, per-sector normalize, wotan biweight (window = 3 × the longest searched duration), stitched.
3. **Search:** full-grid TLS 0.5–40 d on 10-min bins with TIC stellar priors, BLS cross-check.
   Mask and re-search up to 3 more times. A signal passes at SDE ≥ 9, SNR ≥ 7 and ≥ 3 transits.
4. **Kill tests** (on full-cadence data, with earlier signals masked): known-object match (flag) ·
   harmonic of an earlier signal · odd/even · secondary (phase 0.5 and a 0.3–0.7 scan) · duration vs
   circular expectation · implied size · V-vs-U shape · run-level shared periods · bright neighbours
   (flag) · per-sector depth consistency · season-holdout prediction · injection recovery.
5. **Output:** `results.db`, `candidates/<TIC>/sig<N>.png|.json|.audit.txt`, `report.html`.

## Validation (Step 0.5)
    python -m tesshunt validate-run      # 20 known small-planet hosts + 10 known EBs (frozen CSVs in validation/)
    python -m tesshunt validate-report   # -> validation/out/VALIDATION.md
    python -m tesshunt injgrid <TIC> <TIC> <TIC>   # radius x period recovery grid on quiet stars
