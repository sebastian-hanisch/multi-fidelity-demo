"""Orakel-Tests: Gauß-Prozess gegen scikit-learn, Streuung je Kosteneinheit gegen Handformel, Empfehlungen gegen die Wahrheit, Studie gegen eigene Neuberechnung."""

import numpy as np
import pytest

import mfo_algorithm as A
import mfo_constants as C
import mfo_evaluation as ev
import mfo_scenario as S


def test_gp_posterior_equals_scikit_learn_for_fixed_hyperparameters():
    sk = pytest.importorskip("sklearn.gaussian_process")
    from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
    rng = np.random.default_rng(3)
    for trial in range(5):
        d = 2 + trial % 2
        X = rng.random((10, d))
        y = np.sin(3 * X[:, 0]) + X[:, 1]
        ls, var, nz = rng.uniform(0.3, 1.5, d), 1.3, 0.05
        gp = A.GaussianProcess()
        theta = np.concatenate([np.log(ls), [np.log(var), np.log(nz)]])
        gp.fit(X, y, hyper=theta)
        Xs = rng.random((6, d))
        mu, sd = gp.predict(Xs)
        z = (y - y.mean()) / max(y.std(), 1e-9)
        kern = ConstantKernel(var, "fixed") * Matern(length_scale=ls, nu=2.5, length_scale_bounds="fixed") + WhiteKernel(nz, "fixed")
        ref = sk.GaussianProcessRegressor(kern, alpha=1e-8, optimizer=None).fit(X, z)
        m_ref, s_ref = ref.predict(Xs, return_std=True)
        s_f = np.sqrt(np.maximum(s_ref ** 2 - nz, 1e-12))                    # sklearn gibt die Streuung der Beobachtung aus: Rauschen abziehen
        assert np.allclose(mu, m_ref * max(y.std(), 1e-9) + y.mean(), atol=1e-6), trial
        assert np.allclose(sd, s_f * max(y.std(), 1e-9), atol=1e-3), trial


def test_expected_improvement_equals_numerical_integration():
    from scipy.integrate import quad
    from scipy.stats import norm
    for mu, sd, best in [(0.3, 0.7, 0.0), (-0.5, 0.2, 0.1)]:
        ref = quad(lambda f: max(best - f, 0.0) * norm.pdf(f, mu, sd), mu - 12 * sd, mu + 12 * sd)[0]
        assert A.expected_improvement(np.array([mu]), np.array([sd]), best)[0] == pytest.approx(ref, abs=1e-8)


def test_variance_per_cost_equals_the_direct_computation_from_the_replicates():
    v = ev.variance_per_cost()
    truth = S.truth()
    idx = np.unravel_index(np.argsort(truth.ravel())[:20], truth.shape)
    lo = np.array([S.reps(0)[i, j].var(ddof=1) for i, j in zip(*idx)])
    hi = np.array([S.reps(1)[i, j].var(ddof=1) for i, j in zip(*idx)])
    assert v["var_low"] == pytest.approx(lo.mean()) and v["var_high"] == pytest.approx(hi.mean())
    assert v["break_even"] == pytest.approx(hi.mean() / lo.mean())


def test_mean_of_k_short_runs_has_the_variance_over_k():
    """Handformel hinter dem Break-even: Varianz des Mittels aus k kurzen Läufen = sigma^2 / k; Gegenprobe über Ziehungen aus den 30 Wiederholungen."""
    rng = np.random.default_rng(1)
    r = S.reps(0)[3, 2]
    sig2 = r.var()
    means = [rng.choice(r, size=5, replace=True).mean() for _ in range(20000)]
    assert np.var(means) == pytest.approx(sig2 / 5, rel=0.05)


def test_run_reports_true_cost_of_the_recommendation_and_the_budget_is_kept():
    truth = S.truth().ravel()
    for m in C.METHODS:
        x = ev.run_one(m, 20, 0.5, 3)
        assert x.true_cost == pytest.approx(truth[x.rec]) and x.regret == pytest.approx(truth[x.rec] - truth.min())
        assert x.spent <= 20 + 1e-9, m
        assert x.regret >= 0


def test_study_is_complete_and_every_run_stays_within_the_budget():
    raw = ev.study()["runs"]
    for b in C.BUDGETS:
        for r in C.COST_RATIOS:
            rec = raw[ev.study_key(b, r)]
            assert set(rec) == set(C.METHODS)
            for m, x in rec.items():
                assert len(x["regret"]) == 40
                spent = np.array(x["n_low"]) * r + np.array(x["n_high"])
                assert np.all(spent <= b + 1e-9), (b, r, m)
                assert np.all(np.array(x["regret"]) >= -1e-9)


def test_sign_test_matches_the_exact_binomial_by_hand():
    from math import comb
    from scipy.stats import binomtest
    p_hand = 2 * sum(comb(40, k) for k in range(0, 9)) / 2 ** 40               # 8 von 40
    assert binomtest(8, 40, 0.5).pvalue == pytest.approx(p_hand, rel=1e-9)
