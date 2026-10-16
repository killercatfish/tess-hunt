Thanks, that explains it. I ran your F test and sign-flip test on your table and get your numbers: p = 0.0006 and 0.008 for TIC 407126406, and 4.6×10⁻⁸ for TIC 407126397 (F test).

Our per-sector positions are in [paper/centroids_compare_s196/per_sector.csv](https://github.com/killercatfish/tess-hunt/blob/main/paper/centroids_compare_s196/per_sector.csv), in arcsec east and north of TOI-913 like yours. The comparison is scripts/compare_centroids.py.

| Sector | Ours (E, N) | Yours (E, N) | Apart |
|---|---|---|---|
| 12 | 79.2, 1.3 (ran to grid edge) | 15.3, 1.7 | 64″ |
| 13 | 4.3, −1.4 | −0.3, −0.2 | 5″ |
| 65 | 10.8, 12.8 | 9.3, 0.1 | 13″ |
| 66 | 15.4, 21.5 | 21.1, 16.6 | 8″ |
| 93 | 7.3, 23.9 | 9.3, 22.3 | 3″ |
| 100 | 70.7, −9.5 (ran to grid edge) | −6.9, −0.4 | 78″ |
| 101 | 6.4, −1.0 | 8.0, −4.6 | 4″ |
| 102 | 32.8, −64.1 (ran to grid edge) | −17.3, −16.9 | 69″ |

In the five sectors other than 12, 100 and 102 the positions agree to within 3–13″. In those three sectors our fit ran to the edge of its ±3.5 px grid and yours didn't, so yours are the better positions there. The gap on the five sectors (your 0.011, our 0.64) therefore comes from the error model, not the positions: your F test on our five positions gives p = 0.003 for TIC 407126406. Our injection-calibrated errors (30–43″ per sector) are much larger than the 12.3″ scatter of your centroids. Your tighter scatter suggests ours are inflated by our fit's runaways, and I accept that point.

One thing in our injections matters for both methods, though. When we inject a 196 ppm dip on TIC 407126406, our fit measures it on average 18.5″ east of TOI-913, not at the star's 27.1″: it is pulled about 9″ toward the target, and lands 13–26″ out depending on the sector. If your centroids are compared with where a dip on that star would actually be measured, rather than with its catalogue position, your F test gives p = 0.04 for all 8 sectors and 0.36 for the five, and the sign flip gives 0.06. TIC 407126397 is rejected either way (F test 5×10⁻⁷).

The pull may come from our method alone. We fit the target's own out-of-transit image, shifted, within 4 px of the target, and a PRF fit may not have the same bias. The quickest check is the same injection in your pipeline: put a 196 ppm dip on TIC 407126406 in each sector's off-transit data and see where your centroids land. If they land near 27″, your rejection stands and I'll say so in the preprint. If they're pulled in like ours, the star stays open.

Either way I agree with your conclusion for now: TIC 407126406 stays the open scenario, and a seeing-limited observation during a transit is the clean test.
