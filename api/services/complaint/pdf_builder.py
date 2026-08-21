"""
TruthLens — Complaint Draft PDF Builder
Generates a structured, clean A4 "USER-REVIEWABLE COMPLAINT DRAFT" PDF using ReportLab.
Clearly demarcated as a preparatory document for manual submission.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable

from services.report.case_store import EvidenceCase
from .schemas import ComplaintDraftResponse

# Palette
C_DARK_BG    = colors.HexColor("#0f172a")
C_ACCENT     = colors.HexColor("#2563eb")
C_DANGER     = colors.HexColor("#dc2626")
C_WARNING    = colors.HexColor("#d97706")
C_SUCCESS    = colors.HexColor("#059669")
C_NEUTRAL    = colors.HexColor("#64748b")
C_TEXT       = colors.HexColor("#1e293b")
C_BORDER     = colors.HexColor("#cbd5e1")
C_SECTION_BG = colors.HexColor("#f8fafc")

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm
CONTENT_W = PAGE_W - 2 * MARGIN


def _make_styles():
    base = getSampleStyleSheet()

    def ps(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    return {
        "title": ps("cd_title", fontSize=18, leading=22, textColor=C_ACCENT,
                    alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=4),
        "subtitle": ps("cd_sub", fontSize=10, leading=14, textColor=C_DANGER,
                       alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=8),
        "meta": ps("cd_meta", fontSize=8.5, leading=12, textColor=C_NEUTRAL,
                   alignment=TA_CENTER, fontName="Helvetica", spaceAfter=12),
        "sec_hdr": ps("cd_sec_hdr", fontSize=10.5, leading=14, textColor=C_DARK_BG,
                      fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=4),
        "field_lbl": ps("cd_lbl", fontSize=8.5, leading=12, textColor=C_NEUTRAL,
                        fontName="Helvetica-Bold"),
        "field_val": ps("cd_val", fontSize=9, leading=13, textColor=C_TEXT,
                        fontName="Helvetica"),
        "mono": ps("cd_mono", fontSize=8, leading=11, textColor=C_TEXT,
                   fontName="Courier"),
        "body": ps("cd_body", fontSize=9, leading=14, textColor=C_TEXT,
                   fontName="Helvetica", alignment=TA_JUSTIFY),
        "declaration": ps("cd_decl", fontSize=9, leading=14, textColor=C_TEXT,
                          fontName="Helvetica-Oblique", alignment=TA_JUSTIFY),
        "disclaimer": ps("cd_disc", fontSize=7.5, leading=11, textColor=C_NEUTRAL,
                         fontName="Helvetica-Oblique", alignment=TA_JUSTIFY),
    }


def _header_footer(canvas, doc):
    canvas.saveState()
    # Top rule & header
    canvas.setStrokeColor(C_ACCENT)
    canvas.setLineWidth(1.2)
    canvas.line(MARGIN, PAGE_H - 1.1 * cm, PAGE_W - MARGIN, PAGE_H - 1.1 * cm)

    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(C_ACCENT)
    canvas.drawString(MARGIN, PAGE_H - 0.85 * cm, "TruthLens | Cybercrime Complaint Assistance")

    case_id = getattr(doc, "_case_id", "")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(C_NEUTRAL)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 0.85 * cm, "USER-REVIEWABLE COMPLAINT DRAFT (NON-OFFICIAL)")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.85 * cm, f"Case ID: {case_id}")

    # Bottom rule & page numbering
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.1 * cm, PAGE_W - MARGIN, 1.1 * cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(C_NEUTRAL)
    canvas.drawCentredString(PAGE_W / 2, 0.7 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_complaint_pdf(draft_response: ComplaintDraftResponse, case: EvidenceCase) -> bytes:
    """Builds a PDF document from the structured complaint draft."""
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
    )
    doc._case_id = case.case_id

    frame = Frame(MARGIN, 1.4 * cm, CONTENT_W, PAGE_H - 2.8 * cm, id="normal")
    template = PageTemplate(id="draft_page", frames=frame, onPage=_header_footer)
    doc.addPageTemplates([template])

    styles = _make_styles()
    story = []

    draft = draft_response.draft

    # --- Header Banner ---
    story.append(Paragraph("TRUTHLENS CYBERCRIME COMPLAINT ASSISTANCE", styles["title"]))
    story.append(Paragraph("USER-REVIEWABLE COMPLAINT DRAFT — NOT AN OFFICIAL FILING", styles["subtitle"]))
    story.append(Paragraph(
        f"Case Reference: <b>{case.case_id}</b> &nbsp;|&nbsp; "
        f"Draft Generated: {draft_response.generated_at} UTC",
        styles["meta"]
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=8, spaceBefore=2))

    # --- Section 1: Subject & Incident Particulars ---
    story.append(Paragraph("1. Incident Particulars & Platform Information", styles["sec_hdr"]))
    
    user_info = draft.user_provided_info
    info_table_data = [
        [
            Paragraph("Subject:", styles["field_lbl"]),
            Paragraph(draft.subject, styles["field_val"]),
        ],
        [
            Paragraph("Incident Date:", styles["field_lbl"]),
            Paragraph(str(user_info.get("incident_date", "Not provided")), styles["field_val"]),
        ],
        [
            Paragraph("Incident Time:", styles["field_lbl"]),
            Paragraph(str(user_info.get("incident_time", "Not provided")), styles["field_val"]),
        ],
        [
            Paragraph("Platform / Service:", styles["field_lbl"]),
            Paragraph(str(user_info.get("platform", "Not provided")), styles["field_val"]),
        ],
        [
            Paragraph("Platform / Post URL:", styles["field_lbl"]),
            Paragraph(str(user_info.get("platform_url", "Not provided")), styles["field_val"]),
        ],
        [
            Paragraph("Suspected Account:", styles["field_lbl"]),
            Paragraph(str(user_info.get("suspected_account", "Not provided")), styles["field_val"]),
        ],
    ]
    t1 = Table(info_table_data, colWidths=[3.2 * cm, CONTENT_W - 3.2 * cm])
    t1.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (-1, -1), C_SECTION_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#f1f5f9")),
    ]))
    story.append(t1)
    story.append(Spacer(1, 8))

    # --- Section 2: User Statement & Harm ---
    story.append(Paragraph("2. Incident Statement & Observed Impact", styles["sec_hdr"]))
    desc_p = Paragraph(f"<b>Statement of Facts:</b><br/>{draft.incident_details}", styles["body"])
    impact_p = Paragraph(f"<b>Observed Impact / Harm:</b><br/>{user_info.get('impact_description', 'Not provided')}", styles["body"])
    add_p = Paragraph(f"<b>Additional Information:</b><br/>{user_info.get('additional_information', 'Not provided')}", styles["body"])

    statement_table = Table([[desc_p], [impact_p], [add_p]], colWidths=[CONTENT_W])
    statement_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, -1), C_SECTION_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
    ]))
    story.append(statement_table)
    story.append(Spacer(1, 8))

    # --- Section 3: TruthLens Forensic Screening Summary ---
    story.append(Paragraph("3. TruthLens Forensic Screening Summary", styles["sec_hdr"]))
    analysis = draft.analysis_summary
    analysis_table_data = [
        [
            Paragraph("Reference Media Authenticity:", styles["field_lbl"]),
            Paragraph(str(analysis.get("reference_authenticity", "N/A")), styles["field_val"]),
            Paragraph("Decision Category:", styles["field_lbl"]),
            Paragraph(f"<b>{analysis.get('truthlens_assessment', 'N/A')}</b>", styles["field_val"]),
        ],
        [
            Paragraph("Suspected Media Authenticity:", styles["field_lbl"]),
            Paragraph(str(analysis.get("suspected_authenticity", "N/A")), styles["field_val"]),
            Paragraph("Risk Level / Confidence:", styles["field_lbl"]),
            Paragraph(f"{analysis.get('risk_level', 'N/A')} / {analysis.get('confidence', 'N/A')}", styles["field_val"]),
        ],
        [
            Paragraph("Face Identity Verification:", styles["field_lbl"]),
            Paragraph(f"{analysis.get('face_verification', 'N/A')} (Sim: {analysis.get('face_similarity', 'N/A')})", styles["field_val"]),
            Paragraph("Forensic Note:", styles["field_lbl"]),
            Paragraph(str(analysis.get("analysis_explanation", "N/A")), styles["field_val"]),
        ],
    ]
    t3 = Table(analysis_table_data, colWidths=[3.5 * cm, 4.5 * cm, 3.5 * cm, CONTENT_W - 11.5 * cm])
    t3.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (-1, -1), C_SECTION_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#f1f5f9")),
    ]))
    story.append(t3)
    story.append(Spacer(1, 8))

    # --- Section 4: Digital Evidence & Hashes ---
    story.append(Paragraph("4. Digital Evidence & Cryptographic Verification", styles["sec_hdr"]))
    ev = draft.evidence_summary
    ev_table_data = [
        [
            Paragraph("Reference File & Hash:", styles["field_lbl"]),
            Paragraph(f"<b>{ev.get('reference_filename', 'N/A')}</b><br/>SHA-256: <font face='Courier' size='7'>{ev.get('reference_sha256', 'N/A')}</font>", styles["field_val"]),
        ],
        [
            Paragraph("Suspected File & Hash:", styles["field_lbl"]),
            Paragraph(f"<b>{ev.get('suspected_filename', 'N/A')}</b><br/>SHA-256: <font face='Courier' size='7'>{ev.get('suspected_sha256', 'N/A')}</font>", styles["field_val"]),
        ],
        [
            Paragraph("Forensic Report Reference:", styles["field_lbl"]),
            Paragraph(f"<b>{ev.get('forensic_report_reference', 'N/A')}</b> (Complete technical breakdown attached)", styles["field_val"]),
        ],
    ]
    t4 = Table(ev_table_data, colWidths=[3.5 * cm, CONTENT_W - 3.5 * cm])
    t4.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (-1, -1), C_SECTION_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#f1f5f9")),
    ]))
    story.append(t4)
    story.append(Spacer(1, 8))

    # --- Section 5: User Declaration & Signature Placeholder ---
    decl_elements = [
        Paragraph("5. User Affirmation & Declaration", styles["sec_hdr"]),
        Paragraph(f'"{draft.user_declaration}"', styles["declaration"]),
        Spacer(1, 8),
        Table([
            [
                Paragraph("Complainant Name: _______________________", styles["field_val"]),
                Paragraph("Signature: _______________________", styles["field_val"]),
                Paragraph("Date: ____________", styles["field_val"]),
            ]
        ], colWidths=[CONTENT_W / 3, CONTENT_W / 3, CONTENT_W / 3]),
        Spacer(1, 8),
        Paragraph("6. Notice & Legal Disclaimer", styles["sec_hdr"]),
        Paragraph(draft.legal_disclaimer, styles["disclaimer"]),
        Paragraph(f"Official Submission Channel Reference: <b>{draft_response.official_portal_url}</b>", styles["disclaimer"]),
    ]
    story.append(KeepTogether(decl_elements))

    doc.build(story)
    return buf.getvalue()
