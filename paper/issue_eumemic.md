Hi! My home pipeline independently picked up the 5.4501 d / ~200 ppm signal on
TIC 407126408 (TOI-913) that your 2026-10-08 release lists with "close neighbour could
produce the depth". We looked hard at that neighbour, and it can't be the source:

- **TIC 407126405 is a background giant** (Gaia plx 0.16 ± 0.02 mas, ~5 kpc, R ≈ 10 Rsun).
  A 5.45 d orbit around it gives a transit duration of ~23–33 h vs the observed 2.4 h, and a
  grazing chord short enough for 2.4 h blocks only ~0.02% of its light, not the ~1.1% needed.
  TRICERATOPS gives it ~1e-26.
- **TRICERATOPS with the Gemini/Zorro 832 nm speckle curve** (8 × 1e6 draws): FPP 0.054,
  NFPP 0.042. The remaining NFPP comes from TIC 407126406 (26.5") and TIC 10001766874 (56.9").
- **Free-density transit fit:** rho = 2.43 [1.41, 3.39] rho_sun vs TIC 2.09 ± 0.45.
- **Survives:** QLP (top peak in a full 0.5–40 d search), 6 detrending variants, season and
  sector jackknifes, and no momentum-dump/gap coincidence. Holdout test: 3 of 4 seasons.
- **Joint fit with b:** P = 5.450138 ± 0.000016 d, T0 = BJD 2458628.6479, depth 196 ppm,
  T14 2.37 h, Rp ≈ 1.12 Re. Period ratio with b: 2.04.

I'm writing it up as a short preprint that credits your detection as the first. Happy to
share code and results. Do you have an ExoFOP account? A joint CTOI crediting both
searches seems like the right outcome.

— Josh Gold (github.com/killercatfish)
