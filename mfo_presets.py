"""Permalink (Begrenzen/Einrasten), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio)."""

import random
from dataclasses import dataclass

import streamlit as st

import mfo_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    choices: tuple | None = None       # erlaubte Werte bei Auswahlreglern (Permalink rastet ein bzw. fällt auf den Standard zurück)


SETTING_SPECS = {
    "b_slider": SettingSpec("b", int, C.DEFAULT_B, C.B_MIN, C.B_MAX),
    "r_select": SettingSpec("r", float, C.DEFAULT_R, choices=C.COST_RATIOS),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "study_budget": SettingSpec("sb", int, 40, choices=C.BUDGETS),
}
PRESET_KEYS = {"b": "b_slider", "r": "r_select", "seed": "seed_input"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def snap_to_choice(value, choices, default):
    """Erlaubter Wert: bei Zahlen der nächste, bei Zeichenketten nur ein Treffer, sonst der Standard."""
    if isinstance(default, str):
        return value if value in choices else default
    return min(choices, key=lambda c: abs(c - value))


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, begrenzt bzw. eingerastet."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            if spec.lo is not None:
                value = max(spec.lo, value)
            if spec.hi is not None:
                value = min(spec.hi, value)
            if spec.choices is not None:
                value = snap_to_choice(value, spec.choices, spec.default)
            st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
