import sys, os
sys.path.insert(0, os.path.expanduser("~/dev/tess-hunt"))
from tesshunt import config, db, stellar
cfg = config.load("/tmp/ecn/config.yaml")
con = db.connect(cfg["paths"]["db"])
tics = [231725883,88407114,24621747,304655480,422677298,420529106,147163875,48439430,306990399,408310006,163029327,146282666,422217860,247166992,76228620,165337974]
rows = []
for t in tics:
    r = stellar.tic_row(t); rows.append(r); print(t, r.get("teff"), r.get("rad"), r.get("tmag"))
db.add_targets(con, rows, "eumemic_cn")
