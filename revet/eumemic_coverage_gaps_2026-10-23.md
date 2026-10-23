# Which stars eumemic's searches leave out (board item e7, 2026-10-23)

*Read-only check of github.com/eumemic/exoplanets at commit d3daa0f (pushed 2026-10-22): their README,
`results_public/README.md`, `pipeline/build_allsky_targets.py` and `pipeline/search.py`, plus their
`all_signals*` tables. No Cortex time. Input for Josh's Tue 11/03 decision on whether and what we search.*

## What they cover

| Search | Stars | Periods |
|---|---|---|
| K/M dwarfs, T ≤ 11.5, R ≤ 0.75 R☉, Teff ≤ 5,300 K | 9,979 | 0.5–30 d, and 20–100 d |
| TOI hosts (known TOIs masked) | 6,430 | 0.5–30 d, and 20–100 d |
| M dwarfs 11.5 < T ≤ 12.5 (Teff ≤ 3,900 K, R ≤ 0.6 R☉) | 22,448 | 0.5–30 d |
| M dwarfs 12.5 < T ≤ 13.5 | 84,863 | 0.5–30 d |
| SPOC TCEs that never became TOIs, re-measured | 14,112 TCEs on 8,698 stars | the TCE's period |
| Full sky: every TIC 8.2 dwarf (lumclass DWARF, objType STAR) with T ≤ 13.5, Teff ≤ 6,500 K, R ≤ 1.5 R☉ not covered above | 4,039,203 searched | 0.5–30 d (or half the data span if shorter) |

Every search finds at most 3 signals per star (4 for TOI hosts), needs at least 3 good transits, and tries
transit durations only up to 8 hours.

**Our own search is inside theirs.** Our target list (Teff 2,400–5,200 K, within 100 pc, T < 13, dwarfs,
0.5–40 d) is covered by their K/M, faint-M and full-sky searches. The only extra piece is periods of
30–40 d on stars outside their bright K/M sample. Running our pipeline as it is on new stars would mostly
repeat their work.

## The gaps, largest overlap with what we can do first

1. **The search stops early (this is our n5 recall gap, in their pipeline too).** Their loop stops when a
   signal has SNR below 7 or repeats an earlier period, the same rule that made us miss 7 of their 17
   signals blind. In their published per-star tables (K/M and faint-M searches, 117,283 stars), the search
   ended early on **11,219 stars (about 10%)**: 10,776 stopped on a repeated period before a third signal,
   and 559 had a strong first signal (SNR ≥ 9) carried mostly by one transit, after which the search was
   over by the second signal. Counted with `scripts/eumemic_stop_counts.py`.
   - Caveat: many repeat stops are correct (the repeat is the star's variability). These are stars where a
     second look *could* find something, not stars where something is missing.
   - Caveat: the full-sky search's per-star table isn't public, so the same count can't be made for its
     4 million stars.
2. **Periods of 30–100 days on the faint M dwarfs and the full sky.** Only the 9,979 bright K/M dwarfs and
   the TOI hosts were searched past 30 d. The faint M dwarfs (107,311 stars) and the full sky stop at 30 d.
   Long periods need long baselines and three transits, so the yield per star is low, but nobody else has run
   these stars through their pipeline.
3. **Long transits.** Durations are capped at 8 h. This matters only for larger stars at long periods (a
   1.5 R☉, 1.2 M☉ star gives about 8 h at 30 d and 10 h at 60 d), so it mostly overlaps with gaps 2 and 4.
4. **Whole classes of stars left out by design:** hotter than 6,500 K, larger than 1.5 R☉, subgiants and
   giants, stars with no TIC lumclass, and anything fainter than T 13.5. Small planets are hard to see there.
   This is the board's parked item e4 (subgiants and young stars). Not counted: VizieR's TIC 8.2 service timed
   out on whole-sky counts.
5. **Periods under 0.5 days.** Every one of their searches starts at 0.5 d, and so does ours. Dedicated
   ultra-short-period searches exist in the literature; I haven't checked how complete they are.
6. **Stars without a ready-made light curve.** Their index found TESS-SPOC, QLP or SPOC light curves for
   4,086,108 of the 4,166,638 full-sky stars, and searched 4,039,203. About 80,000 have no light curve
   product at all, and reaching them would mean doing our own photometry from full-frame images.
7. **New sectors.** The full sky used Sectors 1–104. Later sectors can push weak signals over threshold,
   which makes a recurring re-search a possible job. A recurring Cortex timer needs Josh's OK.

## What I'd suggest for 11/03 (Claude proposed; Josh decides)

- **First: fix n5, then re-search the 11,219 stars where their search stopped early.** It's our own known
  weakness, the fix is validated on known planets before use, and the star list comes straight from their
  tables. Cortex cost (corrected 10/23; the first version said about a day): the pilot measured 254 s per
  star on average, downloads included, so 11,219 stars take about 5.5 days on 6 workers before the n5 change,
  and roughly 7–11 days after it, since the search now goes on longer (not yet measured). 10 workers, or the
  K/M and brighter faint-M stars first (about 2,960 stars, 2–3 days), would shorten it.
- **Maybe later: 30–100 d on the 107,311 faint M dwarfs**, if the first job finds anything. Our period cap
  (40 d, CHANGELOG 2026-10-09) would have to rise, which is a threshold change Josh approves.
- **Not now:** hot, large and evolved stars (gap 4), periods under 0.5 d (gap 5), and our own photometry
  (gap 6). Each is a new method, not a re-run, and weighs against HKOS v1 (12/18).
