# Mehrere Genauigkeiten: der kurze Lauf als Vorfilter – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-multi-fidelity-demo.streamlit.app/)**

Siebtes und letztes Stück der **Bayessche-Optimierung-Linie** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“.
Es setzt [bayes-opt-demo](https://github.com/sebastian-hanisch/bayes-opt-demo) und [noisy-bo-demo](https://github.com/sebastian-hanisch/noisy-bo-demo) fort und fragt, wann
viele billige, ungenaue Läufe gegen wenige teure, genaue lohnen. Im Unterschied zu den Fall-Demos zeigt die Demo ein einziges Verfahren an einem wachsenden Beispiel.

## Warum dieses Problem

Eine Simulation lässt sich oft kurz und ungenau oder lang und genau rechnen. Hier: ein Containerterminal mit 3 000 Lkw (kurz) gegen 15 000 Lkw (lang), also ein Fünftel des
Aufwands bei größerer Streuung. Die Kernfrage: **Wie setzt man ein festes Rechenbudget ein, um die beste Einstellung (Plätze am Stapel, Tempo des Stapels) zu finden, gemessen an
der Wahrheit?**

## Modell

- **Vehikel:** Terminal-Scheibe aus Tabellen echter Simulationen (aus `bayes-opt-demo`): 12 Platzzahlen x 17 Tempi = 204 Einstellungen, je 30 Wiederholungen mit 3 000 und mit
  15 000 Lkw, dazu eine **Wahrheit** (Mittel aus zwei Läufen mit je 100 000 Lkw). Kosten in EUR/h.
- **Budget:** in Einheiten eines langen Laufs (1). Ein kurzer Lauf kostet r dieser Einheit; r = 0,2 entspricht den echten Rechenzeiten, 0,1 bis 0,8 sind **Annahmen** über das
  Kostenverhältnis (die Tabellen bleiben dieselben).
- **Verfahren:** Zufall mit langen Läufen, Zufall mit kurzen Läufen, BO mit langen Läufen, BO mit kurzen Läufen, **Vorfilter** (die Hälfte des Budgets kurz sieben, die besten lang
  prüfen, beste lange Beobachtung empfehlen) und **BO mit beiden Genauigkeiten** (kurze Phase, dann Gauß-Prozess über Einstellung und Genauigkeit, lange Läufe nach erwarteter
  Verbesserung der langen Genauigkeit). Zufallsverfahren empfehlen die beste Beobachtung, die Modellverfahren den Punkt mit dem kleinsten Modellmittel.
- **Maßstab:** wahre Kosten der Empfehlung minus wahres Optimum (Regret, EUR/h); „gut“ heißt höchstens 5 % über dem Optimum.
- **Live-Teil:** ein Lauf je Verfahren mit Karte der Einstellungen. Die Studie ist vorgerechnet (`precomputed_study.json`, 2 400 Läufe, `generate_study.py`).
- Mathematik im 📐-Expander der App.

## Methodik

Je Zelle (Budget 20 oder 40, Kostenverhältnis, Verfahren) **40 feste Läufe** (Seeds 900000 bis 900039); jedes Verfahren eines Seeds zieht aus denselben Tabellen. Unterschiede werden
mit dem Vorzeichentest gepaart geprüft (`scipy.stats.binomtest`); „kein Unterschied nachweisbar“ heißt nicht „kein Unterschied“.

## Befunde (gemessen, keine Behauptungen)

| Frage | Befund |
|---|---|
| Wie nah am Optimum landet man überhaupt? | **Sehr nah, bei allen Verfahren.** Wahres Optimum 790,6 EUR/h (5 Plätze, Tempo 0,7); der mediane Regret liegt in jeder der 60 Zellen unter 5 % davon, meist bei wenigen EUR/h, und mindestens 80 % der Empfehlungen sind „gut“. Gemessen wird ein **kleiner** Unterschied. |
| Wann lohnt der kurze Lauf? | An den 20 besten Einstellungen ist die Varianz des kurzen Laufs das 4,5-Fache des langen (Break-even: ein kurzer Lauf lohnt je Kosteneinheit, wenn er weniger als etwa 0,22 eines langen kostet). **BO nur mit kurzen Läufen schlägt Zufall mit langen Läufen bei r = 0,1 und 0,2 in beiden Budgets** (z. B. Budget 40, r = 0,2: 26 : 9, p = 0,006). |
| Ab wann verschwindet der Vorteil? | **Ab r = 0,5**: kein nachweisbarer Unterschied; bei Budget 20 und r = 0,8 ist BO mit kurzen Läufen sogar schlechter (7 : 32). |
| Lohnen beide Genauigkeiten im Modell? | **Nein, hier nicht:** BO mit beiden Genauigkeiten ist nie nachweisbar besser als BO nur mit kurzen Läufen (Budget 40, r = 0,1: schlechter, 6 : 17). Gegenüber BO nur mit langen Läufen ist sie bei billigen kurzen Läufen deutlich besser (z. B. Budget 40, r = 0,2: 27 : 10, p = 0,008). Der kurze Lauf ist hier an den guten Einstellungen nahezu unverzerrt (Beträge unter 7 EUR/h), das Modell der Genauigkeit hat nichts zu korrigieren. |
| Ist BO mit langen Läufen besser als Zufall? | **Nein:** bei Budget 40 16 : 18 (p > 0,5), bei Budget 20 sogar schlechter. Die Scheibe ist klein (204 Einstellungen); 40 lange Zufallsläufe decken ein Fünftel ab. |
| Wie schön ist die beste Beobachtung? | **Zu schön, und mehr mit vielen kurzen Läufen:** Median von bester Beobachtung minus wahre Kosten bei Budget 40, r = 0,2: −23 EUR/h (Zufall kurz), −20 (BO kurz), −3 (Zufall lang). |

Jede Zahl ist in `tests/test_claims.py` nachgerechnet.

## Ehrliche Grenzen

- **Der kurze Lauf ist hier fast unverzerrt.** Das ist die günstigste Lage für kurze Läufe und der Grund für das Ergebnis; bei einem Einschwingvorgang, der erst spät endet, ist der
  kurze Lauf verzerrt und die Rechnung kippt. Am Rand des stabilen Bereichs ist die Verzerrung auch hier groß (Mittel −76 EUR/h bei Kosten zwischen 1 200 und 3 000), liegt aber nicht
  bei den guten Einstellungen.
- **Kostenverhältnis nur bei 0,2 gemessen**, die anderen Werte sind Annahmen über den Aufwand; die Tabellen bleiben dieselben.
- **Kleine, flache Scheibe:** die Unterschiede liegen bei wenigen EUR/h; in höheren Dimensionen ist die Abdeckung durch billige Läufe teurer, und die Modelle gewinnen.
- **Feste Aufteilung** (die Hälfte des Budgets kurz); adaptive Verfahren (Hyperband, Knowledge Gradient) sind nicht verglichen.
- **Eigene, einfache Implementierung** (Genauigkeit als dritte Eingabe eines Gauß-Prozesses, nicht Co-Kriging); Zahlen anderer Bibliotheken können abweichen.
- **40 Läufe je Zelle:** der Test trennt nur klare Unterschiede.

## Verifikation

- **Kern:** Kern, erwartete Verbesserung, Budgetaufteilung, Ziehen ohne Wiederholung und die Tabelle (jede Wiederholung genau einmal) gegen Handrechnung auf Mini-Instanzen.
- **Orakel:** Gauß-Prozess-Vorhersage gegen scikit-learn bei festen Hyperparametern (Mittelwert und Streuung der Funktion); erwartete Verbesserung gegen numerische Integration;
  Streuung je Kosteneinheit gegen direkte Berechnung aus den Wiederholungen; Varianz eines Mittels aus k Läufen gegen die Handformel σ²/k; Empfehlungen gegen die Wahrheit; Studie
  gegen das Budget geprüft.
- **Aussagen:** `tests/test_claims.py` rechnet jede README-Zahl über dieselben Auswertungsfunktionen wie die App nach.
- **Presets:** vollständig, Werte innerhalb der Reglergrenzen, Standard-Preset gleich Standardeinstellung.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler und jede Auswahl an beiden Enden) und Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `mfo_algorithm.py` | Kern: Kern, Gauß-Prozess, erwartete Verbesserung, Suchverfahren, Vorfilter |
| `mfo_scenario.py` | Terminal-Scheibe aus Tabellen echter Simulationen |
| `mfo_evaluation.py` | Läufe, Empfehlung an der Wahrheit, vorgerechnete Studie, gepaarte Statistik |
| `mfo_constants.py` | Verfahren, Budgets, Kostenverhältnisse, Regler-Grenzen, Farben, Presets |
| `mfo_presets.py` | Permalink (Begrenzen/Einrasten), Presets, Zufalls-Seed-Button |
| `mfo_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `mfo_pdf_export.py` | PDF-Auswertung des Live-Laufs |
| `generate_study.py` | erzeugt `precomputed_study.json` |
| `precomputed_slice.json` | Tabellen der Simulationen (kurz und lang) und Wahrheit, aus `bayes-opt-demo` |
| `precomputed_study.json` | 2 400 Läufe der Studie |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `requirements-dev.txt` | Laufzeit plus pytest, scikit-learn |
| `tests/` | Handrechnung, Orakel, Aussagen, Presets, AppTest-Smoke-Test, Footer |

## Bewusst nicht umgesetzt

- Hyperband und andere adaptive Verfahren, Co-Kriging und Knowledge Gradient: andere Verfahren bzw. eigene Messungen.
- Eine eigene Messung der Rechenzeiten je Genauigkeit und mehr als zwei Genauigkeiten.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, SciPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
