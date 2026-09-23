"""
TruthLens — Cybercrime Complaint Draft Generator
Translates stored EvidenceCase records and user incident facts into a neutral,
fact-based complaint draft for manual review and submission.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from services.report.case_store import EvidenceCase
from .schemas import (
    ComplaintEligibilityStatus,
    ComplaintEligibilityResponse,
    ComplaintDraftSections,
    ComplaintDraftResponse,
    UserIncidentInput,
)

# Configurable official portal URL
DEFAULT_CYBERCRIME_PORTAL = os.getenv(
    "OFFICIAL_CYBERCRIME_PORTAL_URL", "https://cybercrime.gov.in/"
)

LEGAL_DISCLAIMER = (
    "TruthLens provides AI-assisted analysis and complaint drafting support. "
    "The generated draft is not an official complaint and does not establish that a crime has occurred. "
    "Review all information carefully and submit only accurate information through the appropriate official channel. "
    "TruthLens does not automatically submit complaints."
)

USER_DECLARATION_TEMPLATE = (
    "I have reviewed the information above and confirm that the incident details provided by me "
    "are accurate to the best of my knowledge."
)


def evaluate_case_eligibility(case: EvidenceCase) -> ComplaintEligibilityResponse:
    """
    Evaluates whether complaint assistance is recommended or purely optional.
    Does NOT assert crime, only categorizes forensic screening urgency.
    """
    assessment = {}
    if case.assessment_json:
        try:
            assessment = json.loads(case.assessment_json)
        except Exception:
            pass

    category = assessment.get("category", "UNKNOWN")
    risk_level = assessment.get("risk_level", "UNKNOWN")

    if category == "POTENTIAL_DEEPFAKE" and risk_level == "HIGH":
        status = ComplaintEligibilityStatus.REVIEW_RECOMMENDED
        status_message = "Potential high-risk case identified."
        recommendation_text = (
            "TruthLens detected a combination of signals that may warrant further review. "
            "You can prepare a complaint draft using the available case evidence."
        )
        can_prepare = True
    elif category == "BOTH_MEDIA_APPEAR_SYNTHETIC":
        status = ComplaintEligibilityStatus.NOT_REQUIRED
        status_message = "Both media files appear synthetic."
        recommendation_text = (
            "Review the circumstances before deciding whether to report. "
            "Both reference and suspected media exhibit synthetic/AI generation markers."
        )
        can_prepare = True
    elif category == "LIKELY_AUTHENTIC":
        status = ComplaintEligibilityStatus.NOT_REQUIRED
        status_message = "Suspected media appears authentic."
        recommendation_text = (
            "Based on the current analysis, TruthLens does not automatically recommend a complaint. "
            "You may still review the case and decide whether reporting is appropriate."
        )
        can_prepare = True
    else:
        status = ComplaintEligibilityStatus.NOT_REQUIRED
        status_message = f"Assessment: {category.replace('_', ' ').title()}"
        recommendation_text = (
            "Review the case findings before deciding whether to take formal action."
        )
        can_prepare = True

    return ComplaintEligibilityResponse(
        case_id=case.case_id,
        status=status,
        status_message=status_message,
        assessment_category=category,
        risk_level=risk_level,
        recommendation_text=recommendation_text,
        can_prepare_draft=can_prepare,
    )


def generate_complaint_draft(
    case: EvidenceCase,
    user_input: UserIncidentInput,
) -> ComplaintDraftResponse:
    """
    Constructs a structured, neutral complaint draft combining verified
    forensic evidence with user-provided incident facts.
    """
    eligibility = evaluate_case_eligibility(case)

    # Safely parse case JSON fields
    ref_analysis = json.loads(case.reference_analysis_json or "{}")
    sus_analysis = json.loads(case.suspected_analysis_json or "{}")
    face_verif = json.loads(case.face_verification_json or "{}")
    assessment = json.loads(case.assessment_json or "{}")

    # Format verified evidence details
    ref_status = ref_analysis.get("status", "N/A").replace("_", " ").title()
    sus_status = sus_analysis.get("status", "N/A").replace("_", " ").title()
    face_result = face_verif.get("result", "N/A").replace("_", " ").title()
    
    sim_score = (
        face_verif.get("best_match_score")
        if face_verif.get("best_match_score") is not None
        else face_verif.get("similarity_score")
    )
    face_similarity_str = f"{sim_score * 100:.1f}%" if sim_score is not None else "Similarity unavailable"
    
    assessment_cat = assessment.get("category", "N/A").replace("_", " ").title()
    risk_lvl = assessment.get("risk_level", "N/A")
    confidence_lvl = assessment.get("confidence", "N/A")

    # Format user inputs (ensure no unprovided facts are invented)
    inc_date = user_input.incident_date or "Not provided"
    inc_time = user_input.incident_time or "Not provided"
    platform_name = user_input.platform or "Not provided"
    platform_link = user_input.platform_url or "Not provided"
    sus_account = user_input.suspected_account or "Not provided"
    impact_text = user_input.impact_description or "Not provided"
    add_info_text = user_input.additional_info or "Not provided"

    # Assemble structured sections
    subject = f"Complaint regarding suspected manipulated/AI-generated media [Case {case.case_id}]"
    incident_summary = (
        f"Incident reporting suspected digital media manipulation discovered on {inc_date} "
        f"associated with platform '{platform_name}'."
    )

    user_provided_dict = {
        "incident_date": inc_date,
        "incident_time": inc_time,
        "platform": platform_name,
        "platform_url": platform_link,
        "suspected_account": sus_account,
        "impact_description": impact_text,
        "additional_information": add_info_text,
    }

    analysis_dict = {
        "reference_authenticity": ref_status,
        "suspected_authenticity": sus_status,
        "face_verification": face_result,
        "face_similarity": face_similarity_str,
        "truthlens_assessment": assessment_cat,
        "risk_level": risk_lvl,
        "confidence": confidence_lvl,
        "analysis_explanation": assessment.get("explanation", "N/A"),
    }

    evidence_dict = {
        "case_id": case.case_id,
        "analysis_timestamp": case.completed_at,
        "reference_filename": case.reference_filename or "N/A",
        "reference_sha256": case.reference_sha256 or "N/A",
        "suspected_filename": case.suspected_filename or "N/A",
        "suspected_sha256": case.suspected_sha256 or "N/A",
        "forensic_report_reference": f"TruthLens_Report_{case.case_id}.pdf",
    }

    # Compile plain-text document
    full_text_lines = [
        "================================================================================",
        "                     TRUTHLENS CYBERCRIME COMPLAINT DRAFT                      ",
        "                     (USER-REVIEWABLE COMPLAINT DOCUMENT)                      ",
        "================================================================================",
        "",
        f"SUBJECT: {subject}",
        f"CASE ID: {case.case_id}",
        f"DATE OF ANALYSIS: {case.completed_at}",
        "",
        "--------------------------------------------------------------------------------",
        "1. INCIDENT SUMMARY & PARTICULARS",
        "--------------------------------------------------------------------------------",
        f"Incident Date:        {inc_date}",
        f"Incident Time:        {inc_time}",
        f"Platform / Service:   {platform_name}",
        f"Platform / Post URL:  {platform_link}",
        f"Suspected Account:    {sus_account}",
        "",
        "Incident Description (User Statement):",
        f"{user_input.incident_description}",
        "",
        "Observed Harm / Impact:",
        f"{impact_text}",
        "",
        "Additional Information:",
        f"{add_info_text}",
        "",
        "--------------------------------------------------------------------------------",
        "2. TRUTHLENS FORENSIC SCREENING SUMMARY",
        "--------------------------------------------------------------------------------",
        f"Reference Media Authenticity:  {ref_status}",
        f"Suspected Media Authenticity:  {sus_status}",
        f"Face Identity Verification:    {face_result} (Similarity: {face_similarity_str})",
        f"TruthLens Assessment:          {assessment_cat}",
        f"Risk Level:                    {risk_lvl}",
        f"Decision Confidence:           {confidence_lvl}",
        "",
        "Forensic Observation:",
        f"{assessment.get('explanation', 'Media was analyzed using the DeepSafe multi-model ensemble.')}",
        "",
        "--------------------------------------------------------------------------------",
        "3. DIGITAL EVIDENCE & HASH VERIFICATION",
        "--------------------------------------------------------------------------------",
        f"Reference File:   {case.reference_filename or 'N/A'}",
        f"Reference SHA256: {case.reference_sha256 or 'N/A'}",
        "",
        f"Suspected File:   {case.suspected_filename or 'N/A'}",
        f"Suspected SHA256: {case.suspected_sha256 or 'N/A'}",
        "",
        f"Forensic PDF Reference: TruthLens_Report_{case.case_id}.pdf",
        "",
        "--------------------------------------------------------------------------------",
        "4. USER DECLARATION",
        "--------------------------------------------------------------------------------",
        f'"{USER_DECLARATION_TEMPLATE}"',
        "",
        "--------------------------------------------------------------------------------",
        "5. DISCLAIMER & SUBMISSION NOTICE",
        "--------------------------------------------------------------------------------",
        LEGAL_DISCLAIMER,
        "",
        f"Official Cybercrime Portal Reference: {DEFAULT_CYBERCRIME_PORTAL}",
        "================================================================================",
    ]

    full_text = "\n".join(full_text_lines)

    draft_sections = ComplaintDraftSections(
        subject=subject,
        case_id=case.case_id,
        incident_summary=incident_summary,
        incident_details=user_input.incident_description,
        user_provided_info=user_provided_dict,
        analysis_summary=analysis_dict,
        evidence_summary=evidence_dict,
        user_declaration=USER_DECLARATION_TEMPLATE,
        legal_disclaimer=LEGAL_DISCLAIMER,
        full_text=full_text,
    )

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return ComplaintDraftResponse(
        case_id=case.case_id,
        status=ComplaintEligibilityStatus.USER_REVIEW_REQUIRED,
        status_message="Complaint draft generated successfully. Review all details before manual submission.",
        eligibility_notes=eligibility.recommendation_text,
        draft=draft_sections,
        official_portal_url=DEFAULT_CYBERCRIME_PORTAL,
        generated_at=now_iso,
    )
