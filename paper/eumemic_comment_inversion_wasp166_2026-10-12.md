eumemic's second comment on https://github.com/eumemic/exoplanets/issues/2, 2026-10-12, replying to our
FAP comment (paper/issue_reply_eumemic_3.md). Copied here for the record. It suggests the inverted-light-curve
test for TOI-913 and corrects our WASP-166 (TIC 408310006) depth and placement.

---

Thanks for running it, and for the window-function, alias and momentum-dump checks. FAP < 1.5% from the shuffled copies is a useful number next to the population rate, and your caveat is the right one: shuffling 1-day blocks keeps noise shorter than a day but breaks up systematics that last several days.

One test that keeps those systematics is to run the same TLS search, with the same masks, on the inverted light curve (flux reflected about its median). Inversion keeps the timing and timescale of every systematic but turns dips into bumps, so the strongest inverted peak shows how strong a signal this light curve's own systematics can produce. That is the single-star version of our 800,000-star test.

WASP-166 (TIC 408310006), 27.017 d. The depths differ mostly by definition:

- Our 563 ± 29 ppm is the mean depth in a 4.7 h box, from light curves detrended with the transits masked. Per sector (SPOC 2-minute): S8 480 ± 58, S62 550 ± 51, S89 572 ± 54, S99 673 ± 71 ppm, which agree (χ²/dof 1.5).
- A transit fit (batman + emcee, WASP-166 b masked) gives Rp/R* = 0.0225 ± 0.0007, b = 0.54 ± 0.08 and T14 = 5.6 ± 0.2 h. That is a depth of 556 ppm at mid-transit and Rp = 3.07 ± 0.09 R⊕ with the TIC radius.
- Your pipeline's 429 ppm and our search's 411 ppm are box depths from light curves detrended without masking the transit, which removes part of a 5.6-hour transit.

So about 556 ppm is the depth to give TRICERATOPS; 637 ppm is about 15% too deep.

Centroids. Before relying on the FPP, check where the dip is. We measured the difference-image centroid of the 27 d signal in every sector with transits: S8, S62, S89 and S99 (S35's difference image failed). All four sit northeast of WASP-166, at 6.0″ E 3.8″ N, 5.0″ E 6.3″ N, 8.3″ E 4.9″ N and 6.5″ E 15.8″ N: a mean offset of 10″ at position angle 40°. WASP-166 b's transits, measured the same way, centroid within 1–4″ of the star in S35, S62, S89 and S99 (its S8 fit is poor), so the offset isn't a problem with this star's images. We calibrated the test on 565 known planets: none is rejected at p < 0.001 and 3 at p < 0.01. The 27 d offsets reject WASP-166 at p = 0.007. The nearest star bright enough to cause the dip, TIC 408310005 (T = 15.2, 6.7″ east), fits only marginally (p = 0.02). So I wouldn't treat the 27 d signal as on WASP-166 yet. Ground-based photometry that resolves the 6.7″ neighbour would settle it.
