# Kill-test calibration set (frozen 2026-10-27)

**Decided by Josh, 10/27:** calibrate the kill tests before any new search. The set and its sizes are
Claude's proposal.

**Why.** On 10/27 we reran the 21 stars whose light curves MAST had reprocessed. TOI-2018 b, a real planet
around a bright star, flipped from survivor to rejected (odd/even at 3.8σ). TOI-1450 A b failed the season
holdout. The validation set has 26 planets, which is too few to say how often the hard tests reject real
planets: 1 in 10 and 1 in 4 both fit it. This set has enough stars with known answers to give each test a
measured rate. It runs on freshly downloaded data.

## What's in it

| File | Rows | Stars | What it measures |
|---|---|---|---|
| `planets.csv` | 515 planets | 350 | How often each hard test kills a real planet |
| `false_positives.csv` | 230 TOIs (201 FP, 29 FA) | 230 | How often each test catches something that isn't a planet |
| `ebs.csv` | 120 binaries | 120 | Catch rate on detached eclipsing binaries around cool dwarfs |
| `long_period.csv` | 59 planets at 40–100 d | 58 | Frozen for the long-period search mode; **not run yet** (the search stops at 40 d) |

698 stars run in total, split between Cortex (every fifth star) and kcfgamer (the rest), by
`scripts/calibration_run.sh`. Every star is queued by its TIC number alone, so its radius, mass and Teff come
from the TIC exactly as in a search. The archive's published values are better and would flatter the size
and duration tests.

**Known bias.** Confirmed planets are mostly strong, clean signals; that's how they got confirmed. A new
planet would sit near our threshold. The report therefore splits the rejection rate by search SNR, and the
rate below SNR 10 is the one that applies to a new find. If that bin is small, the next step is injected
planets at low SNR (the injection grid), not more confirmed planets.

**Planets.** Confirmed transiting planets from the NASA Exoplanet Archive (`pscomppars`), excluding any
flagged as controversial. Host Teff < 5200 K and TESS magnitude < 14, P 0.5–40 d, Rp < 6 R⊕. That pool
has 583 hosts. All 121 hosts with a planet at 15–40 d are kept, because that's where the holdout test killed
pilot signals and where our own search is headed. The rest of the 350 are drawn at random (seed 20261027).
Every planet on a kept host is included, so a multi-planet star is judged on each planet. Radius mix:
176 below 1.5 R⊕, 204 at 1.5–2.5, 105 at 2.5–4, 30 above 4. 216 of the 515 were discovered by TESS.
10 hosts overlap the validation set.

**False positives.** TOIs that TFOP gave the disposition FP (an astrophysical false positive) or FA (a false
alarm), from the ExoFOP TOI list on 2026-10-27. Same star limits, P 0.5–40 d, and no star that also hosts a
kept planet. From the TFOP comments (keyword match, rough):

| Type | Count | Can our single-star tests catch it? |
|---|---|---|
| Nearby star or centroid offset | 91 | Mostly not: the dip is real in our aperture. Only the `contamination` soft flag and a centroid check can. |
| Eclipsing binary on the target (secondary, odd/even, V-shape, SB) | 44 | Yes, that's what odd/even, secondary and shape are for |
| Systematic or false alarm | 21 | Yes: holdout, sector consistency, systematics |
| Not stated | 74 | Unknown |

So catch rates are reported per type. A low catch rate on nearby-star false positives is expected and
isn't a test failure.

**Eclipsing binaries.** Detached binaries (morphology < 0.5) from the TESS EB catalog (Prša et al. 2022,
VizieR J/ApJS/258/16), P 0.5–40 d, TESS magnitude < 14, on cool dwarfs (TIC Teff < 5200 K and log g > 4,
from MAST). Two-thirds are shallow (primary depth < 5%, the kind that can pass for a planet), the rest deeper.

## Sources (raw downloads are not committed)

- Planets: `https://exoplanetarchive.ipac.caltech.edu/TAP/sync?format=csv&query=select pl_name,hostname,tic_id,
  pl_orbper,pl_tranmid,pl_trandur,pl_rade,pl_controv_flag,st_teff,st_rad,st_mass,st_logg,sy_tmag,sy_dist,
  disc_facility,disc_year from pscomppars where tran_flag=1 and st_teff<5200 and pl_orbper>0.5 and
  pl_orbper<100 and tic_id is not null and sy_tmag<15` (2026-10-27 14:30 UTC, 1,323 rows)
- TOIs: `https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv` (2026-10-27, 8,151 TOIs)
- Binaries: VizieR TAP, `SELECT TIC, Tmag, RAJ2000, DEJ2000, Per, Morph, "Dp-pf", "Ds-pf", BJD0 FROM
  "J/ApJS/258/16/tess-ebs" WHERE Morph < 0.5 AND Per > 0.5 AND Per < 40 AND Tmag < 14` (2,033 rows)

Rebuild: `python3 -I scripts/calibration_build.py PLANETS_CSV TOI_CSV EBS_CSV`. Catalogs change over time, so
a rebuild later won't give the same set. These CSVs are the frozen record.

## How it is scored (`scripts/calibration_report.py`)

Tested 10/27 on copies of Cortex's pilot and validation databases: the 10 hosts shared with the validation set
and the 10 validation binaries come out as the validation report has them. Copy each machine's
`results.db` into `calibration/out/<machine>/`, then run `.venv/bin/python scripts/calibration_report.py`; it
writes `calibration/out/CALIBRATION.md` and `calibration/out/calibration_rows.csv`.

- **Planets:** for each planet, is a threshold-passing signal found within 1% of its period? If so, which
  hard tests fail it? Per test: the fraction of found planets it kills (false-rejection rate), with a 95%
  interval. Also broken down by period (below and above 15 d), radius, brightness and search SNR.
- **False positives and binaries:** for each, a signal at the catalogue period (or twice, or half)? If so, is
  it rejected, and by which test? The tests credited are those that rejected the first signal found at that
  period, so `harmonic` isn't credited for the 2x and 1/2x echoes it rejects by design. Per test and per
  false-positive type: the catch rate.
- **The `systematics` test** compares periods across every star in a run, so a bigger run has more chance
  matches. It is recomputed over both machines' signals together and reported on its own, including how often
  it hits real planets by coincidence.
- **The data version** (processing version and data release) of every light-curve file will be recorded with
  the results. Not built yet; it has to be in place before the run.
