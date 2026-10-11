"""Terminal-Scheibe als Tabelle: Kosten (EUR/h) je Einstellung [Plätze am Stapel, Tempo des Stapels] aus echten Simulationen,
zwei Genauigkeiten (3 000 und 15 000 Lkw, je 30 Wiederholungen) und eine Wahrheit aus 2 x 100 000 Lkw (aus bayes-opt-demo)."""

import json
import os

import numpy as np

import mfo_constants as C

_HERE = os.path.dirname(os.path.abspath(__file__))
_CACHE = {}


def _raw():
    if "raw" not in _CACHE:
        with open(os.path.join(_HERE, "precomputed_slice.json"), encoding="utf-8") as fh:
            _CACHE["raw"] = json.load(fh)
    return _CACHE["raw"]


def places():
    return list(_raw()["places"])


def speeds():
    return list(_raw()["speeds"])


def truth():
    """Wahre Kosten je Einstellung (Mittel aus zwei Läufen à 100 000 Lkw), Feld Plätze x Tempo."""
    return np.array(_raw()["truth"], float)


def reps(fidelity):
    """Wiederholungen [Plätze, Tempo, r] der Genauigkeit `fidelity` (0 = kurz, 1 = lang)."""
    return np.array(_raw()["reps"][str(C.TRUCKS_LOW if fidelity == 0 else C.TRUCKS_HIGH)], float)


def shape():
    return truth().shape


def n_cells():
    return int(np.prod(shape()))


def cell_ij(k):
    return divmod(int(k), shape()[1])


def unit_coords():
    """Koordinaten aller Einstellungen im Einheitsquadrat, Zeilen in der Reihenfolge i * Spalten + j."""
    r, c = shape()
    return np.array([[i / (r - 1), j / (c - 1)] for i in range(r) for j in range(c)], float)


class Simulator:
    """Auswertung einer Einstellung mit gewählter Genauigkeit: je Einstellung und Genauigkeit eine noch nicht benutzte der 30 Wiederholungen."""

    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)
        self.tables = (reps(0), reps(1))
        self.used = {}

    def observe(self, k, fidelity):
        i, j = cell_ij(k)
        used = self.used.setdefault((int(k), fidelity), [])
        free = [r for r in range(C.REPLICATES) if r not in used]
        if not free:
            used.clear()
            free = list(range(C.REPLICATES))
        r = int(self.rng.choice(free))
        used.append(r)
        return float(self.tables[fidelity][i, j, r])
