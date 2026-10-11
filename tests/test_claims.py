"""Jede Zahl aus dem README, nachgerechnet über dieselben Auswertungsfunktionen wie die App (vorgerechnete Studie: 2 Budgets x 5 Kostenverhältnisse x 6 Verfahren x 40 Läufe)."""

import pytest

import mfo_constants as C
import mfo_evaluation as ev
import mfo_scenario as S


def test_the_true_optimum_and_the_variance_ratio():
    cost, cell = ev.optimum()
    assert cost == pytest.approx(790.6, abs=0.1)
    assert (S.places()[S.cell_ij(cell)[0]], S.speeds()[S.cell_ij(cell)[1]]) == (5, 0.7)
    v = ev.variance_per_cost()
    assert v["ratio"] == pytest.approx(4.5, abs=0.1) and v["break_even"] == pytest.approx(0.22, abs=0.01)


def test_short_run_is_almost_unbiased_at_the_best_settings():
    import numpy as np
    truth = S.truth()
    idx = np.unravel_index(np.argsort(truth.ravel())[:20], truth.shape)
    bias = S.reps(0).mean(-1)[idx] - truth[idx]
    assert np.abs(bias).max() < 7.0
    assert np.abs(bias).mean() < 2.0


def test_cheap_bo_beats_random_long_runs_when_the_short_run_costs_a_fifth_or_less():
    for b in C.BUDGETS:
        for r in (0.1, 0.2):
            s = ev.paired_stats(b, r, "bo_low", "random_high")
            assert s["p"] < 0.05 and s["better"] > s["worse"], (b, r)


def test_the_advantage_is_gone_from_cost_ratio_half_upward():
    for b in C.BUDGETS:
        for r in (0.5, 0.8):
            assert ev.verdict_of(ev.paired_stats(b, r, "bo_low", "random_high")) != "besser", (b, r)
    s = ev.paired_stats(20, 0.8, "bo_low", "random_high")
    assert (s["better"], s["worse"]) == (7, 32)                              # bei kleinem Budget und teurem kurzem Lauf sogar schlechter


def test_two_fidelity_model_is_never_provably_better_than_cheap_only_bo():
    for b in C.BUDGETS:
        for r in C.COST_RATIOS:
            s = ev.paired_stats(b, r, "mf_bo", "bo_low")
            assert not (s["p"] < 0.05 and s["better"] > s["worse"]), (b, r)
    s = ev.paired_stats(40, 0.1, "mf_bo", "bo_low")
    assert (s["better"], s["worse"]) == (6, 17)


def test_two_fidelity_model_beats_long_run_bo_when_short_runs_are_cheap():
    for b, r in ((20, 0.1), (20, 0.2), (40, 0.1), (40, 0.2)):
        s = ev.paired_stats(b, r, "mf_bo", "bo_high")
        assert s["p"] < 0.05 and s["better"] > s["worse"], (b, r)


def test_long_run_bo_is_not_provably_better_than_random_long_runs():
    s = ev.paired_stats(40, 0.2, "bo_high", "random_high")
    assert (s["better"], s["worse"]) == (16, 18) and s["p"] > 0.5
    s20 = ev.paired_stats(20, 0.2, "bo_high", "random_high")
    assert s20["p"] < 0.05 and s20["worse"] > s20["better"]                # bei Budget 20 sogar schlechter


def test_best_observation_is_too_good_and_more_so_with_many_short_runs():
    t = ev.table(40, 0.2)
    assert t["random_low"]["optimism"] < t["random_high"]["optimism"] < 0
    assert t["bo_low"]["optimism"] == pytest.approx(-20, abs=3) and t["random_low"]["optimism"] == pytest.approx(-23, abs=3)
    assert t["random_high"]["optimism"] == pytest.approx(-3, abs=2)


def test_everything_lands_close_to_the_optimum_in_absolute_terms():
    opt = ev.optimum()[0]
    for b in C.BUDGETS:
        for r in C.COST_RATIOS:
            for m, x in ev.table(b, r).items():
                assert x["median"] < 0.05 * opt, (b, r, m)
                assert x["good"] >= 0.8, (b, r, m)


def test_short_run_is_strongly_biased_near_the_stability_edge():
    import numpy as np
    truth = S.truth()
    mid = (truth > 1200) & (truth < 3000)
    assert int(mid.sum()) == 7
    assert (S.reps(0).mean(-1) - truth)[mid].mean() == pytest.approx(-76, abs=3)
    assert (S.reps(1).mean(-1) - truth)[mid].mean() == pytest.approx(11, abs=3)
