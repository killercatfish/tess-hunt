eumemic's comment on https://github.com/eumemic/exoplanets/issues/2, 2026-10-12, copied here so the
preprint can cite it. It corrects their earlier 0.36″ centroid claim. Do not cite the 0.36″.
They said we may cite this comment for the faint-star result (last paragraph of the centroid part).

---

A correction before you cite anything: the 0.36″ is weaker evidence than I made it sound. It is the offset in our single best-quality difference image (Sector 13), which is what our 15″ test uses; the quality-weighted mean over the two sectors the pipeline fitted (13 and 101) was 4.4″. I've now rerun the same PRF centroid fit in all eight sectors and recorded the direction:

| Sector | Quality | Offset from target | Distance from TIC 407126405 | Position angle of offset |
|---|---|---|---|---|
| 12 | 0.50 | 15.4″ | 6.2″ | 84° |
| 13 | 0.69 | 0.4″ | 9.8″ | 226° |
| 65 | 0.64 | 9.3″ | 2.1″ | 90° |
| 66 | 0.27 | 26.8″ | 18.6″ | 52° |
| 93 | 0.24 | 24.1″ | 20.3″ | 23° |
| 100 | 0.53 | 6.9″ | 16.5″ | 267° |
| 101 | 0.56 | 9.3″ | 6.7″ | 120° |
| 102 | 0.22 | 24.2″ | 32.7″ | 226° |

The giant lies at position angle 74–77°. At this signal strength the positions scatter widely, and the quality-weighted mean is about 5″ from the target, toward the giant (position angle about 78°). So the difference images don't settle which of the two stars the dip is on, and they shouldn't be cited as evidence for the target. I should have checked every sector before saying they agreed. For the giant, your duration argument is the evidence that stands on its own.

The centroids do argue against the stars at 26.5″ and 56.9″ that drive your NFPP. No sector puts the centroid within 11″ of the first or within 30″ of the second, and in our calibration on known TOIs, signals from stars 21–63″ away gave offsets above 15″ in 98–100% of cases. You're welcome to cite this comment for that.

On MES 9–10: in our inverted light curves of 798,769 stars (the full-sky search of FGKM dwarfs brighter than T = 13.5), 37% ± 4% of vetted signals at MES 9–10 were false alarms, counting every pixel-check class. The figure is 40% for signals with no flagged neighbour and 31% for close-neighbour ones, each from fewer than 10 inverted events. That's a population average; your shuffled-block test on TOI-913's own light curve is the more direct number for this star.

Thanks for the re-vet of the other set-asides.
