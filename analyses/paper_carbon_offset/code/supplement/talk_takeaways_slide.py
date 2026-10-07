"""
Talk slide (user request 2026-10-07): closing takeaways, one editable 16:9 PowerPoint slide (native text boxes and
shapes, Calibri) with four stat cards and a closing sentence. Numbers as quoted elsewhere in the talk:
  RF - Default cumulative NBP by 2100 3.7-5.3 PgC, RH - Default 1.0-1.5 PgC, Default - DF 10.7-11.8 PgC (Figure 2 bars);
  static-baseline over-credit 14-51 % (dynamic_baseline slide, stock basis); high benefit / low risk ~1/3 of forest
  land (33-37 %, SSP2-4.5 medians as fixed thresholds, notes 3.26); 0.5 deg finds 43 % of the 4 km top-10 % land
  (Figure 3, SSP3-7.0, RF); high benefit / high risk 1 % (SSP1-1.9) to 24 % (SSP5-8.5).

Runs locally (needs python-pptx), from the analysis root:
    uv run --no-project --with python-pptx python code/supplement/talk_takeaways_slide.py
Output: figures/slides/takeaways.pptx (render to PNG with LibreOffice for a picture version)
"""
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "figures/slides")
INK, INK2 = "0B0B0B", "52514E"
CARDS = [  # (accent colour, big number, headline, body)
    ("1C5CAB", "4 km", "High-resolution land modeling",
     "A portable surface-data workflow builds model-ready inputs for any region and grid."),
    ("2A78D6", "+3.7–5.3\u00a0PgC", "Carbon benefit by 2100",
     "Restoration and protection; reduced harvest adds about 1 PgC; protecting existing forests is worth up to ~11 PgC."),
    ("EB6834", "14–51\u00a0%", "Static baselines overstate the benefit",
     "The no-project world also changes with climate and land use, so baselines must be dynamic."),
    ("1BAF7A", "~1/3", "of forest land is high-benefit, low-risk",
     "A 0.5° model finds only 43\u00a0% of the best sites; warmer scenarios put more benefit on high-risk land."),
]
CLOSE = "High-resolution modeling turns a regional carbon number into a map of where to act, measured against a baseline that moves with climate."


def rgb(h):
    return RGBColor.from_string(h)


def text(slide, x, y, w, h, runs, size, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, name=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = runs
    r.font.size, r.font.bold, r.font.name = Pt(size), bold, "Calibri"
    r.font.color.rgb = rgb(color)
    return tb


def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    s = prs.slides.add_slide(prs.slide_layouts[6])                   # blank
    text(s, 0.6, 0.35, 12, 0.9, "Takeaways", 40, bold=True, name="Title")
    cw, ch, gap, x0, y0 = 2.85, 3.75, 0.25, 0.6, 1.45
    for k, (acc, num, head, body) in enumerate(CARDS):
        x = x0 + k * (cw + gap)
        card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y0), Inches(cw), Inches(ch))
        card.name = f"Card {k + 1}"
        card.adjustments[0] = 0.06
        card.fill.solid()
        card.fill.fore_color.rgb = rgb("F4F5F7")
        card.line.fill.background()
        card.shadow.inherit = False
        text(s, x + 0.2, y0 + 0.25, cw - 0.4, 0.9, num, 28, color=acc, bold=True, name=f"Stat {k + 1}")
        text(s, x + 0.2, y0 + 1.05, cw - 0.4, 0.9, head, 18, bold=True, name=f"Head {k + 1}")
        text(s, x + 0.2, y0 + 1.95, cw - 0.4, 1.7, body, 15, color=INK2, name=f"Body {k + 1}")
    text(s, 0.6, 5.55, 12.1, 1.1, CLOSE, 21, color=INK, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
         name="Closing")
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "takeaways.pptx")
    prs.save(p)
    print("wrote", p)


if __name__ == "__main__":
    main()
