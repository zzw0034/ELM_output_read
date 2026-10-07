"""
Talk slide (user request 2026-10-07): put the RF / RH carbon benefits in context of published U.S. and Southeast numbers.
Editable one-slide pptx: native title, callout and source line, plus a horizontal bar chart (matplotlib PNG) of annual
rates in Tg CO2 per year.

This study (4 km, cumulative NBP 2024-2100 over 77 years, 1 PgC = 3.664 Pg CO2): RF - Default 3.7-5.3 PgC ->
176-252 Tg CO2/yr; RH - Default 1.0-1.5 PgC -> 48-71 Tg CO2/yr. References (as retrieved 2026-10-07; check before citing):
  Fargione et al. 2018 Sci. Adv. 4: eaat1869, U.S. maximum potentials: reforestation 307, natural forest management
    (extended harvest cycles) 267 Tg CO2e/yr
  Domke et al. 2020 PNAS 117: 24649, fully stocking understocked U.S. forestland 187.7 Tg CO2/yr
  USDA Forest Service (Treesearch 52758): Southern forests net accumulation ~75 TgC/yr in 2007-2012 (= 275 Tg CO2/yr)
  EPA GHG Inventory 2024: U.S. gross emissions 2022 6,343 Mt CO2e; LULUCF net removals 922 Mt CO2e
Callout: 13.6-19.4 Gt CO2 = 2.1-3.1 years of total U.S. emissions.

Runs locally, from the analysis root:
    uv run --no-project --with python-pptx --with matplotlib python code/supplement/talk_context_slide.py
Output: figures/slides/context_comparison.pptx and context_comparison_chart.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "figures/slides")
C_PER_CO2 = 3.664
YEARS = 77
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e9e8e4"
RF, RH, REF = "#2a78d6", "#eb6834", "#9a9893"
US_EMIS_2022 = 6343.0          # Mt CO2e, EPA

# (label, low, high, colour, note)  -- Tg CO2 per year
ROWS = [
    ("This study: restoration + protection (RF)\nSoutheast, 2024–2100 mean", 3.7, 5.3, RF, "PgC"),
    ("This study: reduced harvest (RH)\nSoutheast, 2024–2100 mean", 1.0, 1.5, RH, "PgC"),
    ("Southeast forests' current net sink\nUSDA Forest Service, 2007–2012", 275, 275, REF, "Tg"),
    ("U.S. reforestation, max. potential\nFargione et al. 2018", 307, 307, REF, "Tg"),
    ("U.S. longer harvest cycles, max. potential\nFargione et al. 2018", 267, 267, REF, "Tg"),
    ("U.S. restocking understocked forests\nDomke et al. 2020", 188, 188, REF, "Tg"),
]


def rate(lo, hi, unit):
    if unit == "PgC":
        return lo * 1000 * C_PER_CO2 / YEARS, hi * 1000 * C_PER_CO2 / YEARS
    return lo, hi


def chart(path):
    fig, ax = plt.subplots(figsize=(8.6, 5.4), facecolor="white")
    y = list(range(len(ROWS)))[::-1]
    for yi, (lab, lo, hi, col, unit) in zip(y, ROWS):
        a, b = rate(lo, hi, unit)
        if a == b:
            ax.barh(yi, a, height=0.55, color=col)
            ax.text(a + 5, yi, f"{a:.0f}", va="center", fontsize=14, color=INK)
        else:
            ax.barh(yi, a, height=0.55, color=col)
            ax.barh(yi, b - a, left=a, height=0.55, color=col, alpha=0.45)
            ax.text(b + 5, yi, f"{a:.0f}–{b:.0f}", va="center", fontsize=14, color=INK, fontweight="bold")
    ax.set_yticks(y, [r[0] for r in ROWS], fontsize=12.5)
    ax.set_xlabel("Tg CO₂ per year", fontsize=14, color=INK)
    ax.set_xlim(0, 360)
    ax.tick_params(axis="x", labelsize=13)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=1)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)


def text(slide, x, y, w, h, s, size, color="0B0B0B", bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    first = True
    for line in s.split("\n"):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size, r.font.bold, r.font.name = Pt(size), bold, "Calibri"
        r.font.color.rgb = RGBColor.from_string(color)
    return tb


def main():
    os.makedirs(OUT, exist_ok=True)
    png = os.path.join(OUT, "context_comparison_chart.png")
    chart(png)
    lo, hi = (v * C_PER_CO2 for v in (3.7, 5.3))
    yrs = (lo * 1000 / US_EMIS_2022, hi * 1000 / US_EMIS_2022)

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.6, 0.35, 12.2, 0.9, "Putting 3.7–5.3 PgC in context", 36, bold=True)
    s.shapes.add_picture(png, Inches(0.4), Inches(1.35), width=Inches(8.4))
    text(s, 9.1, 1.6, 3.9, 0.9, "≈ 2–3 years", 40, color="2A78D6", bold=True)
    text(s, 9.1, 2.45, 3.9, 1.2, f"of total U.S. greenhouse-gas emissions\n({lo:.1f}–{hi:.1f} Gt CO₂ by 2100)", 17, color="52514E")
    text(s, 9.1, 3.75, 3.9, 0.9, "≈ 3–4 % per year", 30, color="2A78D6", bold=True)
    text(s, 9.1, 4.45, 3.9, 1.3, "of annual U.S. emissions, every year until 2100;\ncomparable to the U.S.-wide reforestation potential",
         17, color="52514E")
    text(s, 0.6, 6.75, 12.2, 0.5,
         "Our numbers: cumulative NBP 2024–2100 averaged over 77 years (1 PgC = 3.664 Pg CO₂). Published values are maximum potentials "
         "or inventory estimates with different scopes: compare orders of magnitude only. "
         "Sources: EPA GHG Inventory 2024; Fargione et al. 2018, Sci. Adv.; Domke et al. 2020, PNAS; USDA Forest Service (Southern forests 2007–2012).",
         10.5, color="52514E")
    p = os.path.join(OUT, "context_comparison.pptx")
    prs.save(p)
    print(f"RF {lo:.1f}-{hi:.1f} Gt CO2 = {yrs[0]:.1f}-{yrs[1]:.1f} years of U.S. emissions; "
          f"rates RF {rate(3.7, 5.3, 'PgC')[0]:.0f}-{rate(3.7, 5.3, 'PgC')[1]:.0f}, RH {rate(1.0, 1.5, 'PgC')[0]:.0f}-{rate(1.0, 1.5, 'PgC')[1]:.0f} Tg CO2/yr")
    print("wrote", p)


if __name__ == "__main__":
    main()
