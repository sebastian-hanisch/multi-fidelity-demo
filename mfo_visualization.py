"""Plotly-Abbildungen (alle Achsen fest, damit Touch-Scrollen auf der Seite nicht am Diagramm hängen bleibt)."""

import numpy as np
import plotly.graph_objects as go

import mfo_constants as C
import mfo_scenario as S


def _fixed(fig, **layout):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.25), **layout)
    return fig


def build_map_chart(result, optimum_cell):
    """Terminal-Scheibe: wahre Kosten als Karte (Logarithmus), darauf die Läufe des Verfahrens (kurz = Kreis, lang = Raute), die Empfehlung (Stern) und das wahre Optimum (Kreuz)."""
    truth = S.truth()
    pl, sp = S.places(), S.speeds()
    fig = go.Figure(go.Heatmap(z=np.log10(np.minimum(truth, 3000)), x=sp, y=pl, colorscale="Greys", reversescale=True, showscale=False, hoverinfo="skip", opacity=0.55))

    def pts(cells):
        ij = [S.cell_ij(k) for k in cells]
        return [sp[j] for _, j in ij], [pl[i] for i, _ in ij]

    if result.lo_cells:
        x, y = pts(result.lo_cells)
        fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="kurze Läufe", marker=dict(color="#8c8c8c", size=7, symbol="circle-open", line=dict(width=1.2))))
    if result.hi_cells:
        x, y = pts(result.hi_cells)
        fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="lange Läufe", marker=dict(color=C.COLOR_OBS, size=9, symbol="diamond")))
    x, y = pts([result.rec])
    fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="Empfehlung", marker=dict(color=C.COLOR_NEXT, size=17, symbol="star", line=dict(width=1, color="white"))))
    x, y = pts([optimum_cell])
    fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="wahres Optimum", marker=dict(color=C.COLOR_BAD, size=13, symbol="x", line=dict(width=2))))
    fig.update_xaxes(title_text="Tempo des Stapels")
    fig.update_yaxes(title_text="Plätze am Stapel")
    return _fixed(fig, height=420)


def build_regret_chart(rows, title_x):
    """Balken: Median des Regrets je Verfahren (EUR/h) mit 90-%-Quantil als Fehlerbalken. rows: Liste (Verfahren, Median, q90)."""
    fig = go.Figure()
    for m, med, q90 in rows:
        fig.add_trace(go.Bar(x=[C.METHOD_LABELS[m]], y=[max(med, 0.05)], marker_color=C.METHOD_COLORS[m], name=C.METHOD_LABELS[m], showlegend=False,
                             error_y=dict(type="data", symmetric=False, array=[max(q90 - med, 0)], arrayminus=[0], color="#555", thickness=1.2),
                             hovertemplate="%{x}<br>Median %{y:.1f} EUR/h<extra></extra>"))
    fig.update_yaxes(title_text="Regret (EUR/h), Median und 90-%-Quantil", type="log")
    fig.update_xaxes(title_text=title_x, tickangle=-20)
    return _fixed(fig, height=380)


def build_ratio_chart(by_ratio, methods):
    """Median des Regrets über das Kostenverhältnis des kurzen Laufs; je Verfahren eine Linie. by_ratio: {r: {Verfahren: Median}}."""
    fig = go.Figure()
    rs = sorted(by_ratio)
    for m in methods:
        fig.add_trace(go.Scatter(x=[str(r) for r in rs], y=[max(by_ratio[r][m], 0.05) for r in rs], mode="lines+markers", name=C.METHOD_LABELS[m],
                                 line=dict(color=C.METHOD_COLORS[m], width=2.5)))
    fig.update_xaxes(title_text="Kosten eines kurzen Laufs (1 = so teuer wie ein langer)")
    fig.update_yaxes(title_text="Regret (EUR/h), Median (log)", type="log")
    return _fixed(fig, height=380)
