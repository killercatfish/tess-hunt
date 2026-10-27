"""Count the stars where eumemic's iterative search ended early (board item e7, 2026-10-23).

Their search (pipeline/search.py at d3daa0f) finds up to 3 signals per star and stops when the last
signal has SNR < 7 or repeats an earlier period. That is the same stopping rule behind our own recall
gap (board item n5): a repeat or one deep event ends the search before weaker signals are looked for.

Input: a folder holding their results_public/all_signals.csv.gz, all_signals_faint_t1.csv.gz and
all_signals_faint_t2.csv.gz (download them into an empty folder; they are data, not code).
Usage: python -I scripts/eumemic_stop_counts.py <folder> [single_tics.csv]
With a second argument it also writes the "single" stars (one strong transit ended the search) as a TIC list,
the target list for the first re-search (Josh, 2026-10-26).
"""
import sys

import pandas as pd

FILES = {"all_signals": "K/M dwarfs T <= 11.5", "all_signals_faint_t1": "M dwarfs 11.5 < T <= 12.5",
         "all_signals_faint_t2": "M dwarfs 12.5 < T <= 13.5"}


def main(folder, out=None):
    tot = dict(stars=0, single=0, repeat=0, either=0)
    singles = []
    for f, what in FILES.items():
        d = pd.read_csv(f"{folder}/{f}.csv.gz", usecols=["tic", "rank", "method", "bls_snr", "repeat",
                                                         "max_ses_frac", "n_good_events"])
        d = d[d.method != "semi"]  # K/M dwarfs were searched twice; keep the coherent pass
        g = d.sort_values("rank").groupby("tic")
        first, last = g.head(1).set_index("tic"), g.tail(1).set_index("tic")
        # a strong first signal that is mostly one transit, after which the search was over by signal 2
        single = ((first.bls_snr >= 9) & (first.max_ses_frac > 0.8) & (first.n_good_events >= 3)
                  & (last["rank"] <= 2))
        repeat = last["repeat"] & (last["rank"] < 3)  # stopped on a repeated period before signal 3
        row = dict(stars=len(last), single=int(single.sum()), repeat=int(repeat.sum()),
                   either=int((single | repeat).sum()))
        print(f"{what}: {row}")
        singles += [(int(t), f) for t in single[single].index]
        tot = {k: tot[k] + row[k] for k in tot}
    print(f"total: {tot}")
    if out:
        pd.DataFrame(singles, columns=["tic", "search"]).drop_duplicates("tic").to_csv(out, index=False)
        print(f"wrote {len(set(t for t, _ in singles))} stars to {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
