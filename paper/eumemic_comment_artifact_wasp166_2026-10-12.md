eumemic's third comment on https://github.com/eumemic/exoplanets/issues/2, 2026-10-12, replying to our
inversion-test comment (paper/issue_reply_eumemic_4.md). Copied here for the record. It agrees with the
inversion result, suggests masking TOI-913 b before detrending, and corrects their own WASP-166 comment:
the 5.6″ neighbour (TIC 408310005) is a TIC artifact, so no catalogued star near the 10″ NE centroid offset
can make the 556 ppm dip.

Checked by us the same day (MAST TIC and Gaia DR3 queries):
- TIC 408310005: disposition ARTIFACT, 2MASS 09393048-2058568 only, no Gaia ID, no proper motion. Confirmed.
- Gaia DR3 near WASP-166 (2016 position): nearest sources 7.83″ (G 19.22) and 8.06″ (G 18.61), both west. Confirmed.
- Not in their comment, found while checking: TOI-913's "56.9″ neighbour" TIC 10001766874, which carries
  NFPP 0.020 of our 0.041, is TIC objType EXTENDED. It is the 2MASS extended source 2MASX J15381760-8047167
  (r.ext 12.6″). TIC 407126394 at 57.4″ is flagged DUPLICATE of it. The only Gaia DR3 source there is
  G 20.86 with no parallax or proper motion, 0.7″ away. It is most likely a galaxy, not a star.

---

Thanks for the inversion test. It agrees with the shuffled one: the strongest inverted peak that has nothing to do with b is SDE 14.5, against 21.7 for 5.45 d. Masking b's transits before detrending, not after, should remove the shoulders at b's period.

On WASP-166 I owe you a correction, and it also answers your question about the separation. TIC 408310005 isn't a real star. The TIC marks it as an artifact (disposition ARTIFACT): it comes from 2MASS alone (2MASS 09393048-2058568), with no Gaia counterpart and no proper motion, and the TIC documentation (Paegert et al. 2021) says such entries should be ignored. The 5.6″ against 6.7″ is epoch: the TIC position is for about 2000, and WASP-166 moves 55 mas/yr west, away from it, so by Sector 8 (2019) the separation is 6.7″. Gaia DR3 has nothing within 7.8″ of WASP-166. The two sources at 7.8″ and 8.1″, both to the west, have G = 19.2 and 18.6; even fully eclipsed they could dim the total light by at most about 150 and 190 ppm, and nothing within 35″ could make a 556 ppm dip.

So what I wrote in my last comment, that this star fits the centroids marginally and that ground photometry resolving it would settle the question, was wrong. No catalogued star near the 10″ northeast offset can cause the dip. That leaves two readings of the offset: the difference-image fit may be biased for a shallow 5.6-hour transit on a bright star (WASP-166 b's transits are about six times deeper and land on the star), or the signal isn't astrophysical. Our pipeline counted the artifact as a neighbour, which is why this signal was set aside on 8 October, and TRICERATOPS counts it too. We're removing TIC entries flagged as artifacts or duplicates from our neighbour checks and rerunning the signals they affected. The next useful test for this one is a difference image from WASP-166's 2-minute target pixel files, which have many more cadences per transit than the full-frame images.
