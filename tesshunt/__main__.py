"""CLI: python -m tesshunt <command>. See README.md."""
import argparse
import json
import os
import sys

from . import config as cfgmod


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tesshunt")
    ap.add_argument("--config")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("targets", help="build/refresh the TIC target pool and queue a pilot sample")
    s.add_argument("--n", type=int)
    s.add_argument("--refresh", action="store_true")
    s = sub.add_parser("run", help="process queued stars (resumable)")
    s.add_argument("--labels", nargs="*")
    s.add_argument("--workers", type=int)
    sub.add_parser("postprocess")
    sub.add_parser("report")
    sub.add_parser("negatives", help="write negatives.csv/.md: every non-surviving signal and why")
    s = sub.add_parser("audit")
    s.add_argument("--redo", action="store_true")
    s.add_argument("--import-notes", action="store_true", help="load sig*.audit.txt files written on the Mac")
    s = sub.add_parser("audit-compare", help="run several cortex models over a snapshot dir of survivors")
    s.add_argument("dir")
    s.add_argument("--models", nargs="+", default=["qwen3vl", "qwen38"])
    s = sub.add_parser("survivor-checks", help="shuffled FAP + inverted light curve for every survivor (n1)")
    s.add_argument("--tics", nargs="*", type=int)
    s.add_argument("--workers", type=int)
    s.add_argument("--redo", action="store_true")
    sub.add_parser("status")
    s = sub.add_parser("requeue", help="put error stars back in the queue")
    s.add_argument("--status", default="error")
    sub.add_parser("validate-build", help="draw + freeze the validation sets (CSV)")
    sub.add_parser("validate-run", help="run the pipeline on the validation sets")
    sub.add_parser("validate-report", help="write validation/out/VALIDATION.md")
    s = sub.add_parser("injgrid", help="injection-recovery grid on quiet stars")
    s.add_argument("tics", nargs="+", type=int)
    a = ap.parse_args(argv)

    cfg = cfgmod.load(a.config)
    cfgmod.limit_threads(cfg["resources"]["threads_per_worker"])
    from . import db, pipeline
    if a.cmd == "targets":
        from . import targets
        con = db.connect(cfg["paths"]["db"])
        if a.refresh:
            targets.pool(cfg, refresh=True)
        rows = targets.sample(cfg, a.n)
        db.add_targets(con, rows, "pilot")
        print(f"queued {len(rows)} pilot targets (pool cached in {cfg['paths']['catalog_dir']})")
    elif a.cmd == "run":
        pipeline.run(cfg, a.labels, a.workers)
        from . import report, negatives
        print(report.build(cfg))
        print(negatives.write(cfg))
    elif a.cmd == "postprocess":
        pipeline.postprocess(cfg)
    elif a.cmd == "report":
        from . import report
        print(report.build(cfg))
    elif a.cmd == "negatives":
        from . import negatives
        print(negatives.write(cfg))
    elif a.cmd == "audit":
        from . import audit, report
        print("imported" if a.import_notes else "audited",
              audit.import_notes(cfg) if a.import_notes else audit.run(cfg, a.redo))
        report.build(cfg)
    elif a.cmd == "audit-compare":
        from . import audit
        for row in audit.compare(cfg, a.models, a.dir):
            print(*row)
    elif a.cmd == "survivor-checks":
        from . import survivor_checks, report
        pipeline.setup_logging()
        print("checked", survivor_checks.run(cfg, a.workers, a.redo, a.tics), "survivor(s)")
        print(report.build(cfg))
    elif a.cmd == "status":
        con = db.connect(cfg["paths"]["db"])
        for row in con.execute("SELECT label, status, COUNT(*) FROM targets GROUP BY 1,2 ORDER BY 1,2"):
            print(f"{row[0] or '-':12s} {row[1]:8s} {row[2]}")
        v = con.execute("SELECT verdict, COUNT(*) FROM signals GROUP BY 1").fetchall()
        print("signals:", dict(v))
        print("paused:", os.path.exists(pipeline.PAUSE_FILE))
        from . import provenance
        print("code now:", provenance.label(provenance.stamp(cfg)))
        for st, n in db.provenance_counts(con):
            print(f"  {n} star(s) processed by {provenance.label(st)}")
    elif a.cmd == "requeue":
        con = db.connect(cfg["paths"]["db"])
        with con:
            n = con.execute("UPDATE targets SET status='queued', error=NULL WHERE status=?", (a.status,)).rowcount
        print("requeued", n)
    elif a.cmd.startswith("validate") or a.cmd == "injgrid":
        from . import validate
        if a.cmd == "validate-build":
            print(validate.build_sets())
        elif a.cmd == "validate-run":
            c = validate.queue(cfg)
            pipeline.run(c)
            from . import report
            report.build(c, title="tess-hunt VALIDATION survivors")
            from . import negatives
            negatives.write(c, title="tess-hunt VALIDATION negatives")
        elif a.cmd == "validate-report":
            md = validate.evaluate(cfg)
            path = os.path.join(validate.VDIR, "out", "VALIDATION.md")
            open(path, "w").write(md)
            print(md)
        else:
            df, tab = validate.injection_grid(cfg, a.tics)
            print(tab.to_markdown())


if __name__ == "__main__":
    sys.exit(main())
