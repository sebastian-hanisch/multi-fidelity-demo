"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mini():
    """Vier Einstellungen auf einer Linie; Kosten 5, 1, 3, 4 (Minimum bei Index 1)."""
    coords = np.array([[0.0, 0.0], [1 / 3, 0.0], [2 / 3, 0.0], [1.0, 0.0]])
    return coords, np.array([5.0, 1.0, 3.0, 4.0])
