import io
import json
import base64
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

C_ACCENT    = colors.HexColor("#1e40af")
C_HEADER_BG = colors.HexColor("#0f172a")
C_TEXT      = colors.HexColor("#1e293b")
C_NEUTRAL   = colors.HexColor("#64748b")
C_BORDER    = colors.HexColor("#cbd5e1")
C_SUCCESS   = colors.HexColor("#16a34a")
C_WARNING   = colors.HexColor("#d97706")
C_DANGER    = colors.HexColor("#dc2626")

PAGE_W, PAGE_H = A4
MARGIN = 1.2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "N/A"
    return f"{v * 100:.1f}%"


def _header_footer_summary(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(C_ACCENT)
    canvas.setLineWidth(1.5)
    canvas.line(MARGIN, PAGE_H - 1.0 * cm, PAGE_W - MARGIN, PAGE_H - 1.0 * cm)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(C_ACCENT)
    canvas.drawString(MARGIN, PAGE_H - 0.8 * cm, "TruthLens")
    case_id = getattr(doc, "_case_id", "")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_NEUTRAL)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 0.8 * cm, "Digital Media Analysis Case Summary")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.8 * cm, f"Case: {case_id}")

    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.0 * cm, PAGE_W - MARGIN, 1.0 * cm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_NEUTRAL)
    canvas.drawCentredString(PAGE_W / 2, 0.6 * cm, "Page 1 of 1 — TruthLens Executive Summary")
    canvas.restoreState()


def build_summary_pdf(case) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )
    doc._case_id = case.case_id

    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("stitle", parent=base["Normal"], fontSize=20, leading=24, textColor=C_ACCENT, fontName="Helvetica-Bold", alignment=TA_CENTER),
        "sub": ParagraphStyle("ssub", parent=base["Normal"], fontSize=10, leading=14, textColor=C_NEUTRAL, fontName="Helvetica", alignment=TA_CENTER),
        "hdr": ParagraphStyle("shdr", parent=base["Normal"], fontSize=10, leading=14, textColor=colors.white, fontName="Helvetica-Bold"),
        "lbl": ParagraphStyle("slbl", parent=base["Normal"], fontSize=8, leading=10, textColor=C_NEUTRAL, fontName="Helvetica-Bold"),
        "val": ParagraphStyle("sval", parent=base["Normal"], fontSize=8.5, leading=11, textColor=C_TEXT, fontName="Helvetica"),
        "verdict": ParagraphStyle("sverdict", parent=base["Normal"], fontSize=15, leading=18, fontName="Helvetica-Bold", alignment=TA_CENTER),
        "body": ParagraphStyle("sbody", parent=base["Normal"], fontSize=8.5, leading=12, textColor=C_TEXT, fontName="Helvetica"),
        "disclaimer": ParagraphStyle("sdisc", parent=base["Normal"], fontSize=7, leading=9.5, textColor=C_NEUTRAL, fontName="Helvetica-Oblique"),
    }

    ref_analysis = json.loads(case.reference_analysis_json) if case.reference_analysis_json else {}
    sus_analysis = json.loads(case.suspected_analysis_json) if case.suspected_analysis_json else {}
    face_verif = json.loads(case.face_verification_json) if case.face_verification_json else {}
    assessment = json.loads(case.assessment_json) if case.assessment_json else {}

    cat = assessment.get("category", "N/A").replace("_", " ").title()
    risk = assessment.get("risk_level", "N/A")
    conf = assessment.get("confidence", "N/A")
    expl = assessment.get("explanation", "TruthLens analyzed the submitted media using AI-based detection and supporting forensic analysis.")

    story = []
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("TruthLens", styles["title"]))
    story.append(Paragraph("Digital Media Analysis Case Summary", styles["sub"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_ACCENT, spaceAfter=8, spaceBefore=4))

    meta_data = [
        [Paragraph("Case ID", styles["lbl"]), Paragraph(case.case_id, styles["val"]), Paragraph("Date", styles["lbl"]), Paragraph(str(case.created_at or "N/A")[:10], styles["val"])],
        [Paragraph("Analysis Type", styles["lbl"]), Paragraph(str(case.reference_content_type or "image").split("/")[0].capitalize(), styles["val"]), Paragraph("Status", styles["lbl"]), Paragraph("Case File Ready", styles["val"])],
    ]
    meta_table = Table(meta_data, colWidths=[CONTENT_W * 0.2, CONTENT_W * 0.3, CONTENT_W * 0.2, CONTENT_W * 0.3])
    meta_table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, C_BORDER),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.3 * cm))

    # Executive Verdict
    rc = C_DANGER if "HIGH" in risk.upper() or "DEEPFAKE" in cat.upper() else (C_WARNING if "MEDIUM" in risk.upper() else C_SUCCESS)
    verdict_data = [
        [Paragraph(f'<font color="{rc.hexval()}"><b>ASSESSMENT: {cat.upper()}</b></font>', styles["verdict"])],
        [Paragraph(f"Risk Level: <b>{risk}</b>  |  Confidence: <b>{conf}</b>", ParagraphStyle("vc", parent=styles["sub"], textColor=C_TEXT, fontName="Helvetica-Bold"))]
    ]
    verdict_table = Table(verdict_data, colWidths=[CONTENT_W])
    verdict_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 1, rc),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(verdict_table)
    story.append(Spacer(1, 0.3 * cm))

    # Summary Analysis Table
    sus_score = sus_analysis.get("ai_probability", 0.0)
    ref_score = ref_analysis.get("ai_probability", 0.0)
    face_sim = face_verif.get("best_match_score")
    face_res = face_verif.get("result", "N/A").replace("_", " ").title()

    summary_rows = [
        [Paragraph("<b>Parameter</b>", styles["lbl"]), Paragraph("<b>Value / Result</b>", styles["lbl"])],
        [Paragraph("Suspected AI Score", styles["lbl"]), Paragraph(_fmt_pct(sus_score), styles["val"])],
        [Paragraph("Reference AI Score", styles["lbl"]), Paragraph(_fmt_pct(ref_score), styles["val"])],
        [Paragraph("Face Verification", styles["lbl"]), Paragraph(f"{face_res} (Similarity: {_fmt_pct(face_sim)})" if face_verif else "Not Applicable", styles["val"])],
        [Paragraph("Reference SHA-256", styles["lbl"]), Paragraph(str(case.reference_sha256 or "N/A")[:32] + "...", styles["val"])],
        [Paragraph("Suspected SHA-256", styles["lbl"]), Paragraph(str(case.suspected_sha256 or "N/A")[:32] + "...", styles["val"])],
    ]
    sum_table = Table(summary_rows, colWidths=[CONTENT_W * 0.35, CONTENT_W * 0.65])
    sum_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, C_BORDER),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 0.3 * cm))

    # Narrative Conclusion
    story.append(Paragraph("<b>Conclusion & Key Findings:</b>", styles["lbl"]))
    story.append(Spacer(1, 2))
    story.append(Paragraph(expl, styles["body"]))
    story.append(Spacer(1, 0.4 * cm))

    # Disclaimer
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4, spaceBefore=4))
    story.append(Paragraph(
        "TruthLens provides AI-assisted digital media analysis. Results may contain errors and should be independently reviewed. "
        "The generated case file is an analytical record and does not by itself establish the authenticity or origin of the media.",
        styles["disclaimer"]
    ))

    doc.build(story, onFirstPage=_header_footer_summary, onLaterPages=_header_footer_summary)
    return buf.getvalue()
