"""PDF-Export des Live-Laufs (fpdf2, Kernschriften; Umlaute sind dort erlaubt, Gedankenstrich und Eurozeichen nicht)."""

from fpdf import FPDF

import mfo_constants as C


def _num(x, nd=1):
    return f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")


def build_pdf(settings, results, optimum):
    """Einseitiger Bericht: Einstellungen und je Verfahren Empfehlung, Regret und Zahl der Läufe. Gibt die Bytes der PDF-Datei zurück."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Mehrere Genauigkeiten: der kurze Lauf als Vorfilter", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Sebastian Hanisch, Operations Research und Machine Learning", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Einstellungen", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for k, v in (("Budget (Einheiten eines langen Laufs)", str(settings.b)), ("Kosten eines kurzen Laufs", _num(settings.r, 2)), ("Zufalls-Seed", str(settings.seed)),
                 ("Wahres Optimum (EUR/h)", _num(optimum))):
        pdf.cell(80, 6, k)
        pdf.cell(0, 6, v, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Empfehlung je Verfahren (Regret = wahre Kosten minus Optimum, EUR/h)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for m, x in results.items():
        pdf.cell(0, 6, f"{C.METHOD_LABELS[m]}: Regret {_num(x.regret)}, {x.n_low} kurze und {x.n_high} lange Läufe", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, "Ein einzelner Lauf zeigt nur, was bei diesem Seed geschah; die Studie der Demo mittelt über 40 feste Läufe je Verfahren.")
    return bytes(pdf.output())
