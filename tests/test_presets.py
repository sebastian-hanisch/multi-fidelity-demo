"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen."""

import mfo_constants as C
import mfo_evaluation as ev
import mfo_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds():
    for preset in C.PRESETS.values():
        assert C.B_MIN <= preset["b"] <= C.B_MAX and preset["r"] in C.COST_RATIOS and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS["Standardfall (Voreinstellung)"]
    assert ev.Settings(b=p["b"], r=p["r"], seed=p["seed"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) <= set(P.SETTING_SPECS)


def test_snap_to_choice_for_cost_ratios():
    assert P.snap_to_choice(0.25, C.COST_RATIOS, 0.2) in (0.2, 0.3)
    assert P.snap_to_choice(9.0, C.COST_RATIOS, 0.2) == 0.8
