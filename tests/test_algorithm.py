"""Einheiten des Kerns an Handrechnungen und Mini-Instanzen (DEMO-PLAYBOOK §1b)."""

import numpy as np
import pytest

import mfo_algorithm as A
import mfo_constants as C
import mfo_scenario as S


def test_matern_kernel_hand_values():
    x = np.array([[0.0]])
    assert A.matern52(x, x, np.array([1.0]), 2.0)[0, 0] == pytest.approx(2.0)
    k = A.matern52(x, np.array([[1.0]]), np.array([1.0]), 1.0)[0, 0]
    assert k == pytest.approx((1 + np.sqrt(5) + 5 / 3) * np.exp(-np.sqrt(5)))


def test_expected_improvement_hand_values():
    assert A.expected_improvement(np.array([0.0]), np.array([1.0]), 0.0)[0] == pytest.approx(0.3989422804)
    assert A.expected_improvement(np.array([-1.0]), np.array([1e-12]), 0.0)[0] == pytest.approx(1.0)
    assert A.expected_improvement(np.array([1.0]), np.array([1e-12]), 0.0)[0] == pytest.approx(0.0, abs=1e-12)


def test_budget_counts_by_hand():
    # Budget 40, r = 0,2, Hälfte kurz: 20 / 0,2 = 100 kurze Läufe (Kosten 20), Rest 20 lange Läufe
    assert A.budget_counts(40, 0.2) == (100, 20)
    assert A.budget_counts(40, 0.1) == (200, 20)
    assert A.budget_counts(20, 0.5) == (20, 10)
    assert A.budget_counts(10, 0.8, low_share=0.5) == (6, 5)           # 6 kurze kosten 4,8, Rest 5,2 -> 5 lange
    for b in (10, 40, 60):
        for r in C.COST_RATIOS:
            n_low, n_high = A.budget_counts(b, r)
            assert n_low * r + n_high <= b + 1e-9 and n_high >= 1


def test_sample_cells_has_no_repeats_until_every_cell_is_used():
    rng = np.random.default_rng(0)
    c = A.sample_cells(10, 10, rng)
    assert sorted(c) == list(range(10))
    c2 = A.sample_cells(25, 10, rng)
    assert len(c2) == 25 and max(np.bincount(c2)) <= 3
    assert len(set(c2[:10])) == 10


def test_gp_with_fidelity_input_tells_the_two_fidelities_apart():
    coords = np.linspace(0, 1, 8)[:, None]
    X = np.vstack([np.column_stack([coords, np.zeros(8)]), np.column_stack([coords, np.ones(8)])])
    y = np.concatenate([np.sin(3 * coords[:, 0]), np.sin(3 * coords[:, 0]) + 2.0])            # kurz: um 2 verschoben
    gp = A.GaussianProcess().fit(X, y)
    mu_lo, _ = gp.predict(np.array([[0.5, 0.0]]))
    mu_hi, _ = gp.predict(np.array([[0.5, 1.0]]))
    assert abs((mu_hi - mu_lo)[0] - 2.0) < 0.5


def test_gp_interpolates_noise_free_data(mini):
    coords, y = mini
    gp = A.GaussianProcess().fit(coords, y)
    mu, sd = gp.predict(coords)
    assert np.allclose(mu, y, atol=0.2)


def test_table_scenario_shapes_and_unused_replicates():
    assert S.shape() == (12, 17) and S.n_cells() == 204
    assert S.reps(0).shape == (12, 17, 30) and S.reps(1).shape == (12, 17, 30)
    sim = S.Simulator(1)
    first = [sim.observe(5, 1) for _ in range(30)]
    assert len(set(first)) == len(set(S.reps(1)[S.cell_ij(5)[0], S.cell_ij(5)[1]]))     # 30 Aufrufe nutzen alle 30 Wiederholungen einmal
    assert sorted(first) == sorted(S.reps(1)[S.cell_ij(5)[0], S.cell_ij(5)[1]].tolist())


def test_unit_coords_cover_the_unit_square_in_row_major_order():
    c = S.unit_coords()
    assert c.shape == (204, 2) and c.min() == 0 and c.max() == 1
    assert tuple(c[0]) == (0.0, 0.0) and tuple(c[16]) == (0.0, 1.0) and tuple(c[17]) == (pytest.approx(1 / 11), 0.0)
    assert S.cell_ij(17) == (1, 0)
