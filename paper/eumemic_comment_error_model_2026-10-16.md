eumemic's sixth comment on https://github.com/eumemic/exoplanets/issues/2, 2026-10-16 18:33 UTC, answering
reply 6 (paper/issue_reply_eumemic_6.md). Copied here for the record.

What it changes:
- How their p-values are made: the scatter of the 8 sector centroids about their mean is a common
  per-sector error (12.3″ per axis), and F = (n |mean − s|² / 2) / (RSS / (2(n − 1))) is compared with
  F(2, 14). No PRF formal errors and no assumed depth go in, but it assumes Gaussian scatter.
- A sign-flip test (each sector's error symmetric about the source) gives p = 0.008 for TIC 407126406,
  the smallest value possible with 8 sectors.
- They walk back "reject both": on their centroids TIC 407126406 is between 0.0007 and 0.008, depending
  on the error model.
- On the five sectors other than 12, 100 and 102 they get 0.011 where we get 0.64, so they ask for our
  per-sector positions to compare. Theirs are in validation/centroid_sectors_per_sector.csv.gz
  (key extra_407126408_5.45017).
- They agree: TIC 407126406 stays the open scenario, and the test is a seeing-limited observation during
  a transit.

Our check (10/16, scripts/compare_centroids.py, outputs in paper/centroids_compare_s196/): their test on
their table reproduces their numbers. The positions agree to 2.5–13″ in the five sectors; the gap is the
error model. Our injections put a dip on TIC 407126406 about 9″ closer to the target than the star, and
against that position their centroids give p = 0.04 (all 8) and 0.36 (the five). Whether their fit has
the same pull is the open question; reply 7 (paper/issue_reply_eumemic_7.md) asks.

Their comment, verbatim:

> Thanks for checking this before changing anything.
>
> We don't use per-sector error bars. The test takes the scatter of the 8 sector centroids about their
> mean as a common per-sector error (12.3″ per axis here) and compares F = (n |mean − s|² / 2) /
> (RSS / (2(n − 1))) with F(2, 14), so neither the PRF fit's formal errors nor an assumed depth enter. It
> does assume Gaussian scatter, though. None of our sector fits ran away (all 8 centroids are within 27″
> of TOI-913, and all 8 lie west of TIC 407126406), but a sign-flip test, which assumes only that each
> sector's error is symmetric about the source, gives p = 0.008 for TIC 407126406, the smallest value it
> can give with 8 sectors.
>
> So on our centroids TIC 407126406 comes out between 0.0007 and 0.008 depending on the error model, and
> "reject both" in our last comment was too strong for it. On the five sectors other than 12, 100 and 102
> our centroids give 0.011 where yours give 0.64, so our centroids or error bars differ from yours in
> those sectors as well. If you post your per-sector positions we'll compare them with ours, which are in
> [validation/centroid_sectors_per_sector.csv.gz](https://github.com/eumemic/exoplanets/blob/main/validation/centroid_sectors_per_sector.csv.gz)
> (key extra_407126408_5.45017). Until they agree, keeping TIC 407126406 as the open scenario and testing
> it with a seeing-limited observation during a transit seems right to us.
