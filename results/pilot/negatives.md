# tess-hunt negatives

Every signal the search found that did not survive, and why. Built by code 5a6a15e · config 09c9bdb9a2fe.

- 200 star(s) processed by unstamped (processed before 2026-10-23)

**314 signals: 5 survivors (in the report), 131 rejected by a kill test, 178 below the search threshold.** A signal can fail several tests.

| Kill test | Signals it failed | ...and the only test it failed |
|---|---|---|
| holdout | 94 | 13 |
| odd_even | 81 | 1 |
| sector_consistency | 70 | 0 |
| injection | 39 | 1 |
| harmonic | 20 | 2 |
| duration | 18 | 2 |
| secondary | 15 | 0 |
| shape | 7 | 0 |
| size | 4 | 0 |
| systematics | 2 | 0 |

The 178 below-threshold signals are in `negatives.csv` with the number that kept each out.

## Rejected signals

| TIC | sig | P (d) | depth ppm | Rp R⊕ | SNR | why |
|---|---|---|---|---|---|---|
| 4585822 | 0 | 13.59877 | 28307 | 8.8 | 34.4 | not re-found in held-out seasons (0/3) |
| 9151337 | 1 | 34.71566 | 1099 | 2.6 | 7.6 | not re-found in held-out seasons (0/3); a copy injected at this period was not recovered (found 22.0896 d) |
| 14174651 | 0 | 33.38780 | 7269 | 4.7 | 16.1 | odd/even depths differ by 5.3 sigma (limit 3.0); depth differs between sectors (p 1.5e-11, limit 0.0027) |
| 14174651 | 1 | 39.45137 | 4609 | 3.7 | 12.7 | odd/even depths differ by 44.4 sigma (limit 3.0); not re-found in held-out seasons (0/2) |
| 14174651 | 2 | 27.46597 | 4079 | 3.5 | 10.9 | odd/even depths differ by 3.8 sigma (limit 3.0); not re-found in held-out seasons (0/3) |
| 14174651 | 3 | 37.83495 | 3828 | 3.4 | 7.6 | odd/even depths differ by 4.0 sigma (limit 3.0); not re-found in held-out seasons (0/3); a copy injected at this period was not recovered (found 24.7897 d) |
| 35025541 | 0 | 24.69297 | 2421 | 2.2 | 13.4 | odd/even depths differ by 11.1 sigma (limit 3.0); depth differs between sectors (p 1.2e-18, limit 0.0027); not re-found in held-out seasons (0/4) |
| 35025541 | 1 | 34.00792 | 2291 | 2.2 | 10.1 | odd/even depths differ by 8.2 sigma (limit 3.0); not re-found in held-out seasons (0/2) |
| 72907244 | 0 | 39.68573 | 4186 | 4.5 | 26.9 | odd/even depths differ by 109.4 sigma (limit 3.0); duration 1.81x what the star allows (allowed 0.2-1.6); depth differs between sectors (p 1.4e-09, limit 0.0027); not re-found in held-out seasons (1/5); a copy injected at this period was not recovered (found 39.7019 d) |
| 72907244 | 1 | 30.81788 | 2168 | 3.3 | 14.8 | odd/even depths differ by 48.1 sigma (limit 3.0); not re-found in held-out seasons (0/5); a copy injected at this period was not recovered (found 39.4794 d) |
| 72907244 | 2 | 39.67446 | 3559 | 4.2 | 16.7 | period is a harmonic of signal #0 on the same star; odd/even depths differ by 118.5 sigma (limit 3.0); not re-found in held-out seasons (0/5); a copy injected at this period was not recovered (found 38.7166 d) |
| 79701644 | 0 | 28.37307 | 4290 | 3.6 | 8.5 | not re-found in held-out seasons (0/2); a copy injected at this period was not recovered (found 36.8845 d) |
| 81844650 | 0 | 12.81877 | 2484 | 3.7 | 20.5 | odd/even depths differ by 11.1 sigma (limit 3.0) |
| 85898240 | 0 | 25.29061 | 996 | 3.0 | 15.6 | odd/even depths differ by 12.1 sigma (limit 3.0); depth differs between sectors (p 0.0004, limit 0.0027); a copy injected at this period was not recovered (found 25.2934 d) |
| 103221268 | 0 | 32.57496 | 32443 | 11.5 | 171.0 | not re-found in held-out seasons (0/3) |
| 103221268 | 1 | 35.56787 | 4572 | 4.3 | 16.1 | odd/even depths differ by 5.7 sigma (limit 3.0); not re-found in held-out seasons (0/3) |
| 103221268 | 2 | 35.58330 | 3860 | 4.0 | 16.6 | period is a harmonic of signal #1 on the same star; odd/even depths differ by 8.9 sigma (limit 3.0); not re-found in held-out seasons (1/3) |
| 103221268 | 3 | 32.07786 | 3053 | 3.5 | 11.7 | not re-found in held-out seasons (0/3) |
| 111564865 | 0 | 0.71199 | 10966 | 5.2 | 36.9 | duration 1.79x what the star allows (allowed 0.2-1.6) |
| 111564865 | 1 | 0.71421 | 10742 | 5.1 | 29.3 | period is a harmonic of signal #0 on the same star; secondary eclipse: -3.2 sigma at phase 0.5 (limit 3.0), 9.6 sigma best elsewhere (limit 5.0); duration 1.79x what the star allows (allowed 0.2-1.6); not re-found in held-out seasons (0/3) |
| 111564865 | 2 | 0.71559 | 5214 | 3.6 | 10.8 | period is a harmonic of signal #0 on the same star; secondary eclipse: -2.0 sigma at phase 0.5 (limit 3.0), 12.4 sigma best elsewhere (limit 5.0); duration 1.80x what the star allows (allowed 0.2-1.6); not re-found in held-out seasons (1/3) |
| 111564865 | 3 | 0.71419 | 3701 | 3.0 | 10.4 | period is a harmonic of signal #0 on the same star; secondary eclipse: -5.9 sigma at phase 0.5 (limit 3.0), 12.8 sigma best elsewhere (limit 5.0); duration 1.63x what the star allows (allowed 0.2-1.6) |
| 125345187 | 0 | 25.43844 | 30232 | 9.2 | 8.5 | odd/even depths differ by 8.0 sigma (limit 3.0); not re-found in held-out seasons (0/3) |
| 138711522 | 0 | 11.50960 | 504 | 1.5 | 7.2 | odd/even depths differ by 4.3 sigma (limit 3.0); a copy injected at this period was not recovered (found 10.2312 d) |
| 158104137 | 0 | 28.39891 | 1573 | 3.6 | 14.4 | odd/even depths differ by 25.3 sigma (limit 3.0); depth differs between sectors (p 0.00035, limit 0.0027) |
| 158104137 | 1 | 26.82263 | 949 | 2.8 | 13.6 | odd/even depths differ by 4.7 sigma (limit 3.0); not re-found in held-out seasons (1/4) |
| 158104137 | 2 | 31.67410 | 792 | 2.6 | 12.2 | odd/even depths differ by 11.8 sigma (limit 3.0); depth differs between sectors (p 3.7e-18, limit 0.0027); not re-found in held-out seasons (1/4) |
| 158104137 | 3 | 28.40891 | 773 | 2.5 | 10.2 | period is a harmonic of signal #0 on the same star |
| 219032065 | 0 | 38.58955 | 33505 | 8.3 | 15.3 | odd/even depths differ by 11.5 sigma (limit 3.0); same period on 4 stars: instrumental; depth differs between sectors (p 7.5e-07, limit 0.0027); not re-found in held-out seasons (0/1) |
| 219032065 | 1 | 29.22733 | 12584 | 5.1 | 8.2 | odd/even depths differ by 7.0 sigma (limit 3.0); not re-found in held-out seasons (0/3); a copy injected at this period was not recovered (found 29.2273 d) |
| 230186943 | 0 | 12.28035 | 584 | 1.9 | 13.2 | odd/even depths differ by 8.4 sigma (limit 3.0); duration 1.82x what the star allows (allowed 0.2-1.6); a copy injected at this period was not recovered (found 12.1398 d) |
| 237205427 | 0 | 20.90673 | 791 | 1.1 | 7.8 | odd/even depths differ by 7.3 sigma (limit 3.0); not re-found in held-out seasons (1/3) |
| 238192427 | 0 | 30.91111 | 343 | 1.4 | 9.1 | odd/even depths differ by 10.2 sigma (limit 3.0); not re-found in held-out seasons (0/4) |
| 238192427 | 1 | 20.45876 | 238 | 1.1 | 7.9 | odd/even depths differ by 3.4 sigma (limit 3.0); depth differs between sectors (p 3.8e-05, limit 0.0027); a copy injected at this period was not recovered (found 21.6097 d) |
| 239182681 | 0 | 20.47857 | 2620 | 2.7 | 9.6 | odd/even depths differ by 11.6 sigma (limit 3.0); depth differs between sectors (p 1.5e-13, limit 0.0027); not re-found in held-out seasons (1/5) |
| 243514635 | 1 | 28.57107 | 32714 | 10.8 | 9.6 | odd/even depths differ by 3.4 sigma (limit 3.0); depth differs between sectors (p 6.4e-05, limit 0.0027); a copy injected at this period was not recovered (found 38.7770 d) |
| 245914064 | 0 | 29.13398 | 3120 | 0.9 | 9.1 | not re-found in held-out seasons (1/3) |
| 245914064 | 1 | 30.86053 | 2471 | 0.8 | 7.5 | odd/even depths differ by 6.3 sigma (limit 3.0); same period on 4 stars: instrumental; not re-found in held-out seasons (0/2); a copy injected at this period was not recovered (found 37.0328 d) |
| 264304554 | 0 | 32.18932 | 247 | 1.6 | 10.1 | odd/even depths differ by 5.0 sigma (limit 3.0); depth differs between sectors (p 7.3e-53, limit 0.0027) |
| 264304554 | 1 | 37.00708 | 205 | 1.4 | 8.1 | odd/even depths differ by 6.5 sigma (limit 3.0); depth differs between sectors (p 7.6e-47, limit 0.0027); a copy injected at this period was not recovered (found 35.9739 d) |
| 264304554 | 2 | 35.97394 | 209 | 1.4 | 8.4 | depth differs between sectors (p 3.4e-75, limit 0.0027); a copy injected at this period was not recovered (found 19.8176 d) |
| 264304554 | 3 | 9.86987 | 151 | 1.2 | 7.1 | odd/even depths differ by 3.3 sigma (limit 3.0); depth differs between sectors (p 9e-13, limit 0.0027) |
| 264898074 | 0 | 27.69577 | 4585 | 4.3 | 9.1 | odd/even depths differ by 6.9 sigma (limit 3.0); depth differs between sectors (p 6.1e-39, limit 0.0027); not re-found in held-out seasons (1/3); a copy injected at this period was not recovered (found 29.9360 d) |
| 269556642 | 0 | 23.38330 | 493 | 2.7 | 11.0 | not re-found in held-out seasons (1/3) |
| 274393297 | 0 | 0.82224 | 11227 | 2.3 | 47.1 | secondary eclipse: 27.9 sigma at phase 0.5 (limit 3.0), 28.5 sigma best elsewhere (limit 5.0); duration 2.42x what the star allows (allowed 0.2-1.6); not re-found in held-out seasons (1/3) |
| 274393297 | 1 | 0.82282 | 8691 | 2.0 | 34.1 | period is a harmonic of signal #0 on the same star; secondary eclipse: 13.0 sigma at phase 0.5 (limit 3.0), 20.6 sigma best elsewhere (limit 5.0); duration 2.42x what the star allows (allowed 0.2-1.6); depth differs between sectors (p 7.8e-09, limit 0.0027); not re-found in held-out seasons (1/3) |
| 274393297 | 2 | 0.82223 | 10504 | 2.2 | 40.2 | period is a harmonic of signal #0 on the same star; duration 2.42x what the star allows (allowed 0.2-1.6); not re-found in held-out seasons (1/3) |
| 274393297 | 3 | 0.82245 | 7338 | 1.8 | 17.3 | period is a harmonic of signal #0 on the same star; secondary eclipse: 10.8 sigma at phase 0.5 (limit 3.0), 13.0 sigma best elsewhere (limit 5.0) |
| 277803433 | 0 | 25.67170 | 49820 | 10.1 | 33.1 | odd/even depths differ by 5.4 sigma (limit 3.0); depth differs between sectors (p 1.4e-40, limit 0.0027); not re-found in held-out seasons (1/3) |
| 277803433 | 1 | 38.56558 | 29240 | 7.7 | 21.0 | odd/even depths differ by 23.4 sigma (limit 3.0); depth differs between sectors (p 1.7e-21, limit 0.0027); not re-found in held-out seasons (0/3) |
| 277803433 | 2 | 37.16555 | 25635 | 7.2 | 41.7 | odd/even depths differ by 28.3 sigma (limit 3.0); depth differs between sectors (p 2.4e-19, limit 0.0027); not re-found in held-out seasons (0/3) |
| 277803433 | 3 | 35.00359 | 6181 | 3.6 | 11.0 | odd/even depths differ by 16.0 sigma (limit 3.0); depth differs between sectors (p 2.6e-05, limit 0.0027); not re-found in held-out seasons (0/2); a copy injected at this period was not recovered (found 28.6540 d) |
| 278593441 | 0 | 25.73704 | 5366 | 4.5 | 45.7 | odd/even depths differ by 13.9 sigma (limit 3.0); not re-found in held-out seasons (2/5) |
| 278593441 | 1 | 39.37036 | 3868 | 3.8 | 33.6 | odd/even depths differ by 12.2 sigma (limit 3.0); not re-found in held-out seasons (0/4) |
| 278593441 | 2 | 31.22862 | 1464 | 2.4 | 14.7 | not re-found in held-out seasons (0/4) |
| 278593441 | 3 | 25.65737 | 985 | 1.9 | 13.5 | period is a harmonic of signal #0 on the same star; odd/even depths differ by 5.8 sigma (limit 3.0); not re-found in held-out seasons (1/4) |
| 278726191 | 0 | 35.09937 | 1178 | 2.3 | 19.8 | odd/even depths differ by 37.3 sigma (limit 3.0); depth differs between sectors (p 8.2e-171, limit 0.0027); not re-found in held-out seasons (1/4) |
| 278726191 | 1 | 33.47135 | 997 | 2.1 | 13.6 | odd/even depths differ by 3.6 sigma (limit 3.0); depth differs between sectors (p 7.6e-101, limit 0.0027); not re-found in held-out seasons (0/4); a copy injected at this period was not recovered (found 35.1048 d) |
| 278726191 | 2 | 37.60271 | 867 | 2.0 | 16.1 | odd/even depths differ by 23.3 sigma (limit 3.0); depth differs between sectors (p 7.2e-145, limit 0.0027); a copy injected at this period was not recovered (found 35.1048 d) |
| 278726191 | 3 | 19.78817 | 603 | 1.7 | 14.9 | odd/even depths differ by 44.7 sigma (limit 3.0); duration 1.68x what the star allows (allowed 0.2-1.6); depth differs between sectors (p 0, limit 0.0027); a copy injected at this period was not recovered (found 35.1048 d) |
| 278807030 | 0 | 24.30934 | 1254 | 3.3 | 12.3 | odd/even depths differ by 12.4 sigma (limit 3.0); V-shaped, like a grazing binary (U minus V chi2 13.2, limit 9.0); depth differs between sectors (p 2.3e-29, limit 0.0027); not re-found in held-out seasons (0/2) |
| 278807030 | 1 | 34.31430 | 1075 | 3.0 | 7.1 | not re-found in held-out seasons (1/3) |
| 278807030 | 2 | 37.14678 | 1119 | 3.1 | 9.3 | odd/even depths differ by 7.1 sigma (limit 3.0); depth differs between sectors (p 3.1e-13, limit 0.0027); not re-found in held-out seasons (1/3) |
| 282925698 | 0 | 34.85010 | 857 | 2.5 | 20.8 | odd/even depths differ by 8.9 sigma (limit 3.0); depth differs between sectors (p 3.5e-13, limit 0.0027); not re-found in held-out seasons (1/3) |
| 282925698 | 1 | 18.16553 | 360 | 1.6 | 12.8 | odd/even depths differ by 5.0 sigma (limit 3.0); depth differs between sectors (p 2e-17, limit 0.0027); a copy injected at this period was not recovered (found 26.1557 d) |
| 282925698 | 2 | 26.55883 | 501 | 1.9 | 12.8 | depth differs between sectors (p 1.7e-09, limit 0.0027); not re-found in held-out seasons (0/2) |
| 282925698 | 3 | 35.16181 | 465 | 1.8 | 13.7 | period is a harmonic of signal #0 on the same star |
| 287095354 | 0 | 0.95799 | 257490 | 57.1 | 67.0 | secondary eclipse: 47.9 sigma at phase 0.5 (limit 3.0), 42.4 sigma best elsewhere (limit 5.0); implied radius 57.1 R_earth (limit 22.0); V-shaped, like a grazing binary (U minus V chi2 31.7, limit 9.0) |
| 287095354 | 1 | 0.95799 | 262593 | 57.7 | 89.5 | period is a harmonic of signal #0 on the same star; implied radius 57.7 R_earth (limit 22.0); V-shaped, like a grazing binary (U minus V chi2 29.9, limit 9.0) |
| 287095354 | 2 | 0.95799 | 123523 | 39.6 | 45.1 | period is a harmonic of signal #0 on the same star; secondary eclipse: 58.7 sigma at phase 0.5 (limit 3.0), 55.5 sigma best elsewhere (limit 5.0); implied radius 39.6 R_earth (limit 22.0); V-shaped, like a grazing binary (U minus V chi2 20.5, limit 9.0) |
| 287095354 | 3 | 0.95800 | 134002 | 41.2 | 113.3 | period is a harmonic of signal #0 on the same star; implied radius 41.2 R_earth (limit 22.0); V-shaped, like a grazing binary (U minus V chi2 14.9, limit 9.0) |
| 293803474 | 0 | 27.07529 | 510 | 1.4 | 8.4 | depth differs between sectors (p 1.6e-10, limit 0.0027); not re-found in held-out seasons (1/4); a copy injected at this period was not recovered (found 30.4549 d) |
| 297800792 | 0 | 0.53754 | 13678 | 5.3 | 44.0 | duration 1.86x what the star allows (allowed 0.2-1.6) |
| 297800792 | 1 | 0.53752 | 8760 | 4.2 | 24.3 | period is a harmonic of signal #0 on the same star; secondary eclipse: -2.2 sigma at phase 0.5 (limit 3.0), 17.9 sigma best elsewhere (limit 5.0); duration 1.86x what the star allows (allowed 0.2-1.6) |
| 297800792 | 2 | 0.53860 | 5790 | 3.5 | 12.5 | period is a harmonic of signal #0 on the same star; secondary eclipse: 4.0 sigma at phase 0.5 (limit 3.0), 4.5 sigma best elsewhere (limit 5.0) |
| 297800792 | 3 | 0.53755 | 4326 | 3.0 | 15.0 | period is a harmonic of signal #0 on the same star; secondary eclipse: 9.3 sigma at phase 0.5 (limit 3.0), 11.6 sigma best elsewhere (limit 5.0); duration 1.79x what the star allows (allowed 0.2-1.6) |
| 298129041 | 0 | 35.09878 | 8448 | 5.0 | 10.2 | odd/even depths differ by 8.2 sigma (limit 3.0); depth differs between sectors (p 6.1e-10, limit 0.0027); not re-found in held-out seasons (1/3) |
| 298129041 | 1 | 31.59212 | 5921 | 4.2 | 7.9 | depth differs between sectors (p 4.7e-05, limit 0.0027); not re-found in held-out seasons (0/3); a copy injected at this period was not recovered (found 39.1242 d) |
| 298129041 | 2 | 39.12418 | 7815 | 4.8 | 8.4 | odd/even depths differ by 7.2 sigma (limit 3.0); depth differs between sectors (p 1e-08, limit 0.0027) |
| 298129041 | 3 | 27.49090 | 6086 | 4.3 | 7.2 | not re-found in held-out seasons (0/3) |
| 301917244 | 0 | 37.32307 | 36874 | 11.9 | 57.0 | odd/even depths differ by 229.4 sigma (limit 3.0); depth differs between sectors (p 3.8e-178, limit 0.0027); not re-found in held-out seasons (1/4) |
| 301917244 | 1 | 39.40013 | 13560 | 7.2 | 16.1 | odd/even depths differ by 37.8 sigma (limit 3.0); not re-found in held-out seasons (1/3); a copy injected at this period was not recovered (found 32.5449 d) |
| 301917244 | 2 | 32.54490 | 9190 | 5.9 | 15.8 | odd/even depths differ by 7.7 sigma (limit 3.0); depth differs between sectors (p 4.3e-36, limit 0.0027); not re-found in held-out seasons (2/5) |
| 301917244 | 3 | 26.29489 | 7622 | 5.4 | 14.3 | odd/even depths differ by 6.5 sigma (limit 3.0); depth differs between sectors (p 1e-45, limit 0.0027); not re-found in held-out seasons (0/5) |
| 307218058 | 0 | 33.54836 | 539 | 1.3 | 11.6 | odd/even depths differ by 12.6 sigma (limit 3.0); depth differs between sectors (p 3.1e-133, limit 0.0027); not re-found in held-out seasons (0/4) |
| 307218058 | 1 | 38.75673 | 437 | 1.2 | 11.3 | odd/even depths differ by 6.8 sigma (limit 3.0); depth differs between sectors (p 4.1e-62, limit 0.0027); not re-found in held-out seasons (0/4) |
| 307218058 | 2 | 39.96631 | 393 | 1.1 | 8.3 | odd/even depths differ by 3.9 sigma (limit 3.0); depth differs between sectors (p 3.1e-06, limit 0.0027); not re-found in held-out seasons (1/4); a copy injected at this period was not recovered (found 38.9006 d) |
| 307218058 | 3 | 28.20870 | 281 | 1.0 | 8.5 | odd/even depths differ by 5.6 sigma (limit 3.0); depth differs between sectors (p 3.9e-48, limit 0.0027); not re-found in held-out seasons (0/4); a copy injected at this period was not recovered (found 30.7722 d) |
| 309432404 | 0 | 28.19869 | 9428 | 5.5 | 16.5 | depth differs between sectors (p 3.2e-08, limit 0.0027); not re-found in held-out seasons (0/4) |
| 309432404 | 1 | 21.90317 | 4648 | 3.8 | 12.2 | depth differs between sectors (p 3.1e-15, limit 0.0027); a copy injected at this period was not recovered (found 33.5265 d) |
| 309432404 | 2 | 33.52653 | 5435 | 4.1 | 8.5 | not re-found in held-out seasons (1/4); a copy injected at this period was not recovered (found 38.4825 d) |
| 309432404 | 3 | 38.48252 | 7060 | 4.7 | 10.4 | odd/even depths differ by 5.3 sigma (limit 3.0); depth differs between sectors (p 0.00023, limit 0.0027); not re-found in held-out seasons (0/3); a copy injected at this period was not recovered (found 39.3737 d) |
| 323977652 | 0 | 13.03362 | 1787 | 2.3 | 11.5 | not re-found in held-out seasons (1/4) |
| 323977652 | 1 | 38.64938 | 1474 | 2.1 | 8.1 | odd/even depths differ by 7.3 sigma (limit 3.0); depth differs between sectors (p 1.1e-06, limit 0.0027); not re-found in held-out seasons (0/2) |
| 326668656 | 0 | 39.99296 | 100807 | 16.8 | 85.7 | secondary eclipse: 1.4 sigma at phase 0.5 (limit 3.0), 8.6 sigma best elsewhere (limit 5.0); depth differs between sectors (p 3.1e-18, limit 0.0027); not re-found in held-out seasons (0/2) |
| 326668656 | 1 | 39.13499 | 23615 | 8.2 | 24.2 | odd/even depths differ by 86.8 sigma (limit 3.0); depth differs between sectors (p 3.1e-39, limit 0.0027); not re-found in held-out seasons (0/4); a copy injected at this period was not recovered (found 39.1416 d) |
| 326668656 | 2 | 26.65979 | 11105 | 5.6 | 10.4 | depth differs between sectors (p 4e-22, limit 0.0027); not re-found in held-out seasons (0/4); a copy injected at this period was not recovered (found 39.1414 d) |
| 358850609 | 0 | 37.76237 | 23752 | 9.2 | 25.9 | odd/even depths differ by 37.9 sigma (limit 3.0); depth differs between sectors (p 4.3e-135, limit 0.0027); not re-found in held-out seasons (0/2) |
| 361959837 | 0 | 36.45729 | 17332 | 9.9 | 26.8 | odd/even depths differ by 72.4 sigma (limit 3.0); depth differs between sectors (p 5.4e-06, limit 0.0027); not re-found in held-out seasons (0/5) |
| 361959837 | 1 | 38.64831 | 8968 | 7.1 | 11.7 | odd/even depths differ by 59.5 sigma (limit 3.0); depth differs between sectors (p 1.3e-16, limit 0.0027); not re-found in held-out seasons (0/4) |
| 361959837 | 2 | 27.08079 | 5294 | 5.5 | 11.9 | odd/even depths differ by 23.4 sigma (limit 3.0); depth differs between sectors (p 3.9e-56, limit 0.0027); not re-found in held-out seasons (1/5) |
| 361959837 | 3 | 35.45687 | 4838 | 5.2 | 22.0 | odd/even depths differ by 214.8 sigma (limit 3.0); depth differs between sectors (p 3.4e-90, limit 0.0027); not re-found in held-out seasons (1/5); a copy injected at this period was not recovered (found 36.4534 d) |
| 363319841 | 0 | 39.54053 | 2278 | 4.0 | 21.1 | odd/even depths differ by 30.3 sigma (limit 3.0); not re-found in held-out seasons (0/3) |
| 363319841 | 1 | 37.73472 | 764 | 2.3 | 10.2 | odd/even depths differ by 7.4 sigma (limit 3.0); depth differs between sectors (p 1.1e-21, limit 0.0027); not re-found in held-out seasons (1/4); a copy injected at this period was not recovered (found 20.2298 d) |
| 364145989 | 0 | 0.74311 | 376 | 1.0 | 10.5 | odd/even depths differ by 3.2 sigma (limit 3.0); secondary eclipse: -1.9 sigma at phase 0.5 (limit 3.0), 5.3 sigma best elsewhere (limit 5.0); duration 1.84x what the star allows (allowed 0.2-1.6); depth differs between sectors (p 3.5e-11, limit 0.0027) |
| 364145989 | 1 | 0.98946 | 379 | 1.0 | 8.5 | secondary eclipse: 3.4 sigma at phase 0.5 (limit 3.0), 1.7 sigma best elsewhere (limit 5.0); duration 1.84x what the star allows (allowed 0.2-1.6); depth differs between sectors (p 0.00018, limit 0.0027); a copy injected at this period was not recovered (found 23.3895 d) |
| 364145989 | 2 | 23.01897 | 1642 | 2.2 | 8.1 | a copy injected at this period was not recovered (found 0.7411 d) |
| 382604017 | 0 | 13.57647 | 30807 | 11.8 | 97.1 | odd/even depths differ by 153.8 sigma (limit 3.0); V-shaped, like a grazing binary (U minus V chi2 19.8, limit 9.0); not re-found in held-out seasons (0/4) |
| 383370704 | 0 | 30.88172 | 950 | 2.0 | 9.5 | odd/even depths differ by 11.9 sigma (limit 3.0); depth differs between sectors (p 8.9e-14, limit 0.0027); a copy injected at this period was not recovered (found 30.8817 d) |
| 383469649 | 0 | 14.38947 | 2814 | 2.8 | 9.1 | odd/even depths differ by 5.6 sigma (limit 3.0); depth differs between sectors (p 0.00032, limit 0.0027); not re-found in held-out seasons (0/3) |
| 383469649 | 1 | 35.51087 | 3601 | 3.2 | 8.6 | not re-found in held-out seasons (0/1) |
| 383469649 | 2 | 37.06125 | 2936 | 2.9 | 7.4 | not re-found in held-out seasons (0/2) |
| 407126408 | 1 | 27.28521 | 527 | 1.8 | 12.1 | depth differs between sectors (p 0.00015, limit 0.0027); not re-found in held-out seasons (1/4) |
| 407126408 | 3 | 37.16418 | 453 | 1.7 | 8.3 | odd/even depths differ by 3.4 sigma (limit 3.0); not re-found in held-out seasons (0/4) |
| 418206247 | 0 | 31.81761 | 3936 | 4.0 | 12.0 | odd/even depths differ by 4.0 sigma (limit 3.0); not re-found in held-out seasons (1/3) |
| 418206247 | 1 | 39.69470 | 1968 | 2.8 | 9.7 | depth differs between sectors (p 1e-08, limit 0.0027); not re-found in held-out seasons (0/2) |
| 418206247 | 2 | 31.84832 | 1418 | 2.4 | 8.8 | period is a harmonic of signal #0 on the same star; odd/even depths differ by 9.0 sigma (limit 3.0); depth differs between sectors (p 7.9e-24, limit 0.0027); not re-found in held-out seasons (1/3); a copy injected at this period was not recovered (found 34.9585 d) |
| 448033158 | 0 | 29.60814 | 55822 | 19.4 | 105.7 | odd/even depths differ by 544.7 sigma (limit 3.0); not re-found in held-out seasons (1/4) |
| 458483074 | 0 | 12.94962 | 3296 | 8.8 | 9.9 | odd/even depths differ by 74.9 sigma (limit 3.0); depth differs between sectors (p 0, limit 0.0027); not re-found in held-out seasons (0/3) |
| 458483074 | 1 | 14.31197 | 2144 | 7.1 | 17.3 | odd/even depths differ by 49.9 sigma (limit 3.0); depth differs between sectors (p 6.3e-05, limit 0.0027); not re-found in held-out seasons (1/3) |
| 458483074 | 2 | 35.76919 | 3373 | 8.9 | 25.5 | odd/even depths differ by 91.7 sigma (limit 3.0); V-shaped, like a grazing binary (U minus V chi2 89.8, limit 9.0); depth differs between sectors (p 1.5e-81, limit 0.0027); not re-found in held-out seasons (1/3) |
| 461408984 | 0 | 12.85092 | 286 | 1.2 | 9.7 | not re-found in held-out seasons (0/3) |
| 464779449 | 0 | 1.05361 | 8168 | 4.3 | 36.9 | duration 1.93x what the star allows (allowed 0.2-1.6); depth differs between sectors (p 0.00035, limit 0.0027) |
| 464779449 | 1 | 1.05365 | 5315 | 3.4 | 20.5 | period is a harmonic of signal #0 on the same star; duration 1.93x what the star allows (allowed 0.2-1.6) |
| 464779449 | 2 | 1.05473 | 3588 | 2.8 | 16.3 | period is a harmonic of signal #0 on the same star; secondary eclipse: -1.9 sigma at phase 0.5 (limit 3.0), 10.8 sigma best elsewhere (limit 5.0); duration 1.93x what the star allows (allowed 0.2-1.6); depth differs between sectors (p 7.3e-11, limit 0.0027) |
| 470148871 | 0 | 25.09894 | 889 | 2.4 | 13.9 | odd/even depths differ by 8.1 sigma (limit 3.0); depth differs between sectors (p 2e-31, limit 0.0027); not re-found in held-out seasons (1/3) |
| 470148871 | 1 | 36.56011 | 1072 | 2.6 | 13.2 | odd/even depths differ by 6.0 sigma (limit 3.0); depth differs between sectors (p 1.7e-14, limit 0.0027); not re-found in held-out seasons (0/3) |
| 470148871 | 2 | 34.87602 | 722 | 2.2 | 11.2 | odd/even depths differ by 6.7 sigma (limit 3.0); depth differs between sectors (p 1.2e-10, limit 0.0027); not re-found in held-out seasons (0/3); a copy injected at this period was not recovered (found 37.0497 d) |
| 470148871 | 3 | 32.21895 | 741 | 2.2 | 11.1 | depth differs between sectors (p 5.1e-08, limit 0.0027); not re-found in held-out seasons (1/3) |
| 471016381 | 0 | 39.80971 | 164038 | 19.1 | 63.0 | odd/even depths differ by 85.7 sigma (limit 3.0); depth differs between sectors (p 8.3e-55, limit 0.0027); not re-found in held-out seasons (0/3); a copy injected at this period was not recovered (found 35.2729 d) |
| 942368354 | 0 | 12.99609 | 19067 | ? | 66.5 | not re-found in held-out seasons (1/4) |
