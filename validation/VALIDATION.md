# Step 0.5 validation (2026-10-09, Cortex; final = run 3, after both secondary-test fixes)

Raw machine output: `validation/out/VALIDATION.md` on Cortex (run 1, before the fix: `VALIDATION_run1.md`).
Sets are frozen in `validation/known_planets.csv` (20 TESS-discovered hosts, 26 planets, Rp < 4 R⊕,
Teff < 5200 K, d < 100 pc) and `validation/known_ebs.csv` (10 Prša+2022 detached EBs; 5 shallow 0.5–5%, 5 deep).

## Known planets
| | run 1 | run 2 (robust secondary) | run 3 (+ leave-one-out scan, final) |
|---|---|---|---|
| hosts with ≥1 planet at the right period | 18/20 | 18/20 | **18/20** |
| planets at the right period | 23/26 | 23/26 | **23/26** (+1 only at an alias) |
| recovered planets surviving every hard test | 21/23 | 22/23 | **23/23** |
| EBs correctly rejected / detected | 9/9 | 9/9 | **9/9** (0 survivors on any EB star) |
| secondary-test fails, all passing signals | 20 | 12 | 6 |

All recoveries are at the catalog period within 1%. Recovered planets include LHS 475 b (0.99 R⊕),
TOI-6716 b (0.98 R⊕), TOI-1450 A b (1.13 R⊕), and all three of TOI-663 b/c/d and TOI-1260 b/c/d.

**Misses (3 planets):**
- **HD 15906 b, c**: only 2 sectors (4, 31). Not enough transits in TESS alone; the discovery relied on CHEOPS. Expected.
- **TOI-2443 b** (15.7 d): 1 sector. Found only at an alias. Expected given ≥3 transits.

**Wrongly killed in runs 1–2, fixed in run 3:** TOI-1450 A b (run 1: stray events from another signal) and
TOI-2540 b (runs 1–2: an "eccentric secondary" that was one coincident dip). Both fixes are in CHANGELOG.
Both were found on this validation set, so treat these numbers as somewhat optimistic for unseen stars.

## Known eclipsing binaries
- Detected at the EB period (or ×2/×½): **9/10**. TIC 192111972 (P = 22.8 d) had too few eclipses.
- **Correctly rejected: 9/9.** No survivor of any kind on any EB star.
- Most common killers: sector consistency, size, harmonic (the secondary re-surfacing), shape, odd/even.
- Margin note: after the fix, TIC 202509016 is killed by sector consistency alone (run 1: also secondary).

## Injection-recovery grid (2 quiet stars, 50 injections)
Recovered = right period (±1%) **and** passes SDE ≥ 9, SNR ≥ 7, ≥ 3 transits. Same map on both stars:
TIC 14724388 (M, 0.59 R☉, 4 sectors) and TIC 233684978 (K, 0.79 R☉, 24 sectors).

| Rp (R⊕) \ P (d) | 1 | 3 | 7 | 15 | 30 |
|---|---|---|---|---|---|
| 0.75 | – | – | – | – | – |
| 1.0  | ✓ | – | – | – | – |
| 1.5  | ✓ | ✓ | ✓ | ✓ | – |
| 2.0  | ✓ | ✓ | ✓ | ✓ | ✓ |
| 3.0  | ✓ | ✓ | ✓ | ✓ | ✓ |

**SNR ≥ 7 is the binding cut.** For example, the 1 R⊕ / 3 d injections were found at exactly the right
period (SDE 10–15), but with SNR 5.6–6.2. The validation planets near 1 R⊕ were recovered because their
hosts are smaller and/or have more sectors. Third quiet star dropped: TIC 71038757 has a persistent 0.62 d
signal (likely rotation/spots) that the kill tests rejected.

## Kill-test behaviour (all 69 threshold-passing validation signals)
- `contamination` flags 58/69. At small depths almost any star within 42″ is "capable", so it barely ranks
  anything. It's soft-only, so it does no harm, but it carries little information. TRICERATOPS is the real test.
- `known` flags 64/69, as expected on a validation set.
- `systematics` 0 fails: too few stars for the run-level test to bite. It matters on the pilot.

## Runtime
Median 333 s per star, max 3,501 s (40-sector CVZ star), 4.9 CPU-h for 33 stars on 6 workers.
Pilot estimate: 200 × ~330 s / 6 workers ≈ **3–5 h wall-clock**, longer if the sample has many CVZ stars.

## Audit step
See `AUDIT_COMPARISON.md`. qwen3vl and qwen38 misread statistics; `claude -p` from the Mac reads them
correctly and found real pipeline issues. Backend is now `mac_claude` (`scripts/audit_from_mac.sh`).

## Bugs found and fixed during validation
1. TLS fill-factor bug: durations 20× too short and SNR about 4× too low on multi-year data. Biggest find.
2. Secondary test hijacked by stray events from another signal (robust per-epoch combine).
3. Transient MAST errors: retry with backoff.
4. Report/runtime bookkeeping; `summary.json` not refreshed after postprocess.
