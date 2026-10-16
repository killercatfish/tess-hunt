#!/bin/sh
# Hand check 6: print every TOI-913 5.45 d transit as one row (depths in ppm).
# Run from anywhere: learn/check6.sh
cd "$(dirname "$0")/.." || exit 1
python3 - <<'EOF'
import json
ev = json.load(open("paper/data/harmonic_systematic_test.json"))["events"]
print("  # | time (BTJD) | depth ppm | err ppm | days from 27.3 d systematic")
for e in ev:
    print(f"{e['epoch']:3d} | {e['tc']:11.3f} | {e['depth']*1e6:9.0f} | {e['err']*1e6:7.0f} | {e['offset_from_syst_d']:6.2f}")
EOF
