eumemic's seventh comment on https://github.com/eumemic/exoplanets/issues/2, 2026-10-18 23:24 UTC, answering
reply 7 (paper/issue_reply_eumemic_7.md). Copied here for the record.

What it changes:
- The pull is real and not specific to our method. In their calibration set (signals known to come
  from a neighbouring star), the six with centroid scatter 14–22″ per axis (TOI-913's is 12.3″) and a
  source 20–60″ away are all measured closer to the target than the source, by 3–14″ (mean 9 ± 1.5″,
  about a quarter of the separation). At higher SNR the pull is under 1″.
- With TIC 407126406's expected position pulled in by a quarter to a third (to 18–20″), their F test
  gives p = 0.01–0.03, so their centroids no longer reject it. That matches ours (p 0.02).
- TIC 407126397 (58″) stays rejected on their centroids too (p ≤ 1e-5).
- Both sides now agree: TIC 407126406 is the open scenario, and NFPP stays about 0.018.
- They will add the pull to their centroid validation note.

For the Engine's first job (board item e2, re-checking the 9 signals eumemic demoted on centroids
alone): the same pull applies to any low-SNR signal they rejected against a catalogue position, so
those 9 are worth checking against injection positions, not catalogue positions.

Their comment, verbatim:

> Thanks for the comparison. Our calibration set shows the same pull, so it isn't specific to your
> method. Among the signals we know come from neighbouring stars, the six whose centroids scatter by
> 14–22″ per axis (TOI-913's: 12.3″) and whose source is 20–60″ away are all measured closer to the
> target than the source, by 3–14″ (mean 9 ± 1.5″, about a quarter of the separation). At higher SNR
> the pull is under 1″.
>
> With the expected position of TIC 407126406 pulled in by a quarter to a third (to 18–20″), our F test
> gives p = 0.01–0.03, so our centroids don't reject it either; TIC 407126397 stays rejected
> (p ≤ 10⁻⁵). We agree TIC 407126406 stays the open scenario. We'll add the pull to our centroid
> validation note.
