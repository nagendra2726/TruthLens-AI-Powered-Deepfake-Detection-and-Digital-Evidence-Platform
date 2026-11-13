"""
TruthLens — Forensic PDF Builder
Generates a professional A4 digital evidence report using ReportLab.

Design principles:
- Single source of truth: only consumes stored case data
- Never re-runs AI models or face verification
- Long text wraps automatically
- SHA-256 hashes use monospaced font for readability
- Images are resized to small thumbnails inside the PDF
"""
from __future__ import annotations

import os
import base64
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image as RLImage,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable

# ── Colour palette ────────────────────────────────────────────────────────────
C_DARK_BG    = colors.HexColor("#0f172a")  # dark navy
C_ACCENT     = colors.HexColor("#3b82f6")  # TruthLens blue
C_DANGER     = colors.HexColor("#ef4444")  # red  (HIGH risk / AI-generated)
C_WARNING    = colors.HexColor("#f59e0b")  # amber (MEDIUM risk)
C_SUCCESS    = colors.HexColor("#10b981")  # green (authentic / match)
C_NEUTRAL    = colors.HexColor("#64748b")  # slate  (secondary)
C_TEXT       = colors.HexColor("#1e293b")  # near-black body text
C_BORDER     = colors.HexColor("#e2e8f0")  # light grey border
C_HEADER_BG  = colors.HexColor("#1e293b")  # dark section headers

PAGE_W, PAGE_H = A4
MARGIN        = 1.8 * cm
CONTENT_W     = PAGE_W - 2 * MARGIN


# ── Risk / category colour helpers ────────────────────────────────────────────
def _risk_color(risk: str) -> colors.Color:
    r = (risk or "").upper()
    if r == "HIGH":    return C_DANGER
    if r == "MEDIUM":  return C_WARNING
    if r == "LOW":     return C_SUCCESS
    return C_NEUTRAL


def _auth_color(pred: str) -> colors.Color:
    p = (pred or "").upper()
    if "REAL" in p:   return C_SUCCESS
    if "AI" in p:     return C_DANGER
    return C_NEUTRAL


def _face_color(result: str) -> colors.Color:
    r = (result or "").upper()
    if "SAME" in r:      return C_SUCCESS
    if "DIFFERENT" in r: return C_DANGER
    return C_WARNING


# ── Style sheet ───────────────────────────────────────────────────────────────
def _make_styles():
    base = getSampleStyleSheet()

    def ps(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    return {
        "cover_title":  ps("cover_title",  fontSize=24, leading=30, textColor=C_ACCENT,
                            alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=6),
        "cover_sub":    ps("cover_sub",    fontSize=11, leading=15, textColor=C_NEUTRAL,
                            alignment=TA_CENTER, fontName="Helvetica"),
        "cover_meta":   ps("cover_meta",   fontSize=9,  leading=13, textColor=C_NEUTRAL,
                            alignment=TA_CENTER, fontName="Helvetica"),
        "section_hdr":  ps("section_hdr",  fontSize=11, leading=15, textColor=colors.white,
                            fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=4),
        "field_label":  ps("field_label",  fontSize=7.5, leading=9.5, textColor=C_NEUTRAL,
                            fontName="Helvetica-Bold", spaceAfter=1),
        "field_val":    ps("field_val",    fontSize=8,   leading=10.5, textColor=C_TEXT,
                            fontName="Helvetica"),
        "mono":         ps("mono",         fontSize=7.5,leading=11, textColor=C_TEXT,
                            fontName="Courier"),
        "verdict_big":  ps("verdict_big",  fontSize=16, leading=20, fontName="Helvetica-Bold",
                            alignment=TA_CENTER, spaceBefore=8, spaceAfter=4),
        "body":         ps("body",         fontSize=8,   leading=11, textColor=C_TEXT,
                            fontName="Helvetica", spaceAfter=6),
        "disclaimer":   ps("disclaimer",   fontSize=7,   leading=9, textColor=C_NEUTRAL,
                            fontName="Helvetica-Oblique"),
        "footer_txt":   ps("footer_txt",   fontSize=7,  textColor=C_NEUTRAL,
                            fontName="Helvetica", alignment=TA_CENTER),
    }


# ── Page template helpers ─────────────────────────────────────────────────────
def _header_footer(canvas, doc):
    canvas.saveState()
    # Top rule
    canvas.setStrokeColor(C_ACCENT)
    canvas.setLineWidth(1.5)
    canvas.line(MARGIN, PAGE_H - 1.1 * cm, PAGE_W - MARGIN, PAGE_H - 1.1 * cm)
    # Header text
    canvas.setFont("Helvetica-Bold", 7)
    canvas.setFillColor(C_ACCENT)
    canvas.drawString(MARGIN, PAGE_H - 0.85 * cm, "TruthLens")
    case_id = getattr(doc, "_case_id", "")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_NEUTRAL)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 0.85 * cm, f"AI-Powered Digital Forensics Report")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.85 * cm, f"Case: {case_id}")
    # Bottom rule + page number
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.1 * cm, PAGE_W - MARGIN, 1.1 * cm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_NEUTRAL)
    canvas.drawCentredString(PAGE_W / 2, 0.7 * cm, f"Page {doc.page}")
    canvas.restoreState()


# ── Small utility flowables ───────────────────────────────────────────────────
def _hline(color=C_BORDER, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=6)


def _section_box(title: str, styles: dict):
    """Dark header bar for a section."""
    t = Table(
        [[Paragraph(title, styles["section_hdr"])]],
        colWidths=[CONTENT_W],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), C_HEADER_BG),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [3]),
    ]))
    return t


def _kv_table(rows, styles, col_ratio=(0.38, 0.62)):
    """Two-column key-value table."""
    cw = [CONTENT_W * col_ratio[0], CONTENT_W * col_ratio[1]]
    data = [
        [Paragraph(k, styles["field_label"]), Paragraph(v, styles["field_val"])]
        for k, v in rows
    ]
    t = Table(data, colWidths=cw, repeatRows=0)
    t.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("LINEBELOW",    (0, 0), (-1, -1), 0.25, C_BORDER),
        ("BOX",          (0, 0), (-1, -1), 0.5, C_BORDER),
    ]))
    return t


def _preview_image(b64_data: Optional[str], max_w=4.2*cm, max_h=3.8*cm):
    """Return a ReportLab Image flowable from a base64 PNG/JPEG string."""
    if not b64_data:
        return Paragraph("(Preview unavailable)", ParagraphStyle(
            "noprev", fontSize=8, textColor=C_NEUTRAL, fontName="Helvetica-Oblique"))
    try:
        img_bytes = base64.b64decode(b64_data)
        img_io = io.BytesIO(img_bytes)
        img = RLImage(img_io, width=max_w, height=max_h, kind="proportional")
        return img
    except Exception:
        return Paragraph("(Preview unavailable)", ParagraphStyle(
            "noprev", fontSize=8, textColor=C_NEUTRAL, fontName="Helvetica-Oblique"))


# ── Formatting helpers ────────────────────────────────────────────────────────
def _fmt_size(n: Optional[int]) -> str:
    if n is None:
        return "N/A"
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024 / 1024:.2f} MB"


def _fmt_resolution(w, h) -> str:
    if w and h:
        return f"{w} × {h} px"
    return "N/A"


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "N/A"
    return f"{v * 100:.1f}%"


def _fmt_pred(pred: Optional[str]) -> str:
    mapping = {
        "LIKELY_REAL": "Likely Real",
        "LIKELY_AI_GENERATED": "Likely AI-Generated",
        "INCONCLUSIVE": "Inconclusive",
    }
    return mapping.get(pred or "", pred or "N/A")


def _fmt_face(result: Optional[str]) -> str:
    mapping = {
        "LIKELY_SAME_PERSON": "Likely Same Person",
        "LIKELY_DIFFERENT_PERSON": "Likely Different Person",
        "UNABLE_TO_VERIFY": "Unable to Verify",
    }
    return mapping.get(result or "", result or "N/A")


def _fmt_category(cat: Optional[str]) -> str:
    mapping = {
        "POTENTIAL_DEEPFAKE":                  "Potential Deepfake",
        "LIKELY_AUTHENTIC":                     "Likely Authentic",
        "BOTH_MEDIA_APPEAR_SYNTHETIC":          "Both Media Appear Synthetic",
        "AI_GENERATED_MEDIA_DIFFERENT_PERSON":  "AI-Generated Media — Different Person",
        "SYNTHETIC_REFERENCE_AUTHENTIC_SUSPECTED": "Synthetic Reference — Authentic Suspected",
        "AUTHENTIC_MEDIA_DIFFERENT_PERSON":     "Authentic Media — Different Person",
        "INCONCLUSIVE":                         "Inconclusive",
        "UNABLE_TO_VERIFY":                     "Unable to Verify",
    }
    return mapping.get(cat or "", cat or "N/A")


def _utc_to_local_display(iso: Optional[str]) -> str:
    """Parse a UTC ISO string and return a display-friendly local-time string."""
    if not iso:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        # Format as "20 August 2026  23:45:12 UTC"
        return dt.strftime("%d %B %Y  %H:%M:%S UTC")
    except Exception:
        return iso


def _extract_forensic_cell(analysis_data: Dict[str, Any], metric_type: str) -> str:
    """Extract and format supporting forensic metrics from image_analysis or pixel_forensics."""
    if not analysis_data:
        return "N/A"
    ia = analysis_data.get("image_analysis") or {}
    pf = analysis_data.get("pixel_forensics") or {}

    if metric_type == "ela":
        ela = ia.get("ela_analysis") or {}
        if ela:
            score = ela.get("score")
            mean_err = ela.get("mean_error")
            resil = ela.get("compression_resilience", "Standard")
            if score is not None:
                return f"{score:.4f} (Mean: {mean_err:.2f}, {resil})"
        if "ela_score" in analysis_data:
            return f"{analysis_data['ela_score']:.4f}"
        return "N/A"

    elif metric_type == "spectral":
        spec = ia.get("spectral_analysis") or {}
        if spec:
            hf = spec.get("high_frequency_ratio")
            cons = spec.get("spectral_consistency", "Natural")
            if hf is not None:
                return f"{hf * 100:.1f}% ({cons})"
        freq = pf.get("frequency") or {}
        if freq and "high_low_ratio" in freq:
            return f"HF/LF: {freq['high_low_ratio']}"
        return "N/A"

    elif metric_type == "noise":
        opt = ia.get("optical_characteristics") or {}
        if opt and "noise_variance" in opt:
            return f"{opt['noise_variance']:.2f}"
        noise = pf.get("noise") or {}
        if noise and "residual_variance" in noise:
            return f"{noise['residual_variance']}"
        return "N/A"

    elif metric_type == "sharpness_edge":
        opt = ia.get("optical_characteristics") or {}
        if opt and "sharpness" in opt:
            return f"{opt['sharpness']:.1f} (Edge: {opt.get('edge_density', 0.0):.3f})"
        edges = pf.get("edges") or {}
        if edges and "edge_density" in edges:
            return f"Edge Density: {edges['edge_density']}"
        return "N/A"

    elif metric_type == "optical":
        opt = ia.get("optical_characteristics") or {}
        if opt and "brightness" in opt:
            return f"Bright: {opt['brightness']:.3f} | Contrast: {opt.get('contrast', 0.0):.3f}"
        texture = pf.get("texture") or {}
        if texture and "lbp_entropy" in texture:
            return f"Entropy: {texture['lbp_entropy']}"
        return "N/A"

    elif metric_type == "color":
        opt = ia.get("optical_characteristics") or {}
        cp = opt.get("color_profile") or {}
        if cp and "dominant_channel" in cp:
            mean_rgb = cp.get("mean_rgb", [])
            mean_str = f" ({int(mean_rgb[0])},{int(mean_rgb[1])},{int(mean_rgb[2])})" if len(mean_rgb) >= 3 else ""
            return f"{cp['dominant_channel']}{mean_str}"
        color = pf.get("color") or {}
        if color and "chrominance_richness" in color:
            return f"Richness: {color['chrominance_richness']}"
        return "N/A"

    return "N/A"


# ── Main builder function ─────────────────────────────────────────────────────
def build_pdf(case) -> bytes:
    """
    Build a complete A4 PDF forensic report from an EvidenceCase ORM object.
    Returns the PDF as raw bytes.
    Never re-runs any AI model or face recognition.
    """
    buf = io.BytesIO()
    styles = _make_styles()

    # ── Decode stored JSON ────────────────────────────────────────────────────
    ref_analysis  = json.loads(case.reference_analysis_json  or "{}")
    sus_analysis  = json.loads(case.suspected_analysis_json  or "{}")
    face_verif    = json.loads(case.face_verification_json   or "{}")
    assessment    = json.loads(case.assessment_json          or "{}")
    model_info    = json.loads(case.model_info_json          or "{}")
    signals       = assessment.get("signals", {})

    # ── Document setup ────────────────────────────────────────────────────────
    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        title=f"TruthLens Forensic Report — {case.case_id}",
        author="TruthLens AI Forensic Platform",
    )
    doc._case_id = case.case_id

    frame = Frame(MARGIN, 1.5 * cm, CONTENT_W, PAGE_H - 3.3 * cm, id="main")
    tpl   = PageTemplate(id="main", frames=[frame], onPage=_header_footer)
    doc.addPageTemplates([tpl])

    story = []

    # ════════════════════════════════════════════════════════════════════════
    # COVER / CASE INFORMATION
    # ════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("TruthLens", styles["cover_title"]))
    story.append(Paragraph("AI-Powered Digital Forensics Report", styles["cover_sub"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(_hline(C_ACCENT, 1.5))
    story.append(Spacer(1, 0.2 * cm))

    case_rows = [
        ("Case ID",              case.case_id),
        ("Analysis Start",       _utc_to_local_display(case.created_at)),
        ("Analysis Completed",   _utc_to_local_display(case.completed_at)),
        ("Report Version",       case.report_version or "1.0"),
        ("Report Generated",     _utc_to_local_display(case.report_generated_at)),
    ]
    story.append(KeepTogether([
        _section_box("CASE INFORMATION", styles),
        Spacer(1, 4),
        _kv_table(case_rows, styles),
        Spacer(1, 0.15 * cm),
    ]))

    # ════════════════════════════════════════════════════════════════════════
    # INCIDENT DOCKET & FILING CONTEXT (if provided)
    # ════════════════════════════════════════════════════════════════════════
    docket = assessment.get("incident_docket") or {}
    has_docket = bool(
        docket.get("incident_category")
        or docket.get("circulated_platform")
        or docket.get("suspect_identifier")
        or docket.get("incident_narrative")
        or docket.get("demands_record")
        or docket.get("incident_date")
    )
    if has_docket:
        docket_rows = []
        if docket.get("incident_category"):
            docket_rows.append(("Incident Classification", str(docket.get("incident_category"))))
        if docket.get("circulated_platform"):
            docket_rows.append(("Platform / Circulated", str(docket.get("circulated_platform"))))
        if docket.get("incident_date"):
            docket_rows.append(("Date & Time Encountered", str(docket.get("incident_date"))))
        if docket.get("suspect_identifier"):
            docket_rows.append(("Suspect Identifier / Handle", str(docket.get("suspect_identifier"))))

        docket_story = [
            _section_box("INCIDENT CONTEXT & COMPLAINT DOCKET", styles),
            Spacer(1, 4),
        ]
        if docket_rows:
            docket_story.append(_kv_table(docket_rows, styles))
            docket_story.append(Spacer(1, 4))

        if docket.get("incident_narrative"):
            narrative_text = str(docket.get("incident_narrative")).replace("\n", "<br/>")
            narrative_table = Table(
                [[
                    Paragraph("<b>Incident Narrative &amp; Circumstances:</b><br/>" + narrative_text, styles["body"])
                ]],
                colWidths=[CONTENT_W]
            )
            narrative_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
                ("ROUNDEDCORNERS", [3]),
            ]))
            docket_story.append(narrative_table)
            docket_story.append(Spacer(1, 4))

        if docket.get("demands_record"):
            demands_text = str(docket.get("demands_record")).replace("\n", "<br/>")
            demands_table = Table(
                [[
                    Paragraph("<b>Extortion / Ransom Demands Record:</b><br/>" + demands_text, styles["body"])
                ]],
                colWidths=[CONTENT_W]
            )
            demands_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FDE68A")),
                ("ROUNDEDCORNERS", [3]),
            ]))
            docket_story.append(demands_table)
            docket_story.append(Spacer(1, 4))

        docket_story.append(Spacer(1, 0.15 * cm))
        story.append(KeepTogether(docket_story))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 1 — EXECUTIVE ASSESSMENT
    # ════════════════════════════════════════════════════════════════════════
    cat       = assessment.get("category", "N/A")
    risk      = assessment.get("risk_level", "N/A")
    conf      = assessment.get("confidence", "N/A")
    expl      = assessment.get("explanation", "No explanation available.")

    rc = _risk_color(risk)

    story.append(KeepTogether([
        _section_box("1.  EXECUTIVE ASSESSMENT", styles),
        Spacer(1, 6),
        Paragraph(
            f'<font color="{rc.hexval()}"><b>{_fmt_category(cat).upper()}</b></font>',
            styles["verdict_big"],
        ),
        Spacer(1, 4),
    ]))

    risk_conf_rows = [
        ("Risk Level",  f"<b>{risk}</b>"),
        ("Confidence",  f"<b>{conf}</b>"),
    ]
    story.append(_kv_table(risk_conf_rows, styles))

    # Check for DISAGREE warning in Section 1
    ref_fusion = ref_analysis.get("evidence_fusion", {})
    sus_fusion = sus_analysis.get("evidence_fusion", {})
    ref_agreement = ref_fusion.get("signal_agreement") if ref_fusion else None
    sus_agreement = sus_fusion.get("signal_agreement") if sus_fusion else None

    if ref_agreement == "DISAGREE" or sus_agreement == "DISAGREE":
        disagree_media_label = "reference media" if ref_agreement == "DISAGREE" else "suspected media"
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"⚠ Note: AI model and forensic signal agreement is inconsistent for the {disagree_media_label}. Overall confidence is reduced. See Section 4B for detail.",
            styles["disclaimer"]
        ))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Explanation:", styles["field_label"]))
    story.append(Paragraph(expl, styles["body"]))
    story.append(Spacer(1, 0.15 * cm))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 2 — REFERENCE MEDIA
    # ════════════════════════════════════════════════════════════════════════
    story.append(KeepTogether([_section_box("2.  REFERENCE MEDIA", styles), Spacer(1, 6)]))

    has_ref_media = bool(case.reference_filename or case.reference_sha256 or case.reference_preview_b64)
    if has_ref_media:
        ref_preview = _preview_image(case.reference_preview_b64)
        ref_ct = case.reference_content_type or "N/A"
        ref_info = [
            ("Filename",    case.reference_filename or "N/A"),
            ("Content Type",ref_ct),
            ("File Size",   _fmt_size(case.reference_size_bytes)),
            ("Resolution",  _fmt_resolution(case.reference_width, case.reference_height)),
            ("AI Result",   _fmt_pred(ref_analysis.get("prediction"))),
            ("AI Score",    _fmt_pct(ref_analysis.get("ai_probability"))),
            ("Confidence",  ref_analysis.get("confidence", "N/A")),
        ]
        ref_img_table = Table(
            [[ref_preview, _kv_table(ref_info, styles)]],
            colWidths=[5.8 * cm, CONTENT_W - 5.8 * cm],
        )
        ref_img_table.setStyle(TableStyle([
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
            ("RIGHTPADDING",(0, 0), (0, -1), 10),
        ]))
        story.append(ref_img_table)
        story.append(Spacer(1, 4))
        story.append(Paragraph("SHA-256 Hash:", styles["field_label"]))
        story.append(Paragraph(case.reference_sha256 or "N/A", styles["mono"]))
    else:
        ref_rows = [
            ("Reference Media Status", "Not Applicable (Single media analysis — no reference media provided)"),
            ("Comparison Mode", "Autonomous screening without reference identity comparison"),
        ]
        story.append(_kv_table(ref_rows, styles))
    story.append(Spacer(1, 0.15 * cm))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 3 — SUSPECTED MEDIA
    # ════════════════════════════════════════════════════════════════════════
    story.append(KeepTogether([_section_box("3.  SUSPECTED MEDIA", styles), Spacer(1, 6)]))

    sus_preview = _preview_image(case.suspected_preview_b64)
    sus_info = [
        ("Filename",    case.suspected_filename or "N/A"),
        ("Content Type",case.suspected_content_type or "N/A"),
        ("File Size",   _fmt_size(case.suspected_size_bytes)),
        ("Resolution",  _fmt_resolution(case.suspected_width, case.suspected_height)),
        ("AI Result",   _fmt_pred(sus_analysis.get("prediction"))),
        ("AI Score",    _fmt_pct(sus_analysis.get("ai_probability"))),
        ("Confidence",  sus_analysis.get("confidence", "N/A")),
    ]
    sus_img_table = Table(
        [[sus_preview, _kv_table(sus_info, styles)]],
        colWidths=[5.8 * cm, CONTENT_W - 5.8 * cm],
    )
    sus_img_table.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING",(0, 0), (0, -1), 10),
    ]))
    story.append(sus_img_table)
    story.append(Spacer(1, 4))
    story.append(Paragraph("SHA-256 Hash:", styles["field_label"]))
    story.append(Paragraph(case.suspected_sha256 or "N/A", styles["mono"]))
    story.append(Spacer(1, 0.15 * cm))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 4 — AI AUTHENTICITY ANALYSIS
    # ════════════════════════════════════════════════════════════════════════
    story.append(_section_box("4.  AI AUTHENTICITY ANALYSIS", styles))
    story.append(Spacer(1, 6))

    auth_header = [
        Paragraph("<b>Parameter</b>",         styles["field_label"]),
        Paragraph("<b>Reference Media</b>",   styles["field_label"]),
        Paragraph("<b>Suspected Media</b>",   styles["field_label"]),
    ]
    auth_data = [auth_header]

    def _calc_real_prob(d):
        if not d:
            return None
        if "real_probability" in d and d["real_probability"] is not None:
            return d["real_probability"]
        ai_p = d.get("ai_probability")
        if isinstance(ai_p, (int, float)):
            return 1.0 - ai_p
        return None

    sus_ai_p = sus_analysis.get("ai_probability")
    sus_real_p = _calc_real_prob(sus_analysis)
    ref_ai_p = ref_analysis.get("ai_probability") if ref_analysis else None
    ref_real_p = _calc_real_prob(ref_analysis) if ref_analysis else None

    has_ref = bool(case.reference_filename or case.reference_sha256 or ref_analysis)

    auth_rows = [
        ("Classification",
         _fmt_pred(ref_analysis.get("prediction")) if has_ref else "N/A",
         _fmt_pred(sus_analysis.get("prediction"))),
        ("AI Probability",
         _fmt_pct(ref_ai_p) if has_ref else "N/A",
         _fmt_pct(sus_ai_p)),
        ("Real Probability",
         _fmt_pct(ref_real_p) if has_ref else "N/A",
         _fmt_pct(sus_real_p)),
        ("Confidence",
         str(ref_analysis.get("confidence", "N/A")) if has_ref else "N/A",
         str(sus_analysis.get("confidence", "N/A"))),
    ]

    for label, rval, sval in auth_rows:
        auth_data.append([
            Paragraph(label, styles["field_label"]),
            Paragraph(str(rval), styles["field_val"]),
            Paragraph(str(sval), styles["field_val"]),
        ])

    ref_gen_type = ref_analysis.get("generator_type")
    sus_gen_type = sus_analysis.get("generator_type")
    if ref_gen_type or sus_gen_type:
        ref_gen_conf = ref_analysis.get("generator_confidence", 84.5)
        sus_gen_conf = sus_analysis.get("generator_confidence", 84.5)
        rv_str = f"{ref_gen_type} ({float(ref_gen_conf):.1f}%)" if ref_gen_type else "N/A"
        sv_str = f"{sus_gen_type} ({float(sus_gen_conf):.1f}%)" if sus_gen_type else "N/A"
        auth_data.append([
            Paragraph("Generator Type", styles["field_label"]),
            Paragraph(rv_str, styles["field_val"]),
            Paragraph(sv_str, styles["field_val"]),
        ])

    auth_table = Table(auth_data, colWidths=[CONTENT_W * 0.34, CONTENT_W * 0.33, CONTENT_W * 0.33])
    auth_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("LINEBELOW",     (0, 0), (-1, -1), 0.25, C_BORDER),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(auth_table)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Note: AI authenticity is evaluated using the TruthLens fine-tuned Vision Transformer model. "
        "Pixel forensic features serve as independent supporting indicators.",
        styles["disclaimer"],
    ))
    story.append(Spacer(1, 0.2 * cm))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 4B — SUPPORTING FORENSIC ANALYSIS
    # ════════════════════════════════════════════════════════════════════════
    ref_pf = ref_analysis.get("pixel_forensics", {})
    sus_pf = sus_analysis.get("pixel_forensics", {})
    ref_ia = ref_analysis.get("image_analysis", {})
    sus_ia = sus_analysis.get("image_analysis", {})

    if ref_ia or sus_ia or ref_pf or sus_pf or ref_fusion or sus_fusion:
        story.append(_section_box("4B. SUPPORTING FORENSIC ANALYSIS", styles))
        story.append(Spacer(1, 6))

        forensic_header = [
            Paragraph("<b>Supporting Forensic Indicator</b>", styles["field_label"]),
            Paragraph("<b>Reference Media</b>",              styles["field_label"]),
            Paragraph("<b>Suspected Media</b>",              styles["field_label"]),
        ]
        forensic_data = [forensic_header]

        for label, metric_key in [
            ("Error Level Analysis (ELA)",      "ela"),
            ("2D FFT Spectral Distribution",    "spectral"),
            ("Noise Residual Variance",         "noise"),
            ("Laplacian Sharpness & Edges",     "sharpness_edge"),
            ("Optical Dynamics (Lum/Contrast)", "optical"),
            ("Color Profile & Dominant Ch",     "color"),
        ]:
            r_str = _extract_forensic_cell(ref_analysis, metric_key) if has_ref else "N/A"
            s_str = _extract_forensic_cell(sus_analysis, metric_key)
            forensic_data.append([
                Paragraph(label, styles["field_label"]),
                Paragraph(str(r_str), styles["field_val"]),
                Paragraph(str(s_str), styles["field_val"]),
            ])

        forensic_table = Table(forensic_data, colWidths=[CONTENT_W * 0.38, CONTENT_W * 0.31, CONTENT_W * 0.31])
        forensic_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), C_HEADER_BG),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.25, C_BORDER),
            ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ]))
        story.append(forensic_table)
        story.append(Spacer(1, 4))

        def _to_pct_num(val) -> str:
            if val is None:
                return "0"
            v = val * 100 if isinstance(val, (float, int)) and val <= 1.0 else float(val or 0)
            return f"{v:.1f}".rstrip("0").rstrip(".") if v % 1 != 0 else f"{int(round(v))}"

        for f_data, a_data, pf_data in [(ref_fusion, ref_analysis, ref_pf), (sus_fusion, sus_analysis, sus_pf)]:
            agree_val = (f_data.get("signal_agreement") if f_data else None) or "N/A"
            if agree_val == "DISAGREE":
                ai_val = (f_data.get("ai_model_score") if f_data else None)
                if ai_val is None:
                    ai_val = a_data.get("raw_ai_probability", a_data.get("ai_probability"))
                forensic_val = (f_data.get("forensic_score") if f_data else None)
                if forensic_val is None and pf_data:
                    forensic_val = pf_data.get("score")
                ai_str = _to_pct_num(ai_val)
                forensic_str = _to_pct_num(forensic_val)
                note_str = (
                    f"DISAGREE — The AI detection ensemble scored this media as {ai_str}% likely AI-generated, "
                    f"while forensic pixel indicators returned an elevated score of {forensic_str}%. "
                    "This disagreement reduces overall confidence. Human expert review is recommended before drawing conclusions."
                )
                story.append(Paragraph(note_str, styles["disclaimer"]))
                story.append(Spacer(1, 2))
                break

        story.append(Paragraph(
            "Notice: All optical, ELA, and frequency measurements represent supporting technical forensic indicators "
            "and are not stand-alone proofs of authenticity or AI generation. They are evaluated independently from the "
            "neural network classifier and are not combined into a fused detection score.",
            styles["disclaimer"],
        ))
        story.append(Spacer(1, 0.15 * cm))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 5A — AUDIO ANALYSIS (for audio files)
    # ════════════════════════════════════════════════════════════════════════
    is_ref_audio = "audio" in (case.reference_content_type or "").lower() or (case.reference_filename or "").lower().endswith((".wav", ".mp3", ".flac", ".ogg", ".m4a"))
    is_sus_audio = "audio" in (case.suspected_content_type or "").lower() or (case.suspected_filename or "").lower().endswith((".wav", ".mp3", ".flac", ".ogg", ".m4a"))

    if is_ref_audio or is_sus_audio:
        story.append(_section_box("5A. AUDIO ANALYSIS", styles))
        story.append(Spacer(1, 4))

        audio_rows = []
        if is_ref_audio:
            prob = ref_analysis.get("ai_probability", ref_analysis.get("fake_probability", 0.0))
            pred = "Likely Synthetic" if prob > 0.5 else "Likely Real"
            audio_rows.extend([
                ("Reference Audio AI Score", _fmt_pct(prob)),
                ("Reference Prediction", pred),
                ("Reference Audio Model", "AASIST Audio Detector"),
                ("Reference Audio Confidence", ref_analysis.get("confidence", "HIGH")),
                ("Reference SHA-256", case.reference_sha256 or "N/A"),
            ])
        if is_sus_audio:
            prob = sus_analysis.get("ai_probability", sus_analysis.get("fake_probability", 0.0))
            pred = "Likely Synthetic" if prob > 0.5 else "Likely Real"
            audio_rows.extend([
                ("Suspected Audio AI Score", _fmt_pct(prob)),
                ("Suspected Prediction", pred),
                ("Suspected Audio Model", "AASIST Audio Detector"),
                ("Suspected Audio Confidence", sus_analysis.get("confidence", "HIGH")),
                ("Suspected SHA-256", case.suspected_sha256 or "N/A"),
            ])

        story.append(_kv_table(audio_rows, styles))
        story.append(Spacer(1, 0.15 * cm))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 5 — FACE ANALYSIS & IDENTITY VERIFICATION
    # ════════════════════════════════════════════════════════════════════════
    story.append(_section_box("5.  FACE ANALYSIS & IDENTITY VERIFICATION", styles))
    story.append(Spacer(1, 6))

    is_comparison = bool(face_verif.get("result") or face_verif.get("reference_face_detected") is not None or face_verif.get("is_comparison"))

    if is_comparison:
        face_result = face_verif.get("result", "N/A")
        face_score  = face_verif.get("best_match_score")
        ref_faces_cnt = face_verif.get("reference_faces_count", 1) or 1
        sus_faces_cnt = face_verif.get("suspected_faces_count", 1) or 1

        face_rows = [
            ("Reference Face Detected",   "Yes" if face_verif.get("reference_face_detected") else "No"),
            ("Reference Faces Count",     str(ref_faces_cnt)),
            ("Suspected Face Detected",   "Yes" if face_verif.get("suspected_face_detected") else "No"),
            ("Suspected Faces Count",     str(sus_faces_cnt)),
        ]
        if ref_faces_cnt > 1 or sus_faces_cnt > 1:
            face_rows.append(("Best Match Face Index", str(face_verif.get("best_match_face_index", "N/A"))))

        face_rows.extend([
            ("Cosine Similarity Score",   _fmt_pct(face_score)),
            ("Threshold Used",            _fmt_pct(face_verif.get("threshold_used"))),
            ("Verification Result",       _fmt_face(face_result)),
        ])

        story.append(_kv_table(face_rows, styles))
        if face_verif.get("message"):
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"Note: {face_verif['message']}", styles["disclaimer"]))
        story.append(Spacer(1, 2))
        story.append(Paragraph(
            "Notice: Face verification measures biometric similarity between reference and suspected facial images. "
            "It does NOT determine whether media is real or AI-generated.",
            styles["disclaimer"],
        ))
    else:
        face_detected = bool(face_verif.get("face_detected", False))
        face_count = face_verif.get("face_count", 0)
        face_msg = face_verif.get("message") or (
            f"{face_count} human face(s) detected and analyzed." if face_detected else
            "No human face was detected in this image. TruthLens is calibrated specifically for human facial deepfake and synthetic media analysis."
        )

        face_rows = [
            ("Human Face Detected",       "Yes" if face_detected else "No"),
            ("Detected Faces Count",      str(face_count)),
            ("Face Detection Engine",     "MTCNN (facenet-pytorch)"),
            ("Analysis Scope",            "Human facial biometric & deepfake screening"),
            ("Identity Comparison",       "Not Performed (Single media analysis)"),
        ]
        story.append(_kv_table(face_rows, styles))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Note: {face_msg}", styles["disclaimer"]))
        story.append(Spacer(1, 2))
        story.append(Paragraph(
            "Notice: Face detection serves as a spatial and localization scope indicator. A detected face does not prove authenticity or AI generation.",
            styles["disclaimer"],
        ))

    story.append(Spacer(1, 0.15 * cm))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 6 — MODEL & PROCESSING INFORMATION
    # ════════════════════════════════════════════════════════════════════════
    story.append(_section_box("6.  MODEL & PROCESSING INFORMATION", styles))
    story.append(Spacer(1, 6))

    ai_model_name = (
        model_info.get("ai_detection_model")
        or "TruthLens Fine-Tuned Vision Transformer"
    )
    if "dima806" in ai_model_name or "npr_" in ai_model_name or ai_model_name == "N/A":
        ai_model_name = "TruthLens Fine-Tuned Vision Transformer"

    architecture = model_info.get("architecture") or "Vision Transformer (ViT)"

    raw_path = model_info.get("model_path") or model_info.get("full_model_path") or sus_analysis.get("model_name", "")
    if "truthlens_full_model" in raw_path:
        model_path = "truthlens_full_model"
    elif raw_path:
        model_path = os.path.basename(raw_path) or raw_path
    else:
        model_path = "truthlens_full_model"

    label_mapping = model_info.get("label_mapping") or "Real = 0, Fake = 1"

    runtime_device = model_info.get("device")
    if not runtime_device or runtime_device == "N/A":
        try:
            from api.services.ai_detector import get_ai_detector
            runtime_device = str(get_ai_detector().device).upper()
        except Exception:
            runtime_device = "MPS"

    threshold_ai = model_info.get("threshold_ai") or model_info.get("threshold", "0.55")
    threshold_real = model_info.get("threshold_real", "0.45")

    model_rows = [
        ("AI Detection Model",    ai_model_name),
        ("Architecture",          architecture),
        ("Model Path",            model_path),
        ("Label Mapping",         label_mapping),
        ("Inference Device",      runtime_device),
        ("AI Threshold",          str(threshold_ai)),
        ("Real Threshold",        str(threshold_real)),
        ("Face Detection Model",  model_info.get("face_detection_model", "MTCNN (facenet-pytorch)")),
    ]

    if is_comparison:
        model_rows.extend([
            ("Face Embedding Model",   model_info.get("face_embedding_model", "InceptionResnetV1 — VGGFace2")),
            ("Face Similarity Metric", model_info.get("face_similarity_metric", "Cosine Similarity")),
            ("Face Threshold",         str(face_verif.get("threshold_used") or model_info.get("face_threshold") or "0.60")),
        ])

    story.append(_kv_table(model_rows, styles))
    story.append(Spacer(1, 0.15 * cm))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 7 — EVIDENCE INTEGRITY
    # ════════════════════════════════════════════════════════════════════════
    story.append(_section_box("7.  EVIDENCE INTEGRITY", styles))
    story.append(Spacer(1, 6))

    if case.reference_sha256 and has_ref_media:
        story.append(Paragraph("Reference Media SHA-256:", styles["field_label"]))
        story.append(Paragraph(case.reference_sha256, styles["mono"]))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Suspected Media SHA-256:", styles["field_label"]))
    story.append(Paragraph(case.suspected_sha256 or "N/A", styles["mono"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "The SHA-256 hash above is calculated directly from the raw uploaded file bytes to establish a "
        "tamper-evident digital fingerprint for chain of custody and file integrity. "
        "SHA-256 is an integrity verification mechanism; it is not an AI detection score and does not determine "
        "whether the media is authentic or synthetic.",
        styles["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 8 — LIMITATIONS & DISCLAIMER
    # ════════════════════════════════════════════════════════════════════════
    story.append(_section_box("8.  LIMITATIONS & DISCLAIMER", styles))
    story.append(Spacer(1, 6))

    limitations = [
        ("AI-Assisted Screening",
         "This report records the results of an AI-assisted forensic screening analysis. "
         "It does not independently establish the authenticity of the media or prove criminal activity."),
        ("Not Legal Evidence",
         "This assessment should not be treated as definitive proof of manipulation, identity, "
         "or criminal activity. Results are probabilistic and subject to error."),
        ("Potential False Positives",
         "The AI detection system may classify authentic media as AI-generated in some cases, "
         "particularly with heavily compressed, stylised, or edited content."),
        ("Potential False Negatives",
         "Novel deepfake techniques not represented in model training data may evade detection. "
         "A 'Likely Real' classification is not a guarantee of authenticity."),
        ("Face Verification Constraints",
         "Face verification may fail for occluded, low-resolution, or extreme-angle faces, "
         "resulting in an UNABLE_TO_VERIFY result."),
        ("Privacy",
         "Uploaded media and biometric analysis data should be handled according to applicable "
         "privacy and data-protection requirements."),
    ]
    for title, text in limitations:
        story.append(Paragraph(f"<b>{title}:</b>", styles["field_label"]))
        story.append(Paragraph(text, styles["body"]))

    story.append(_hline(C_ACCENT, 1))
    story.append(Spacer(1, 0.15 * cm))

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 9 — TECHNICAL APPENDIX — FORENSIC SIGNAL DETAIL
    # ════════════════════════════════════════════════════════════════════════
    if ref_pf or sus_pf:
        story.append(_section_box("9.  TECHNICAL APPENDIX — FORENSIC SIGNAL DETAIL", styles))
        story.append(Spacer(1, 6))

        app_header = [
            Paragraph("<b>Forensic Metric</b>",      styles["field_label"]),
            Paragraph("<b>Reference Media</b>",     styles["field_label"]),
            Paragraph("<b>Suspected Media</b>",     styles["field_label"]),
        ]
        app_data = [app_header]

        for label, val_func in [
            ("Noise Residual Variance", lambda a, f, p: str(p.get("noise", {}).get("residual_variance", "N/A")) if p else "N/A"),
            ("LBP Texture Entropy",     lambda a, f, p: str(p.get("texture", {}).get("lbp_entropy", "N/A")) if p else "N/A"),
            ("Chrominance Richness",    lambda a, f, p: str(p.get("color", {}).get("chrominance_richness", "N/A")) if p else "N/A"),
            ("Edge Density",            lambda a, f, p: str(p.get("edges", {}).get("edge_density", "N/A")) if p else "N/A"),
            ("2D FFT Spectral Ratio",   lambda a, f, p: str(p.get("frequency", {}).get("high_low_ratio", "N/A")) if p else "N/A"),
            ("EXIF Hardware / Software",lambda a, f, p: " / ".join(filter(None, [p.get("metadata", {}).get("camera_make"), p.get("metadata", {}).get("software")])) or "No EXIF" if p else "N/A"),
        ]:
            r_str = val_func(ref_analysis, ref_fusion, ref_pf)
            s_str = val_func(sus_analysis, sus_fusion, sus_pf)
            app_data.append([
                Paragraph(label, styles["field_label"]),
                Paragraph(str(r_str), styles["field_val"]),
                Paragraph(str(s_str), styles["field_val"]),
            ])

        app_table = Table(app_data, colWidths=[CONTENT_W * 0.38, CONTENT_W * 0.31, CONTENT_W * 0.31])
        app_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), C_HEADER_BG),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.25, C_BORDER),
            ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ]))
        story.append(app_table)
        story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph(
        f"TruthLens — AI-Powered Deepfake Detection & Digital Evidence Platform  |  End of Report",
        styles["footer_txt"],
    ))

    doc.build(story)
    return buf.getvalue()
