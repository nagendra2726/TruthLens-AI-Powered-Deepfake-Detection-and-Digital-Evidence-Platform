import io
import os
import json
import zipfile
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional

try:
    from .pdf_builder import build_pdf
    from .summary_builder import build_summary_pdf
except ImportError:
    from services.report.pdf_builder import build_pdf
    from services.report.summary_builder import build_summary_pdf


def build_case_metadata_json(case) -> Dict[str, Any]:
    ref_analysis = json.loads(case.reference_analysis_json) if case.reference_analysis_json else {}
    sus_analysis = json.loads(case.suspected_analysis_json) if case.suspected_analysis_json else {}
    face_verif = json.loads(case.face_verification_json) if case.face_verification_json else {}
    assessment = json.loads(case.assessment_json) if case.assessment_json else {}
    model_info = json.loads(case.model_info_json) if case.model_info_json else {}

    ref_fusion = ref_analysis.get("evidence_fusion", {})
    sus_fusion = sus_analysis.get("evidence_fusion", {})

    media_type = "image"
    ct = (case.reference_content_type or case.suspected_content_type or "").lower()
    if "video" in ct or (case.reference_filename or "").lower().endswith((".mp4", ".avi", ".mov")):
        media_type = "video"
    elif "audio" in ct or (case.reference_filename or "").lower().endswith((".wav", ".mp3", ".flac", ".m4a")):
        media_type = "audio"

    return {
        "caseId": case.case_id,
        "createdAt": case.created_at,
        "completedAt": case.completed_at,
        "analysisType": media_type,
        "status": "Case File Ready",
        "media": {
            "referenceFilename": case.reference_filename,
            "referenceFormat": case.reference_content_type,
            "referenceSize": case.reference_size_bytes,
            "referenceResolution": f"{case.reference_width}x{case.reference_height}" if case.reference_width and case.reference_height else "N/A",
            "referenceSha256": case.reference_sha256,
            "suspectedFilename": case.suspected_filename,
            "suspectedFormat": case.suspected_content_type,
            "suspectedSize": case.suspected_size_bytes,
            "suspectedResolution": f"{case.suspected_width}x{case.suspected_height}" if case.suspected_width and case.suspected_height else "N/A",
            "suspectedSha256": case.suspected_sha256,
        },
        "analysis": {
            "assessment": assessment.get("category"),
            "aiScore": sus_analysis.get("ai_probability", 0.0),
            "forensicScore": sus_fusion.get("forensic_score", 0.0),
            "confidence": assessment.get("confidence", "N/A"),
            "riskLevel": assessment.get("risk_level", "N/A"),
            "explanation": assessment.get("explanation", ""),
        },
        "faceVerification": {
            "performed": bool(face_verif and face_verif.get("result")),
            "similarity": face_verif.get("best_match_score"),
            "result": face_verif.get("result"),
            "referenceFacesCount": face_verif.get("reference_faces_count", 0),
            "suspectedFacesCount": face_verif.get("suspected_faces_count", 0),
        },
        "modelInfo": model_info,
        "report": {
            "generated": True,
            "version": case.report_version or "1.0",
        },
        "audit": {
            "createdAt": case.created_at,
            "completedAt": case.completed_at,
            "reportGeneratedAt": case.report_generated_at or case.completed_at,
            "caseFileGeneratedAt": datetime.now(timezone.utc).isoformat(),
        },
        "incidentDocket": assessment.get("incident_docket", {}),
        "disclaimer": "TruthLens provides AI-assisted digital media analysis. Results may contain errors and should be independently reviewed. The generated case file is an analytical record and does not by itself establish the authenticity or origin of the media.",
    }


def build_case_zip(case) -> bytes:
    zip_buffer = io.BytesIO()
    cid = case.case_id

    # 1. Build PDF report and Summary PDF
    report_pdf_bytes = build_pdf(case)
    summary_pdf_bytes = build_summary_pdf(case)

    # 2. Build Metadata JSON
    meta_dict = build_case_metadata_json(case)
    meta_json_str = json.dumps(meta_dict, indent=2)

    # 3. Build README text
    readme_text = f"""========================================================================
TRUTHLENS DIGITAL EVIDENCE CASE PACKAGE
Case ID: {cid}
Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
========================================================================

CONTENTS:
1. {cid}_Summary.pdf    - Executive 1-Page Analysis Case Summary
2. {cid}_Report.pdf     - Detailed 3-Page Forensic Analysis Report
3. {cid}_Metadata.json   - Machine-Readable Case Metadata & Signal Details
4. Evidence/            - Extracted Preview Evidence Files (if stored)
5. README.txt           - Audit Trail & Disclaimer Information

LEGAL & ACADEMIC DISCLAIMER:
TruthLens provides AI-assisted digital media analysis. Results are probabilistic,
contain analytical estimates, and should be independently reviewed by human forensic
experts. This case package is an analytical record and does not by itself establish
the legal authenticity or criminal provenance of the analyzed media.

INTEGRITY HASHING:
Reference SHA-256: {case.reference_sha256 or 'N/A'}
Suspected SHA-256: {case.suspected_sha256 or 'N/A'}
"""

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        prefix = f"TruthLens_Case_{cid}/"

        zf.writestr(f"{prefix}{cid}_Summary.pdf", summary_pdf_bytes)
        zf.writestr(f"{prefix}{cid}_Report.pdf", report_pdf_bytes)
        zf.writestr(f"{prefix}{cid}_Metadata.json", meta_json_str.encode("utf-8"))
        zf.writestr(f"{prefix}README.txt", readme_text.encode("utf-8"))

        # Evidence folder
        has_media = False
        if case.reference_preview_b64:
            try:
                ref_bytes = base64.b64decode(case.reference_preview_b64)
                ref_ext = os.path.splitext(case.reference_filename or "ref.jpg")[-1] or ".jpg"
                zf.writestr(f"{prefix}Evidence/{cid}_Reference{ref_ext}", ref_bytes)
                has_media = True
            except Exception:
                pass

        if case.suspected_preview_b64:
            try:
                sus_bytes = base64.b64decode(case.suspected_preview_b64)
                sus_ext = os.path.splitext(case.suspected_filename or "sus.png")[-1] or ".png"
                zf.writestr(f"{prefix}Evidence/{cid}_Suspected{sus_ext}", sus_bytes)
                has_media = True
            except Exception:
                pass

        if not has_media:
            no_media_msg = "Original media files are not stored directly in this evidence package to preserve privacy and storage limits. Hashing (SHA-256) is provided in metadata for content verification."
            zf.writestr(f"{prefix}Evidence/README_MEDIA.txt", no_media_msg.encode("utf-8"))

    return zip_buffer.getvalue()
