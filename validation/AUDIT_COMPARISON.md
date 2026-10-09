# Survivor audit: qwen3vl vs qwen38 vs claude -p (2026-10-09)

Same prompt, same inputs (diagnostic PNG + summary JSON), on all **24 validation survivor signals**.
All of them are known planets, so every "this isn't a planet" claim can be checked against the truth.
Notes sit side by side on Cortex: `validation/out/audit_compare/<TIC>/sig<N>.audit.{qwen3vl,qwen38,claude}.txt`.

| | qwen3vl (Cortex) | qwen38, thinking off (Cortex) | claude -p (Mac, fresh, Read-only) |
|---|---|---|---|
| time / candidate | 21 s | 49 s | 15 s |
| failures | 0/24 | 0/24 | 0/24 |
| reads the "known" match correctly (= recovery) | **no**: calls it "likely blend / false positive" in ~8 of the first 9 | yes | yes |
| treats sub-2σ odd/even or secondary as evidence | constantly (σ = 0.02 called an "asymmetry") | most notes (2.1σ called "a strong indicator of an EB") | no: says "not significant", "probably noise" |
| reads p-values the right way round | no | often no (passing p called "inconsistent") | yes |
| invented facts | several ("35 nearby stars", "injection overfitting") | some (calls TOI-5704 V-shaped when the U fit wins by Δχ² = 22) | 2 minor slips (calls MAST's real "sector 1751" a labelling bug; says one already-masked planet might be unmasked) |
| found real pipeline problems | no | no | **yes**, see below |

## Real issues the Claude audits surfaced (now on the fix list)
1. **Baseline offset after detrending.** In about 15 of 24 folds the out-of-transit baseline sits +100–400 ppm
   above zero. The biweight is partly fitting the transit, which biases depth and every depth-based kill test.
   Standard fix: re-detrend with the found transits masked before the kill tests run.
2. **Stale "systematics n/a" on the PNG.** The plot is drawn before the run-level test runs. Fixed (label).
3. **Headline depth vs core depths disagree.** TLS depth averages over the whole transit including ingress;
   the kill tests use the central 60%. The definitions differ, but Rp should probably use a fitted depth.
4. **BLS cross-check disagreement goes unflagged** (TIC 231949697: TLS 0.907 d, BLS 39.5 d). It's recorded but not surfaced.

## Caveat
The grading was done by Claude (me), so it's Claude scoring Claude. The qwen failures are easy to verify
against the facts line in each case. Spot-check a few of the `.claude.txt` notes yourself before trusting it.

## Decision
Audit backend = **mac_claude** (`scripts/audit_from_mac.sh`). Cortex models stay available via `backend: cortex_vlm`.
