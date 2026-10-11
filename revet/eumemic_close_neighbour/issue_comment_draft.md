Follow-up, as promised: an independent re-vet of the other 16 stars (17 signals) in your 2026-10-08
list marked "close neighbour could produce the depth". Code: scripts/neighbour_geometry.py and
revet/eumemic_close_neighbour/ in https://github.com/killercatfish/tess-hunt. Not reviewed by eye
yet; treat it as a second opinion, not a verdict.

**Recovery:** all 17 signals are present in our light curves. 10 come out of our blind search at your
period, and 9 of those pass all our hard tests. The other 7 show up at your timing at 5.2–7.7σ. Our
search missed them blind because it stops at the first signal below threshold.

**Your flagged neighbour, excluded:** for 420529106, 76228620 and 48439430 a geometry check rules
out the flagged star. No eclipsing companion on it can match the required depth and 0.7–1.4× the
observed duration at P or 2P. For 408310006 our TRICERATOPS gives the 5.6" star an NEB probability
of about 1e-6.

**TRICERATOPS results** (4 × 1e6, SPOC apertures, no contrast curves yet):
- **408310006 (WASP-166), 27.017 d, ~2.8 Re:** FPP 0.013 ± 0.005, NFPP 4e-6. Holdout 4/4. ExoFOP has
  Gemini/SOAR speckle we haven't folded in yet. The TESS Ten Thousand EB catalogue (arXiv:2506.05631)
  noted extra transit-like events in S62/S89.
- **88407114, 1.4975 d, ~1.2 Re:** FPP 0.23, NFPP 7e-5 (the bound-companion scenario dominates).
- **231725883, 4.659 d:** FPP 0.073, NFPP 1.9e-3. Apertures existed for only 2 of 13 sectors, so we
  want to rerun this one.
- **420529106 / 146282666 / 306990399:** NFPP 0.024 / 0.014 / 0.039. These are driven by stars other
  than the one you flagged; ask for the TIC IDs if useful.

Full table and per-signal TRICERATOPS scenario tables are in the repo folder above. Happy to dig
into any of these with you.
