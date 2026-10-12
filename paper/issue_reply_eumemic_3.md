Thank you for the correction, and for checking all eight sectors. That is exactly the kind of check I should be doing too. I won't cite the 0.36″ anywhere. For the giant I'll rely on the duration argument alone, and say plainly that the difference images don't separate it from the target. I'll cite this comment only for what it does show: no sector puts the centroid within 11″ of TIC 407126406 or within 30″ of TIC 10001766874. Those are the two stars that drive our NFPP, so it's useful evidence even though it isn't the result we hoped for.

Now the false-alarm number, as promised.

I reran our TLS search on 200 copies of the TOI-913 light curve. Each copy shuffles 1-day blocks within each sector, and uses the same masks our pipeline had applied when it found the signal (b, TOI-913.02 and a 27.3 d signal it had rejected as systematic). On the real data, 5.4501 d is the top peak at SDE 21.8. Across the 200 shuffled copies, the highest SDE anywhere in 0.5–40 d had a median of 13.1, a 99th percentile of 18.1 and a maximum of 18.8. None reached 21.8, so FAP < 1.5% (95% upper limit).

The limit: shuffling keeps noise under a day but not systematics coherent over many days. In the unmasked search a 27.3 d systematic outranks it, and 5.45 d only comes out once that is masked (with cosine detrending and in QLP it is the top peak outright). So I'd read this next to your 37% population rate at MES 9–10, not in place of it.

Also checked: there is no window-function peak at 5.45 d and the signal isn't an alias of b. No momentum dump falls in transit (0.8 expected), and the 43 dump events show no phase clustering. GLS doesn't detect it, but it doesn't detect b either (920 ppm, SDE 125), so GLS can't decide this either way.

Figure: paper/figures/fig4_periodograms.png. Code: scripts/periodogram_fap.py. Both in https://github.com/killercatfish/tess-hunt.
