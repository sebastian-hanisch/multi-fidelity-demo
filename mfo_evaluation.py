"""Auswertung: ein Lauf je Verfahren, Empfehlung an der Wahrheit gemessen, vorgerechnete Studie mit gepaarten Läufen und Vorzeichentest."""

import json
import os
import time
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

import mfo_algorithm as A
import mfo_constants as C
import mfo_scenario as S

_HERE = os.path.dirname(os.path.abspath(__file__))


@dataclass(frozen=True)
class Settings:
    b: int = C.DEFAULT_B
    r: float = C.DEFAULT_R
    seed: int = C.DEFAULT_SEED


@dataclass
class Result:
    method: str
    rec: int                       # empfohlene Einstellung (Index im Raster)
    true_cost: float               # wahre Kosten der Empfehlung (EUR/h)
    regret: float                  # wahre Kosten minus wahres Optimum
    best_observed: float           # bester beobachteter Wert (Vergleich mit der Wahrheit zeigt die Verzerrung der Auswahl)
    n_low: int
    n_high: int
    spent: float
    lo_cells: list = field(default_factory=list)
    hi_cells: list = field(default_factory=list)
    seconds: float = 0.0


def optimum():
    t = S.truth()
    return float(t.min()), int(np.argmin(t))


def run_one(method, b, r, seed):
    coords = S.unit_coords()
    truth = S.truth().ravel()
    rng = np.random.default_rng(seed + 31 * (C.METHODS.index(method) + 1))
    sim = S.Simulator(seed + 7 * (C.METHODS.index(method) + 1))
    t0 = time.perf_counter()
    ncell = len(coords)
    lo_cells, hi_cells, lo_y, hi_y = [], [], [], []
    if method in ("random_high", "random_low"):
        fid = 1 if method == "random_high" else 0
        n = int(b / (1.0 if fid else r) + 1e-9)
        cells = A.sample_cells(n, ncell, rng)
        ys = [sim.observe(k, fid) for k in cells]
        rec = cells[int(np.argmin(ys))]
        (hi_cells if fid else lo_cells).extend(cells)
        (hi_y if fid else lo_y).extend(ys)
    elif method in ("bo_high", "bo_low"):
        fid = 1 if method == "bo_high" else 0
        n = int(b / (1.0 if fid else r) + 1e-9)
        cells, ys = A.bo_search(sim, fid, n, coords, rng)
        rec = A.recommend_single(coords, cells, ys)
        (hi_cells if fid else lo_cells).extend(cells)
        (hi_y if fid else lo_y).extend(ys)
    elif method == "sh":
        lo_cells, lo_y, hi_cells, hi_y, rec = A.successive_halving(sim, b, r, coords, rng)
    else:
        lo_cells, lo_y, hi_cells, hi_y, rec = A.mf_bo(sim, b, r, coords, rng)
    opt = float(truth.min())
    obs_all = (hi_y if hi_y else lo_y)
    return Result(method, int(rec), float(truth[rec]), float(truth[rec] - opt), float(min(obs_all)), len(lo_cells), len(hi_cells),
                  len(lo_cells) * r + len(hi_cells), list(map(int, lo_cells)), list(map(int, hi_cells)), time.perf_counter() - t0)


# --- Vorgerechnete Studie ------------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=1)
def study():
    with open(os.path.join(_HERE, "precomputed_study.json"), encoding="utf-8") as fh:
        return json.load(fh)


def study_key(b, r):
    return f"b{int(b)}_r{r:g}"


def regrets(b, r, method):
    return np.array(study()["runs"][study_key(b, r)][method]["regret"], float)


def table(b, r):
    """Je Verfahren: Median und 90-%-Quantil des Regrets (EUR/h), Anteil guter Empfehlungen (≤ 5 % über dem Optimum), mittlere Zahl kurzer und langer Läufe, Optimismus."""
    opt = optimum()[0]
    out = {}
    raw = study()["runs"][study_key(b, r)]
    for m, rec in raw.items():
        reg = np.array(rec["regret"], float)
        out[m] = {
            "median": float(np.median(reg)), "q90": float(np.quantile(reg, 0.9)), "good": float(np.mean(reg <= C.GOOD_WITHIN * opt)),
            "n_low": float(np.mean(rec["n_low"])), "n_high": float(np.mean(rec["n_high"])),
            "optimism": float(np.median(np.array(rec["best_observed"], float) - np.array(rec["true_cost"], float))),
            "seconds": float(np.median(rec["seconds"])),
        }
    return out


def paired_stats(b, r, a, base, tol=1e-9):
    """Gepaarter Vergleich der Verfahren a und base über die festen Läufe (Regret; negativ = a besser): besser, schlechter, gleich, Median der Differenz, p (Vorzeichentest)."""
    from scipy.stats import binomtest
    diff = regrets(b, r, a) - regrets(b, r, base)
    better, worse = int((diff < -tol).sum()), int((diff > tol).sum())
    p = float(binomtest(better, better + worse, 0.5).pvalue) if better + worse else 1.0
    return {"better": better, "worse": worse, "equal": int(len(diff) - better - worse), "median_diff": float(np.median(diff)), "p": p, "n": int(len(diff))}


def verdict_of(stats, alpha=0.05):
    if stats["p"] < alpha:
        return "besser" if stats["better"] > stats["worse"] else "schlechter"
    return "kein Unterschied nachweisbar"


def variance_per_cost():
    """Streuung der Wiederholungen je Genauigkeit an den 20 besten Einstellungen (Mittel der Varianzen) und Verhältnis kurz zu lang; Grundlage des Break-even-Kostenverhältnisses."""
    truth = S.truth()
    idx = np.unravel_index(np.argsort(truth.ravel())[:20], truth.shape)
    v_low = float(np.mean(S.reps(0).var(-1, ddof=1)[idx]))
    v_high = float(np.mean(S.reps(1).var(-1, ddof=1)[idx]))
    return {"var_low": v_low, "var_high": v_high, "ratio": v_low / v_high, "break_even": v_high / v_low}
