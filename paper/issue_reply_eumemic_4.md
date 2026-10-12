Thanks, the inversion test was quick to run, so here it is.

Same light curve, same prep and the same masks as the shuffled test (TOI-913 b, TOI-913.02 and the 27.3 d systematic). The flux was reflected about its median right after normalising, so the inverted copy also went through the outlier clip and the biweight detrend. Each search was repeated four times, masking the top peak each time.

- Real light curve: 5.4501 d at SDE 21.7, as before.
- Inverted, peaks 1 and 2: 11.0996 d at SDE 18.2 and 11.0994 d at SDE 15.6, both 5.3 h long. That's TOI-913 b's period. Their epochs sit about 0.2 d before and after b's transits, so they are the shoulders the biweight leaves next to a transit it didn't mask. They become dips once the flux is inverted. This is an artefact of our detrending, not a systematic in the star's light curve. It's the same effect you describe for WASP-166's depth.
- Inverted, peaks 3 and 4: 38.8 d at SDE 14.5 (3 transits) and 37.7 d at SDE 9.6. The 38.8 d peak is the strongest one in the inverted light curve that has nothing to do with b.

So the strongest peak this light curve's systematics produce is SDE 14.5, or 18.2 if you count b's shoulders. The 5.45 d signal is at 21.7. This is one inverted copy, so it's a comparison, not a probability. It agrees with the shuffled test, where the strongest null peak was 18.8. One more note: the real light curve's next peaks after 5.45 d are 33.6 d (SDE 15.9) and 32.6 d (SDE 14.0), each with only 5–6 transits. That's about the same level as the inverted 38.8 d peak, so long periods with few transits are where this light curve's noise floor sits.

Code: scripts/inversion_test.py in https://github.com/killercatfish/tess-hunt.

On WASP-166: thanks for sorting out the depths. I'll treat about 556 ppm as the depth, and our 637 ppm TRICERATOPS input as too deep. More important, your centroids mean the FPP doesn't answer the real question. TRICERATOPS doesn't use centroids, and TIC 408310005 has no radius in the TIC, so its low NEB probability (about 1e-6) depends on assumed properties for that star. I'll stop quoting the FPP for this signal until the location is settled, and I agree that ground photometry resolving the neighbour is the test. One small thing: our TIC query puts TIC 408310005 at 5.6″ from WASP-166, and you have 6.7″. Is that a different epoch, or a different star?
