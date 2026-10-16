Thanks. I'm glad the galaxy check was useful across your catalogue, and thanks for confirming that version 2 describes your work correctly.

The faint-star result matters a lot here. Those two stars carry almost all of our remaining NFPP: 0.0175 from TIC 407126406 and 0.0043 from TIC 407126397, out of 0.023. Without both, NFPP would be about 0.0007, just under the 0.001 cut, which with FPP 0.036 would meet Giacalone et al.'s "likely planet" criteria. Because that lands so close to the cut, I checked it with our own per-sector centroids before changing anything (scripts/centroid_per_sector.py in https://github.com/killercatfish/tess-hunt).

Method: in each 2-minute sector I stack the difference images, fit them with the target's out-of-transit image shifted over a grid (±3.5 px, 0.1 px steps), and take the best shift as that sector's centroid. To get error bars, for each star I inject a dip of the fitted depth at that star's position into 60 stacks built at off-transit phases (real noise and systematics), refit, and use the recovered positions' mean and covariance. At this SNR the fit sometimes runs to the edge of the grid (Sectors 12, 100 and 102 do here), so the errors are heavy-tailed. I therefore calibrate the summed statistic empirically, by drawing one injected recovery per sector, rather than reading it off a χ² table.

Results for the 5.45 d signal at 196 ppm (p values for "the dip is on this star"):

| Star | Separation | p (Gaussian χ², 16 dof) | p (calibrated) | p (calibrated, without the 3 edge sectors) |
|---|---|---|---|---|
| TOI-913 | 0″ | 0.48 | 0.48 | 0.99 |
| TIC 407126405 (giant) | 9.5″ | 0.44 | 0.44 | 0.99 |
| TIC 407126406 | 26.5″ | 0.00014 | 0.022 | 0.64 |
| TIC 407126397 | 58.0″ | ~0 | < 5×10⁻⁶ | 0.034 |

The target and giant numbers match yours. The 58″ star is rejected in every version. The 27″ star depends on the error model. My Gaussian version gives 0.00014, close to your 0.0007, but the calibrated value is 0.02. That comes mostly from the sectors that don't localise, and it moves with the assumed depth: 0.21 at 150 ppm, 5×10⁻⁶ at 250 ppm. As a control, TOI-913 b (912 ppm) gives p = 0.97 for the target, 0.30 for the giant and < 5×10⁻⁶ for both faint stars.

So TIC 407126397 can come out (NFPP would then be about 0.018), but TIC 407126406 can't. It stays the open scenario, and a seeing-limited look during a predicted transit (it would need a ~23% eclipse at T = 17) is the clean test. How do you get your per-sector uncertainties? If they come from the PRF fit's formal errors, that could explain the difference. (Small point: you give the separations as 27.0″ and 57.2″; we have 26.5″ and 58.0″, probably different catalogue epochs or positions. It doesn't change anything.)

Good luck with the TFOP application, and the joint-filing offer stands.
