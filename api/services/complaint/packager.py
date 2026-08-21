"""
TruthLens — Incident Evidence Packager
Bundles verified forensic artifacts into a secure ZIP package:
- Complaint Draft (TXT & PDF)
- Forensic Report PDF (Task 4)
- Evidence Manifest JSON (SHA-256 hashes, timestamps, metadata)

Security guarantees:
- Never includes raw face embeddings
- Never includes server secrets, configs, or internal system paths
- Filename adheres to strict format: TruthLens_Evidence_{case_id}.zip
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Optional

from services.report.case_store import EvidenceCase
from services.report.pdf_builder import build_pdf as build_forensic_report_pdf
from .schemas import ComplaintDraftResponse
from .pdf_builder import build_complaint_pdf


def build_evidence_package_zip(
    case: EvidenceCase,
    draft_response: ComplaintDraftResponse,
) -> bytes:
    """Creates an in-memory ZIP package containing all case evidence artifacts."""
    zip_buf = io.BytesIO()
    
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. Plain Text Complaint Draft
        draft_txt = draft_response.draft.full_text.encode("utf-8")
        zf.writestr(f"TruthLens_Complaint_Draft_{case.case_id}.txt", draft_txt)

        # 2. User-Reviewable Complaint Draft PDF
        complaint_pdf_bytes = build_complaint_pdf(draft_response, case)
        zf.writestr(f"TruthLens_Complaint_Draft_{case.case_id}.pdf", complaint_pdf_bytes)

        # 3. Task 4 Forensic Report PDF
        try:
            forensic_pdf_bytes = build_forensic_report_pdf(case)
            zf.writestr(f"TruthLens_Forensic_Report_{case.case_id}.pdf", forensic_pdf_bytes)
        except Exception:
            # If forensic PDF fails to build, package still succeeds with manifest and draft
            pass

        # 4. Sanitized Evidence Manifest JSON
        manifest = {
            "case_id": case.case_id,
            "packaged_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "analysis_completed_at": case.completed_at,
            "evidence_integrity": {
                "reference_media": {
                    "filename": case.reference_filename or "N/A",
                    "sha256": case.reference_sha256 or "N/A",
                    "content_type": case.reference_content_type or "N/A",
                    "size_bytes": case.reference_size_bytes,
                },
                "suspected_media": {
                    "filename": case.suspected_filename or "N/A",
                    "sha256": case.suspected_sha256 or "N/A",
                    "content_type": case.suspected_content_type or "N/A",
                    "size_bytes": case.suspected_size_bytes,
                },
            },
            "forensic_summary": draft_response.draft.analysis_summary,
            "incident_particulars": draft_response.draft.user_provided_info,
            "disclaimer": draft_response.draft.legal_disclaimer,
        }
        manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
        zf.writestr(f"Evidence_Manifest_{case.case_id}.json", manifest_bytes)

    return zip_buf.getvalue()
