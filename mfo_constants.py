"""Konstanten der Demo „Mehrere Genauigkeiten“: Terminal-Scheibe, Verfahren, Studie, Regler, Presets, Farben."""

# --- Vehikel: Terminal-Scheibe (Plätze am Stapel x Tempo des Stapels) aus Tabellen echter Simulationen -------------------------------------------
TRUCKS_LOW, TRUCKS_HIGH = 3000, 15000      # Länge der kurzen und der langen Simulation (Lkw)
REPLICATES = 30                            # Wiederholungen je Einstellung und Genauigkeit in der Tabelle
TRUE_COST_RATIO = TRUCKS_LOW / TRUCKS_HIGH  # Rechenaufwand des kurzen Laufs gegenüber dem langen (0,2)

# --- Verfahren ----------------------------------------------------------------------------------------------------------------------------
METHODS = ("random_high", "random_low", "bo_high", "bo_low", "sh", "mf_bo")
METHOD_LABELS = {
    "random_high": "Zufall, nur lange Läufe",
    "random_low": "Zufall, nur kurze Läufe",
    "bo_high": "BO, nur lange Läufe",
    "bo_low": "BO, nur kurze Läufe",
    "sh": "Vorfilter (kurz sieben, dann lang prüfen)",
    "mf_bo": "BO mit beiden Genauigkeiten",
}
METHOD_HELP = {
    "random_high": "Zufällige Einstellungen mit langem Lauf auswerten, die beste Beobachtung empfehlen.",
    "random_low": "Fünfmal so viele zufällige Einstellungen, aber nur kurze Läufe; die beste Beobachtung empfehlen.",
    "bo_high": "Bayessche Optimierung mit Gauß-Prozess auf den langen Läufen; empfohlen wird die Einstellung mit dem besten Modellmittel.",
    "bo_low": "Dasselbe auf kurzen Läufen: viel mehr Auswertungen für dasselbe Budget, jede mit mehr Streuung.",
    "sh": "Erst kurze Läufe an vielen zufälligen Einstellungen, dann die besten davon lang prüfen; empfohlen wird die beste lange Beobachtung (Successive Halving mit zwei festen Stufen).",
    "mf_bo": "Zuerst kurze Läufe, dann Bayessche Optimierung mit der Genauigkeit als Eingabe des Modells, um die langen Läufe gezielt zu setzen.",
}
METHOD_COLORS = {"random_high": "#8c8c8c", "random_low": "#B8B8B8", "bo_high": "#14233B", "bo_low": "#7B5EA7", "sh": "#D68A2E", "mf_bo": "#2F6B65"}

# --- Studie -------------------------------------------------------------------------------------------------------------------------------
BUDGETS = (20, 40)                         # in Einheiten eines langen Laufs
COST_RATIOS = (0.1, 0.2, 0.3, 0.5, 0.8)    # Kosten eines kurzen Laufs in Einheiten eines langen
LOW_SHARE = 0.5                            # Anteil des Budgets für die kurze Phase von Vorfilter und BO mit beiden Genauigkeiten
SWEEP_SEEDS = tuple(range(900000, 900040))
GOOD_WITHIN = 0.05                         # „gute“ Empfehlung: wahrer Wert höchstens 5 % über dem Optimum

# --- Regler -----------------------------------------------------------------------------------------------------------------------------
B_MIN, B_MAX, DEFAULT_B = 10, 40, 40
SEED_MAX, DEFAULT_SEED = 999999, 35
DEFAULT_R = 0.2

PRESETS = {
    "Standardfall (Voreinstellung)": {"b": DEFAULT_B, "r": 0.2, "seed": DEFAULT_SEED},
    "Kleines Budget": {"b": 10, "r": 0.2, "seed": DEFAULT_SEED},
    "Kurzer Lauf fast so teuer": {"b": DEFAULT_B, "r": 0.8, "seed": DEFAULT_SEED},
    "Kurzer Lauf sehr billig": {"b": DEFAULT_B, "r": 0.1, "seed": DEFAULT_SEED},
    "Mittleres Budget": {"b": 20, "r": 0.3, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "40 Einheiten, der kurze Lauf kostet ein Fünftel eines langen (3 000 statt 15 000 Lkw).",
    "Kleines Budget": "Nur 10 Einheiten: zehn lange oder fünfzig kurze Läufe.",
    "Kurzer Lauf fast so teuer": "Der kurze Lauf kostet 80 % eines langen: kaum noch Ersparnis, bei deutlich mehr Streuung.",
    "Kurzer Lauf sehr billig": "Der kurze Lauf kostet ein Zehntel: doppelt so viele kurze Läufe wie im Standardfall, ihre Streuung bleibt.",
    "Mittleres Budget": "20 Einheiten, kurzer Lauf kostet 30 %: der Vorteil der kurzen Läufe wird dünn.",
}
COLOR_OBS = "#2F6B65"
COLOR_BAD = "#B3463A"
COLOR_NEXT = "#D68A2E"
