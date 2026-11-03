import hashlib
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app import config

PRIMARY = colors.HexColor("#0f766e")
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")
LINE = colors.HexColor("#e2e8f0")
TONES = {
    "ok": ("#15803d", "#dcfce7", "#86efac"),
    "warn": ("#b45309", "#fef3c7", "#fcd34d"),
    "bad": ("#b91c1c", "#fee2e2", "#fca5a5"),
}
PAGE_W, MARGIN = A4[0], 18 * mm
FRAME_PAD = 6  # ReportLab frames pad 6pt on each side; content must fit inside that
CONTENT_W = PAGE_W - 2 * MARGIN - 2 * FRAME_PAD


def make_report_id(timestamp: datetime, values: Dict[str, float]) -> str:
    h = hashlib.sha1(f"{timestamp.isoformat()}{sorted(values.items())}".encode()).hexdigest()[:6].upper()
    return f"HAI-{timestamp:%Y%m%d}-{h}"


def _styles():
    base = dict(fontName="Helvetica", fontSize=9.5, leading=13, textColor=INK)
    return {
        "body": ParagraphStyle("body", **base),
        "small": ParagraphStyle("small", **{**base, "fontSize": 8, "leading": 11, "textColor": MUTED}),
        "h2": ParagraphStyle("h2", **{**base, "fontName": "Helvetica-Bold", "fontSize": 12,
                                       "textColor": PRIMARY, "spaceBefore": 9, "spaceAfter": 4}),
        "cell": ParagraphStyle("cell", **{**base, "fontSize": 9, "leading": 12}),
        "cellc": ParagraphStyle("cellc", **{**base, "fontSize": 9, "leading": 12, "alignment": TA_CENTER}),
        "thl": ParagraphStyle("thl", **{**base, "fontName": "Helvetica-Bold", "fontSize": 8.5,
                                        "textColor": colors.white, "alignment": TA_LEFT}),
        "th": ParagraphStyle("th", **{**base, "fontName": "Helvetica-Bold", "fontSize": 8.5,
                                       "textColor": colors.white, "alignment": TA_CENTER}),
        "label": ParagraphStyle("label", **{**base, "fontName": "Helvetica-Bold", "fontSize": 8,
                                             "textColor": MUTED}),
        "bullet": ParagraphStyle("bullet", **{**base, "leftIndent": 10, "bulletIndent": 0, "spaceAfter": 2}),
    }


def _prob_bar(p: float, tone: str) -> Drawing:
    w, d = CONTENT_W, Drawing(CONTENT_W, 28)
    d.add(Rect(0, 12, w, 8, fillColor=LINE, strokeColor=None, rx=4, ry=4))
    if p > 0:
        d.add(Rect(0, 12, max(w * p, 8), 8, fillColor=colors.HexColor(TONES[tone][0]),
                   strokeColor=None, rx=4, ry=4))
    d.add(Line(w * 0.5, 8, w * 0.5, 24, strokeColor=MUTED, strokeWidth=0.8))
    for x, txt, anchor in ((0, "0%", "start"), (w * 0.5, "50% decision threshold", "middle"), (w, "100%", "end")):
        d.add(String(x, 0, txt, fontName="Helvetica", fontSize=7, fillColor=MUTED, textAnchor=anchor))
    return d


def build_report_pdf(*, values: Dict[str, float], result, flags: List[dict], findings: List[str],
                     band: tuple, patient: Dict[str, str], model_summary: dict,
                     timestamp: datetime, report_id: str, feature_labels: List[str],
                     notice: Optional[Dict[str, str]] = None) -> bytes:
    st = _styles()
    tone = "bad" if result.is_positive else "ok"
    t_txt, t_bg, t_bd = TONES[tone]
    band_label, band_tone = band
    story = []

    title = Table([[Paragraph("<font color='#99f6e4' size='10'><b>HepatoAI</b></font><br/>"
                              "<font color='white' size='18'><b>Liver Function Screening Report</b></font><br/>"
                              "<font color='#ccfbf1' size='9'>AI-assisted analysis of 8 liver-panel biomarkers</font>",
                              ParagraphStyle("t", fontName="Helvetica", leading=22)),
                    Paragraph(f"<font color='white' size='8'>REPORT ID</font><br/>"
                              f"<font color='white' size='10'><b>{escape(report_id)}</b></font>",
                              ParagraphStyle("r", fontName="Helvetica", leading=13, alignment=TA_RIGHT))]],
                  colWidths=[CONTENT_W * 0.68, CONTENT_W * 0.32])
    title.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                               ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
    story += [title, Spacer(1, 10)]

    def v(key, fallback="Not provided"):
        val = (patient or {}).get(key)
        if key == "age" and val:
            return f"{int(val)} years"
        return escape(str(val)) if val not in (None, "", 0) else fallback

    L = lambda s: Paragraph(s.upper(), st["label"])
    meta = Table([
        [L("Patient name"), Paragraph(v("name"), st["cell"]), L("Generated"),
         Paragraph(f"{timestamp:%Y-%m-%d %H:%M} UTC", st["cell"])],
        [L("Patient ID"), Paragraph(v("patient_id"), st["cell"]), L("Model"),
         Paragraph(escape(str(model_summary.get("name", "-"))), st["cell"])],
        [L("Age"), Paragraph(v("age"), st["cell"]), L("Biomarkers"), Paragraph(str(len(values)), st["cell"])],
    ], colWidths=[26 * mm, CONTENT_W / 2 - 26 * mm, 26 * mm, CONTENT_W / 2 - 26 * mm])
    meta.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
                              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                              ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story.append(meta)

    story.append(Paragraph("Screening result", st["h2"]))
    box = Table([[Paragraph(f"<font color='{t_txt}' size='15'><b>{escape(result.label_text)}</b></font><br/>"
                            f"<font color='#475569' size='9'>Risk band: <b>{band_label}</b></font>",
                            ParagraphStyle("b1", fontName="Helvetica", leading=19)),
                  Paragraph(f"<font color='{t_txt}' size='22'><b>{result.probability_positive:.1%}</b></font><br/>"
                            f"<font color='#475569' size='8'>probability of liver disease</font>",
                            ParagraphStyle("b2", fontName="Helvetica", leading=24, alignment=TA_RIGHT))]],
                colWidths=[CONTENT_W * 0.62, CONTENT_W * 0.38])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(t_bg)),
                             ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(t_bd)),
                             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                             ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                             ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    story += [box, Spacer(1, 6), _prob_bar(result.probability_positive, tone)]

    story.append(Paragraph("Biomarker review", st["h2"]))
    rows = [[Paragraph(h, st["thl"] if i == 0 else st["th"])
             for i, h in enumerate(("Biomarker", "Result", "Unit", "Typical range", "Status"))]]
    style = [("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    for i, r in enumerate(flags, start=1):
        lo, hi = r["range"]
        color, bg = {"HIGH": ("#b91c1c", "#fef2f2"), "LOW": ("#b45309", "#fffbeb"),
                     "NORMAL": ("#15803d", None)}.get(r["status"], ("#64748b", None))
        rows.append([Paragraph(escape(r["marker"]), st["cell"]),
                     Paragraph(f"<b>{r['value']:g}</b>", st["cellc"]),
                     Paragraph(escape(r["unit"]), st["cellc"]),
                     Paragraph("-" if lo is None else f"{lo:g} - {hi:g}", st["cellc"]),
                     Paragraph(f"<font color='{color}'><b>{r['status'].title()}</b></font>", st["cellc"])])
        if bg:
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(bg)))
    tbl = Table(rows, colWidths=[CONTENT_W * f for f in (0.36, 0.15, 0.13, 0.20, 0.16)], repeatRows=1)
    tbl.setStyle(TableStyle(style))
    story.append(tbl)
    story.append(Paragraph("Typical adult reference ranges; exact ranges vary between laboratories.", st["small"]))

    story.append(Paragraph("Key findings", st["h2"]))
    for f in findings:
        story.append(Paragraph(escape(f), st["bullet"], bulletText="-"))
    if notice:
        warn = Table([[Paragraph(f"<font color='#b45309'><b>{escape(notice['title'])}.</b></font> "
                                 f"{escape(notice['text'])}", st["cell"])]], colWidths=[CONTENT_W])
        warn.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                                  ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#fcd34d")),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                                  ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
        story += [Spacer(1, 6), warn]

    closing = [Paragraph("About this analysis", st["h2"])]
    acc = model_summary.get("accuracy")
    acc_txt = f" (reported development accuracy {acc:.2%})" if acc else ""
    closing.append(Paragraph(
        f"Predictions are produced by a {escape(str(model_summary.get('name', 'machine-learning')))} classifier"
        f"{acc_txt} trained on: {escape(', '.join(feature_labels))}. Accuracy was measured on the development "
        "dataset and may not generalize to other populations; independent clinical validation is required "
        "before any clinical use.", st["body"]))

    closing.append(Spacer(1, 8))
    disc = Table([[Paragraph("<b>Disclaimer.</b> This report is for research and educational purposes only and is "
                             "not a medical diagnosis. It must not replace professional medical advice. Please consult "
                             "a qualified clinician to interpret these results.", st["small"])]],
                 colWidths=[CONTENT_W])
    disc.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                              ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                              ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                              ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    closing.append(disc)
    story.append(KeepTogether(closing))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(MARGIN + FRAME_PAD, 14 * mm, PAGE_W - MARGIN - FRAME_PAD, 14 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN + FRAME_PAD, 9.5 * mm, f"{config.APP_TITLE}  |  {report_id}  |  Research and educational use only")
        canvas.drawRightString(PAGE_W - MARGIN - FRAME_PAD, 9.5 * mm, f"Page {doc.page}")
        canvas.restoreState()

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=12 * mm,
                            bottomMargin=19 * mm, title="Liver Function Screening Report",
                            author=config.APP_TITLE)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
