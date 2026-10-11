"""Kern der Demo: Gauß-Prozess (Matérn-5/2, Längenmaße und Rauschen gelernt), erwartete Verbesserung und sechs Suchverfahren auf der Terminal-Scheibe.

Alles auf einem Raster aus Einstellungen (Einheitsquadrat), Minimierung, nur numpy/scipy. Die Zielgröße geht als Logarithmus ins Modell (Kosten reichen von rund 800 bis
über 7 000 EUR/h). Eine Einheit = eine Regel (DEMO-PLAYBOOK §1b): `matern52`, `GaussianProcess.fit/predict`, `expected_improvement`, `budget_counts`, `random_search`,
`bo_search`, `recommend_single`, `successive_halving`, `mf_bo`. Zufall nur über übergebene Generatoren.
"""

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize
from scipy.stats import norm

import mfo_constants as C


def matern52(A, B, lengthscales, variance):
    """Matérn-5/2-Kern k(a, b) = σ² (1 + √5 r + 5r²/3) exp(−√5 r), r = Abstand mit je Eingabe eigenem Längenmaß."""
    r2 = np.maximum((((A[:, None, :] - B[None, :, :]) / lengthscales) ** 2).sum(-1), 0.0)
    s = np.sqrt(5.0) * np.sqrt(r2)
    return variance * (1.0 + s + s * s / 3.0) * np.exp(-s)


class GaussianProcess:
    """Gauß-Prozess-Regression, Ausgabe standardisiert; Längenmaße, Signal- und Rauschvarianz durch Maximieren der Randwahrscheinlichkeit (L-BFGS-B, feste Starts)."""

    def __init__(self, restarts=2):
        self.restarts = restarts
        self.theta_ = None

    @staticmethod
    def _unpack(theta, d):
        return np.exp(theta[:d]), np.exp(theta[d]), np.exp(theta[d + 1])

    def _neg_log_marginal(self, theta, X, z):
        ls, var, nz = self._unpack(theta, X.shape[1])
        K = matern52(X, X, ls, var) + (nz + 1e-8) * np.eye(len(X))
        try:
            c = cho_factor(K, lower=True)
        except np.linalg.LinAlgError:
            return 1e10
        a = cho_solve(c, z)
        return 0.5 * z @ a + np.log(np.diag(c[0])).sum() + 0.5 * len(z) * np.log(2 * np.pi)

    def fit(self, X, y, hyper=None):
        """Anpassen. `hyper` = früherer Parameterstand: dann nur Zerlegung neu (keine Optimierung)."""
        X, y = np.asarray(X, float), np.asarray(y, float)
        self.X = X
        self.y_mean, self.y_std = float(y.mean()), max(float(y.std()), 1e-9)
        z = (y - self.y_mean) / self.y_std
        d = X.shape[1]
        if hyper is None:
            bounds = [(np.log(0.05), np.log(10.0))] * d + [(np.log(0.05), np.log(10.0)), (np.log(1e-6), np.log(2.0))]
            starts = np.random.default_rng(0).uniform(0.15, 1.0, (self.restarts, d))
            best = None
            for r in range(self.restarts):
                th0 = np.concatenate([np.log(starts[r]), [0.0, np.log(1e-2)]])
                res = minimize(self._neg_log_marginal, th0, args=(X, z), method="L-BFGS-B", bounds=bounds, options={"maxiter": 80})
                if best is None or res.fun < best.fun:
                    best = res
            hyper = best.x
        self.theta_ = np.asarray(hyper, float)
        self.lengthscales, self.variance, self.noise = self._unpack(self.theta_, d)
        K = matern52(X, X, self.lengthscales, self.variance) + (self.noise + 1e-8) * np.eye(len(X))
        self._chol = cho_factor(K, lower=True)
        self._alpha = cho_solve(self._chol, z)
        return self

    def predict(self, Xs):
        """Mittelwert und Standardabweichung der **Funktion** (ohne Beobachtungsrauschen)."""
        Ks = matern52(np.asarray(Xs, float), self.X, self.lengthscales, self.variance)
        mu = Ks @ self._alpha
        v = cho_solve(self._chol, Ks.T)
        var = np.maximum(self.variance - (Ks * v.T).sum(1), 1e-12)
        return mu * self.y_std + self.y_mean, np.sqrt(var) * self.y_std


def expected_improvement(mu, sd, best):
    """Erwartete Verbesserung (Minimierung): E[max(best − f, 0)], f ~ N(mu, sd²)."""
    sd = np.maximum(np.asarray(sd, float), 1e-12)
    z = (best - mu) / sd
    return (best - mu) * norm.cdf(z) + sd * norm.pdf(z)


def budget_counts(budget, ratio, low_share=C.LOW_SHARE):
    """(kurze Läufe, lange Läufe) der zweistufigen Verfahren: `low_share` des Budgets für kurze Läufe zum Preis `ratio`, der Rest für lange Läufe zum Preis 1."""
    n_low = int(low_share * budget / ratio + 1e-9)
    n_high = max(int((budget - n_low * ratio) + 1e-9), 1)
    return n_low, n_high


def sample_cells(n, n_cells, rng):
    """n Einstellungen zufällig, ohne Wiederholung, solange es geht (danach neue Durchgänge)."""
    out = []
    while len(out) < n:
        out.extend(rng.permutation(n_cells).tolist())
    return out[:n]


def _features(coords, fidelity=None):
    if fidelity is None:
        return coords
    return np.column_stack([coords, np.full(len(coords), float(fidelity))])


def bo_search(sim, fidelity, n_evals, coords, rng, refit_every=4, n_start=6):
    """Bayessche Optimierung auf einer Genauigkeit. Gibt (Zellen, Beobachtungen) zurück; jede Beobachtung geht als Logarithmus ins Modell."""
    ncell = len(coords)
    cells = sample_cells(min(n_start, n_evals), ncell, rng)
    ys = [sim.observe(k, fidelity) for k in cells]
    hyper = None
    step = 0
    refit_every = max(refit_every, n_evals // 20)               # bei sehr vielen kurzen Läufen seltener neu anpassen (Rechenzeit)
    while len(cells) < n_evals:
        gp = GaussianProcess().fit(coords[cells], np.log(ys), hyper=hyper if step % refit_every else None)
        hyper = gp.theta_
        mu_all, sd_all = gp.predict(coords)
        best = float(np.min(mu_all[np.unique(cells)]))
        k = int(np.argmax(expected_improvement(mu_all, sd_all, best)))
        cells.append(k)
        ys.append(sim.observe(k, fidelity))
        step += 1
    return cells, ys


def recommend_single(coords, cells, ys):
    """Einstellung mit dem kleinsten Modellmittel eines Modells, das nur auf einer Genauigkeit angepasst ist."""
    gp = GaussianProcess().fit(coords[cells], np.log(ys))
    mu, _ = gp.predict(coords)
    return int(np.argmin(mu))


def mf_bo(sim, budget, ratio, coords, rng, low_share=C.LOW_SHARE):
    """Zwei Phasen: kurze Läufe an zufälligen Einstellungen (ohne Wiederholung), dann Bayessche Optimierung mit der Genauigkeit als dritter Eingabe; die langen Läufe
    maximieren die erwartete Verbesserung der langen Genauigkeit. Gibt (kurze Zellen, kurze Werte, lange Zellen, lange Werte, Empfehlung) zurück."""
    ncell = len(coords)
    n_low, n_high = budget_counts(budget, ratio, low_share)
    lo_cells = sample_cells(n_low, ncell, rng)
    lo_y = [sim.observe(k, 0) for k in lo_cells]
    hi_cells, hi_y = [], []
    hyper = None
    for step in range(n_high):
        X = np.vstack([_features(coords[lo_cells], 0), _features(coords[hi_cells], 1)]) if hi_cells else _features(coords[lo_cells], 0)
        y = np.log(lo_y + hi_y)
        gp = GaussianProcess().fit(X, y, hyper=hyper if step % 3 else None)
        hyper = gp.theta_
        mu, sd = gp.predict(_features(coords, 1))
        best = float(np.min(mu))
        k = int(np.argmax(expected_improvement(mu, sd, best)))
        hi_cells.append(k)
        hi_y.append(sim.observe(k, 1))
    X = np.vstack([_features(coords[lo_cells], 0), _features(coords[hi_cells], 1)])
    gp = GaussianProcess().fit(X, np.log(lo_y + hi_y), hyper=hyper)
    mu, _ = gp.predict(_features(coords, 1))
    return lo_cells, lo_y, hi_cells, hi_y, int(np.argmin(mu))


def successive_halving(sim, budget, ratio, coords, rng, low_share=C.LOW_SHARE):
    """Zwei feste Stufen: kurze Läufe an zufälligen Einstellungen, die besten davon (nach kurzem Wert) lang prüfen; empfohlen wird der beste lange Wert."""
    ncell = len(coords)
    n_low, n_high = budget_counts(budget, ratio, low_share)
    lo_cells = sample_cells(n_low, ncell, rng)
    lo_y = np.array([sim.observe(k, 0) for k in lo_cells])
    mean_by_cell = {}
    for k, v in zip(lo_cells, lo_y):
        mean_by_cell.setdefault(k, []).append(v)
    ranked = sorted(mean_by_cell, key=lambda k: float(np.mean(mean_by_cell[k])))
    hi_cells = ranked[:n_high]
    hi_y = [sim.observe(k, 1) for k in hi_cells]
    return lo_cells, list(lo_y), hi_cells, hi_y, int(hi_cells[int(np.argmin(hi_y))])
