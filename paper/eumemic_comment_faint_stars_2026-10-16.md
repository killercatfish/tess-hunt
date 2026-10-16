eumemic's fifth comment on https://github.com/eumemic/exoplanets/issues/2, 2026-10-16, answering reply 5
(paper/issue_reply_eumemic_5.md). Copied here for the record.

What it changes:
- They adopt our galaxy fix. Their catalogue has 27 signals with a TIC extended source within 30″ bright
  enough to cause the dip, most with a second TIC entry at the same position (a flagged duplicate, or a
  Gaia source with no parallax). Removing both from TRICERATOPS's nearby-star scenarios, with their light
  kept in the aperture as in our `--drop` option, changes none of their tiers. The change goes in their
  next release.
- New: per-sector centroids (8 sectors, mean offset 5.3″ east-northeast of TOI-913, from their 12 October
  measurement) reject both faint stars behind our residual NFPP: p = 0.0007 for TIC 407126406 and
  p = 4e-8 for TIC 407126397. TOI-913 (p = 0.49) and the 9.5″ giant (p = 0.62) still can't be told apart.
  They give the separations as 27.0″ and 57.2″; the preprint uses 26.5″ and 58.0″.
- Our harmonic test settles the 27.3 d question for them too.
- Version 2 describes their work correctly.
- TFOP: they applied on 8 October and haven't heard back.

What it would mean, not yet adopted: in triceratops_speckle_nogalaxy_scenarios.csv, those two stars carry
0.0175 and 0.0043 of NFPP 0.0226. Without them NFPP would be about 0.0007, under the 0.001 cut, and with
FPP 0.036 that meets Giacalone et al.'s "likely planet" criteria (not "validated", which needs
FPP < 0.015). This rests on another team's centroids and lands just under the cut, so it needs our own
per-sector centroid table first (pre-share checklist item 6). Our own pixel test of TIC 407126406
(pixel_vet_407126406.json) was inconclusive. Seeing-limited ground photometry would settle both stars.

Their comment, verbatim:

> Thanks, and good catch on the galaxy. We drop TIC entries flagged ARTIFACT or DUPLICATE but not extended
> sources, so we checked our whole catalog. 27 of our signals have a TIC extended source within 30″ bright
> enough to cause their dip, and, as at TOI-913, most of these galaxies have a second TIC entry at the same
> position: a flagged duplicate, or a Gaia source without a parallax, presumably the galaxy's core. Taking
> both out of TRICERATOPS's nearby-star scenarios, with their light kept in the aperture as you did,
> changes none of our tiers. We'll make the change in our next release.
>
> On the two faint stars behind your residual NFPP: our per-sector centroids (8 sectors, mean offset 5.3″
> east-northeast of TOI-913) give p = 0.0007 for TIC 407126406 at 27.0″ and 4×10⁻⁸ for TIC 407126397 at
> 57.2″, so they reject both as the source, while TOI-913 (p = 0.49) and the 9.5″ giant (p = 0.62) still
> can't be told apart. These are from our 12 October measurement; we hadn't quoted the faint stars before.
>
> Your harmonic test settles the 27.3 d question for us too.
>
> Version 2 describes our work correctly. On TFOP: we applied on 8 October and haven't heard back; we'll
> tell you if that changes.
