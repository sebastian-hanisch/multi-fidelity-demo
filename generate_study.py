"""Vorgerechnete Studie: sechs Verfahren, Budgets 20 und 40, Kostenverhältnisse 0,1 bis 0,8, je 40 feste Läufe auf der Terminal-Scheibe.
Wenige Minuten auf 14 Kernen.

    python generate_study.py            # schreibt precomputed_study.json
"""
import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import mfo_constants as C
import mfo_evaluation as ev


def job(args):
    b, r, method, seed = args
    x = ev.run_one(method, b, r, seed)
    return b, r, method, seed, {"regret": x.regret, "true_cost": x.true_cost, "best_observed": x.best_observed, "n_low": x.n_low, "n_high": x.n_high,
                                "seconds": x.seconds}


def main(workers=14):
    t0 = time.time()
    jobs = [(b, r, m, s) for b in C.BUDGETS for r in C.COST_RATIOS for m in C.METHODS for s in C.SWEEP_SEEDS]
    jobs.sort(key=lambda j: (j[2] != "bo_low", -j[0]))                      # die langsamen (BO mit vielen kurzen Läufen) zuerst
    runs = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for b, r, method, seed, rec in ex.map(job, jobs, chunksize=1):
            slot = runs.setdefault(ev.study_key(b, r), {}).setdefault(method, {k: [] for k in ("regret", "true_cost", "best_observed", "n_low", "n_high", "seconds", "seeds")})
            for k, v in rec.items():
                slot[k].append(v)
            slot["seeds"].append(seed)
    out = {"runs": runs, "meta": {"seeds": len(C.SWEEP_SEEDS), "jobs": len(jobs), "seconds": round(time.time() - t0)}}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "precomputed_study.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    print("fertig", len(jobs), "Läufe in", round(time.time() - t0), "s")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 14)
