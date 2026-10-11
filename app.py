"""Mehrere Genauigkeiten: der kurze Lauf als Vorfilter - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Siebtes Stück der Linie Bayessche Optimierung. Eine einzelne Frage: Wann lohnt es sich, viele billige, ungenaue Läufe gegen wenige teure, genaue zu tauschen?
Vehikel: Terminal-Scheibe (Plätze x Tempo des Stapels) aus Tabellen echter Simulationen mit 3 000 und 15 000 Lkw; die Wahrheit liegt bei 2 x 100 000 Lkw.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import mfo_constants as C
import mfo_evaluation as ev
import mfo_scenario as S
from mfo_evaluation import Settings
from mfo_pdf_export import build_pdf
from mfo_presets import apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sync_query_params
from mfo_visualization import build_map_chart, build_ratio_chart, build_regret_chart

st.set_page_config(page_title="Mehrere Genauigkeiten – Sebastian Hanisch", layout="wide")


def de(x, nd=1):
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")


@st.cache_data(show_spinner=False)
def _live(settings):
    return {m: ev.run_one(m, settings.b, settings.r, settings.seed) for m in C.METHODS}


st.title("🔍 Mehrere Genauigkeiten: der kurze Lauf als Vorfilter")
st.markdown(
    """
Eine Simulation lässt sich oft **kurz und ungenau** oder **lang und genau** rechnen. Hier: ein Containerterminal, 3 000 Lkw (kurz) gegen 15 000 Lkw (lang), also ein Fünftel
des Aufwands bei größerer Streuung. Die Frage: Wie setzt man ein festes Rechenbudget ein, wenn man die **beste Einstellung** (Plätze am Stapel und Tempo des Stapels) sucht,
gemessen an der **Wahrheit** aus zwei Läufen mit je 100 000 Lkw? Verglichen werden sechs Verfahren: nur lange Läufe, nur kurze Läufe, jeweils zufällig oder mit
Bayesscher Optimierung, ein **Vorfilter** (kurz sieben, lang prüfen) und eine BO mit **beiden** Genauigkeiten als Modell-Eingabe. Die Demo ist das siebte und letzte Stück der Linie
**Bayessche Optimierung**; im Unterschied zu den Fall-Demos zeigt sie ein einziges Verfahren an einem wachsenden Beispiel.

Weiter unten: vier Experimente (**🔬**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("Was sich mit der Genauigkeit ändert", expanded=True):
    st.markdown(
        """
1. **Ein kurzer Lauf kostet weniger und streut mehr.** Hier ein Fünftel des Aufwands bei etwa der 4,5-fachen Varianz an den guten Einstellungen: je Kosteneinheit sind kurze Läufe
   **knapp** besser, solange sie höchstens etwa 0,22 eines langen kosten.
2. **Ein kurzer Lauf kann verzerrt sein.** Das ist der eigentliche Haken: Läuft das System kurz nicht ein, zeigt der kurze Lauf nicht dasselbe wie der lange. Hier ist die Verzerrung an
   den guten Einstellungen klein (Beträge unter 7 EUR/h), am Rand des stabilen Bereichs groß.
3. **Das Budget wird in Einheiten eines langen Laufs gezählt.** Ein kurzer Lauf kostet r dieser Einheit (Regler); r = 0,2 entspricht den echten Rechenzeiten.
4. **Maßstab ist die Wahrheit,** nicht der beste beobachtete Wert: Die beste Beobachtung unter vielen verrauschten Läufen ist zu schön.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
cols = st.columns(len(C.PRESETS))
for col, name in zip(cols, C.PRESETS):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Der Live-Lauf**")
    b = st.slider("Budget (Einheiten eines langen Laufs)", *bounds("b_slider"), key="b_slider", step=1, help="Gesamtes Rechenbudget; ein langer Lauf kostet 1.")
    r = st.select_slider("Kosten eines kurzen Laufs", C.COST_RATIOS, key="r_select",
                         help="In Einheiten eines langen Laufs. 0,2 entspricht den echten Rechenzeiten (3 000 gegen 15 000 Lkw); die Tabellen der Simulationen bleiben dieselben.")
    seed = st.number_input("Zufalls-Seed des Laufs", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Lauf generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"b_slider": int(b), "r_select": float(r), "seed_input": int(seed)})

settings = Settings(b=int(b), r=float(r), seed=int(seed))
with st.spinner("Läuft: sechs Verfahren (bei billigen kurzen Läufen einige Sekunden)…"):
    results = _live(settings)
opt_cost, opt_cell = ev.optimum()

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
st.caption(f"Budget {settings.b} Einheiten, ein kurzer Lauf kostet {de(settings.r, 1)}. Wahres Optimum: **{de(opt_cost, 0)} EUR/h** bei {S.places()[S.cell_ij(opt_cell)[0]]} Plätzen am Stapel "
           f"und Tempo {de(S.speeds()[S.cell_ij(opt_cell)[1]], 2)}. Regret = wahre Kosten der Empfehlung minus Optimum.")
cols = st.columns(3)
for k, m in enumerate(C.METHODS):
    x = results[m]
    cols[k % 3].metric(C.METHOD_LABELS[m], f"{de(x.regret)} EUR/h", delta=f"{x.n_low} kurz, {x.n_high} lang", delta_color="off",
                       help=f"Empfehlung: {S.places()[S.cell_ij(x.rec)[0]]} Plätze, Tempo {de(S.speeds()[S.cell_ij(x.rec)[1]], 2)}; wahre Kosten {de(x.true_cost, 0)} EUR/h.")
mshow = st.radio("Verfahren auf der Karte", C.METHODS, format_func=lambda m: C.METHOD_LABELS[m], index=C.METHODS.index("mf_bo"), key="map_method", horizontal=True)
st.caption(C.METHOD_HELP[mshow])
st.plotly_chart(build_map_chart(results[mshow], opt_cell), width="stretch", key=f"map_{mshow}")
st.download_button("📄 Auswertung als PDF", data=build_pdf(settings, results, opt_cost), file_name="mehrere_genauigkeiten_auswertung.pdf", mime="application/pdf", key="pdf_button")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wann lohnt der kurze Lauf?")
vpc = ev.variance_per_cost()
st.info(
    f"An den 20 besten Einstellungen streuen kurze Läufe mit Varianz {de(vpc['var_low'], 0)}, lange mit {de(vpc['var_high'], 0)}: das Verhältnis ist {de(vpc['ratio'], 1)}. "
    f"Ein langer Lauf lohnt sich je Kosteneinheit erst, wenn ein kurzer **mehr als das 1/{de(vpc['ratio'], 1)}-Fache** kostet, also ab r ≈ {de(vpc['break_even'], 2)}. "
    "Darunter sind viele kurze Läufe die bessere Währung; darüber nicht. Das ist die Rechnung ohne Verzerrung: sie gilt, weil der kurze Lauf an den guten Einstellungen nahezu unverzerrt ist."
)
st.caption("Ein einzelner Lauf zeigt nur, was bei diesem Seed geschah; die Experimente mitteln über 40 feste Läufe je Verfahren.")

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

sb = st.radio("Budget der Studie (Einheiten eines langen Laufs)", C.BUDGETS, key="study_budget", horizontal=True)
sr = st.select_slider("Kosten eines kurzen Laufs (Studie)", C.COST_RATIOS, value=0.2, key="study_r")
T = ev.table(sb, sr)

st.subheader("🔬 Experiment 1: Sechs Verfahren, ein Budget")
rows = []
for m in C.METHODS:
    st_ = ev.paired_stats(sb, sr, m, "random_high") if m != "random_high" else None
    verdict = "–" if st_ is None else f"{st_['better']} : {st_['worse']}, {ev.verdict_of(st_)}"
    rows.append(f"| {C.METHOD_LABELS[m]} | {de(T[m]['n_low'], 0)} | {de(T[m]['n_high'], 0)} | {de(T[m]['median'])} | {de(T[m]['q90'])} | {de(100 * T[m]['good'], 0)} % | {verdict} |")
st.markdown(
    f"**Budget {sb}, kurzer Lauf kostet {de(sr, 1)}, 40 feste Läufe.** Regret in EUR/h gegenüber dem Optimum von {de(opt_cost, 0)}; „gut“ heißt höchstens 5 % darüber. "
    "Gepaarter Vergleich mit „nur lange Läufe, Zufall“ (besser : schlechter, Vorzeichentest p < 0,05):\n\n"
    "| Verfahren | kurze Läufe | lange Läufe | Regret, Median | Regret, 90-%-Quantil | gute Empfehlungen | gegen Zufall mit langen Läufen |\n|---|---|---|---|---|---|---|\n" + "\n".join(rows)
)
st.plotly_chart(build_regret_chart([(m, T[m]["median"], T[m]["q90"]) for m in C.METHODS], "Verfahren"), width="stretch", key=f"regret_{sb}_{sr}")
st.info("Alle Verfahren landen im Mittel nahe am Optimum: die Fläche ist am Optimum flach, und die Scheibe hat nur 204 Einstellungen, von denen 40 lange Läufe schon ein Fünftel abdecken. "
        "Gemessen wird deshalb ein **kleiner** Unterschied; er ist nur an der Zahl der Läufe und an den Quantilen sichtbar.")

st.subheader("🔬 Experiment 2: Ab welchem Preis lohnt der kurze Lauf?")
by_ratio = {rr: {m: ev.table(sb, rr)[m]["median"] for m in C.METHODS} for rr in C.COST_RATIOS}
st.plotly_chart(build_ratio_chart(by_ratio, ("random_high", "bo_high", "bo_low", "sh", "mf_bo")), width="stretch", key=f"ratio_{sb}")
c_lo = ev.paired_stats(sb, 0.2, "bo_low", "random_high")
c_hi = ev.paired_stats(sb, 0.8, "bo_low", "random_high")
st.info(
    f"Mit Budget {sb}: BO nur mit kurzen Läufen ist bei r = 0,2 in {c_lo['better']} von {c_lo['n']} Läufen besser als Zufall mit langen Läufen ({ev.verdict_of(c_lo)}, p = {de(c_lo['p'], 3)}), "
    f"bei r = 0,8 in {c_hi['better']} ({ev.verdict_of(c_hi)}). **Die Vorteile der kurzen Läufe verschwinden ab r ≈ 0,5.** Das passt zur Streuungsrechnung oben, nicht zu der Annahme, mehr Genauigkeiten "
    "seien immer besser."
)

st.subheader("🔬 Experiment 3: Wie schön ist die beste Beobachtung?")
orows = []
for m in C.METHODS:
    orows.append(f"| {C.METHOD_LABELS[m]} | {de(T[m]['optimism'], 0)} |")
st.markdown(
    f"Bester beobachteter Wert minus wahre Kosten derselben Einstellung (Median, EUR/h; negativ = zu schön), Budget {sb}, r = {de(sr, 1)}:\n\n| Verfahren | Optimismus |\n|---|---|\n" + "\n".join(orows)
)
st.info("Je mehr verrauschte Läufe, desto schöner die beste Beobachtung: kurze Läufe erzeugen viele Beobachtungen, deren beste die Wahrheit unterschreitet. Wer die Empfehlung aus der besten "
        "Beobachtung abliest und nicht aus dem Modell oder einer langen Nachprüfung, überschätzt den Gewinn.")

st.subheader("🔬 Experiment 4: Beide Genauigkeiten im Modell oder nur sieben?")
a = ev.paired_stats(sb, sr, "mf_bo", "sh")
c = ev.paired_stats(sb, sr, "mf_bo", "bo_low")
d_ = ev.paired_stats(sb, sr, "mf_bo", "bo_high")
st.markdown(
    f"**Budget {sb}, r = {de(sr, 1)}** (gepaart, besser : schlechter):\n\n"
    f"- BO mit beiden Genauigkeiten gegen den Vorfilter: {a['better']} : {a['worse']}, {ev.verdict_of(a)} (p = {de(a['p'], 3)})\n"
    f"- BO mit beiden Genauigkeiten gegen BO nur mit kurzen Läufen: {c['better']} : {c['worse']}, {ev.verdict_of(c)} (p = {de(c['p'], 3)})\n"
    f"- BO mit beiden Genauigkeiten gegen BO nur mit langen Läufen: {d_['better']} : {d_['worse']}, {ev.verdict_of(d_)} (p = {de(d_['p'], 3)})"
)
st.info("Das zweistufige Modell ist bei billigen kurzen Läufen deutlich besser als BO nur mit langen Läufen, ist aber **nie nachweisbar besser** als die einfachere BO nur mit kurzen Läufen "
        "(bei Budget 40 und r = 0,1 sogar schlechter). Die Genauigkeit als Modell-Eingabe lohnt erst, wenn der kurze Lauf **verzerrt** ist, hier nicht an den guten Einstellungen.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der kurze Lauf ist an den guten Einstellungen nahezu unverzerrt** | Das ist hier der Fall (Beträge unter 7 EUR/h) und der Grund, warum kurze Läufe so gut abschneiden. Bei einem Einschwingvorgang, der erst nach langer Zeit endet, ist der kurze Lauf verzerrt und die Rechnung kippt. | Messung der Verzerrung vorab |
| **Zwei Genauigkeiten, Kostenverhältnis 0,2 gemessen, andere angenommen** | Nur die Rechenzeit 3 000 gegen 15 000 Lkw ist echt; die Kosten von 0,1 bis 0,8 sind eine Annahme über den Aufwand, die Tabellen bleiben dieselben. | Eigene Messung der Rechenzeiten |
| **Kleine Scheibe (204 Einstellungen)** | Auf einem Raster dieser Größe deckt schon ein Fünftel das Ganze ab; in höheren Dimensionen ist Abdeckung teurer und die Modelle gewinnen. | Größere Räume |
| **40 Läufe je Zelle** | Die Zellen trennen nur klare Unterschiede; viele Unterschiede liegen bei wenigen EUR/h. | Mehr Läufe |
| **Feste Aufteilung des Budgets** | Die Hälfte für kurze Läufe ist gesetzt, nicht optimiert; ein adaptives Verfahren (Hyperband, Knowledge Gradient) kann die Aufteilung anpassen. | Adaptive Verfahren |
| **Eigene, einfache Implementierung** | Gauß-Prozess mit der Genauigkeit als dritte Eingabe, nicht die Co-Kriging-Fassungen der Literatur; Zahlen anderer Bibliotheken können abweichen. | Vergleich mit BoTorch |
    """
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Beobachtungsmodell.** Ein Lauf der Genauigkeit $s \in \{0, 1\}$ (kurz, lang) an der Einstellung $x$ liefert

$$y = f(x) + b_s(x) + \varepsilon_s, \qquad \varepsilon_s \sim \mathcal{N}(0, \sigma_s^2)$$

mit der wahren Kostenfunktion $f$ (aus $2 \times 100\,000$ Lkw), der Verzerrung $b_s$ und dem Rauschen $\sigma_s^2$. Kosten des Laufs: $c_1 = 1$, $c_0 = r$.

**Streuung je Kosteneinheit.** $k$ kurze Läufe mitteln auf die Varianz $\sigma_0^2 / k$; für gleiche Kosten $k = 1/r$ gilt:

$$\frac{\sigma_0^2}{1/r} = r\,\sigma_0^2 \;<\; \sigma_1^2 \quad\Longleftrightarrow\quad r < \frac{\sigma_1^2}{\sigma_0^2}$$

**Ersatzmodell.** Gauß-Prozess über $(x, s)$ mit Matérn-5/2-Kern, je Eingabe (zwei für $x$, eine für $s$) ein Längenmaß; die Zielgröße geht als Logarithmus ein. Die Empfehlung ist
$\arg\min_x \mu(x, s{=}1)$.

**Erwartete Verbesserung** der langen Genauigkeit (Minimierung, $z = (f^\* - \mu)/s$):

$$\mathrm{EI}(x) = (f^\* - \mu(x, 1))\,\Phi(z) + s(x, 1)\,\varphi(z)$$

**Budgetaufteilung.** Der Anteil $\lambda = 0{,}5$ geht in kurze Läufe: $n_0 = \lfloor \lambda B / r \rfloor$ kurze und $n_1 = \lfloor B - n_0 r \rfloor$ lange Läufe.

**Literatur.** K. Kandasamy u. a. (2016), *Gaussian Process Bandit Optimisation with Multi-fidelity Evaluations*, NeurIPS; M. C. Kennedy, A. O'Hagan (2000), *Predicting the output from a
complex computer code when fast approximations are available*, Biometrika 87; L. Li u. a. (2018), *Hyperband: A Novel Bandit-Based Approach to Hyperparameter Optimization*, JMLR 18.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
