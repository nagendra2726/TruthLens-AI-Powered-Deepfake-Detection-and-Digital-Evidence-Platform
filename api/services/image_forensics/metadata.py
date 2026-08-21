"""
TruthLens — Metadata & EXIF Analysis (Supporting Signal Only)
Extracts image container and EXIF metadata strictly as supporting evidence.
IMPORTANT: Metadata presence or absence NEVER determines whether an image is AI-generated.
"""
from __future__ import annotations

import io
from typing import Any, Dict, List, Optional
from PIL import Image, ExifTags
from .schemas import MetadataSignals


def extract_metadata_signals(image_bytes: bytes) -> MetadataSignals:
    """
    Extracts EXIF metadata fields and tags without exposing raw private coordinates or paths.
    Strictly used as supporting context; never drives automated AI classification.
    """
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    software: Optional[str] = None
    creation_date: Optional[str] = None
    gps_present: bool = False
    observations: List[str] = []

    try:
        img = Image.open(io.BytesIO(image_bytes))
        raw_exif = img.getexif()

        if raw_exif:
            # Map numeric EXIF tags to readable strings
            for tag_id, value in raw_exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                if tag_name == "Make" and value:
                    camera_make = str(value).strip()
                elif tag_name == "Model" and value:
                    camera_model = str(value).strip()
                elif tag_name == "Software" and value:
                    software = str(value).strip()
                elif tag_name in ("DateTime", "DateTimeOriginal", "DateTimeDigitized") and value:
                    creation_date = str(value).strip()
                elif tag_name == "GPSInfo":
                    gps_present = True

            # Also check EXIF IFD sub-dictionaries if present
            if hasattr(raw_exif, "get_ifd"):
                try:
                    exif_ifd = raw_exif.get_ifd(ExifTags.IFD.Exif)
                    for ifd_tag_id, val in exif_ifd.items():
                        ifd_tag_name = ExifTags.TAGS.get(ifd_tag_id, str(ifd_tag_id))
                        if ifd_tag_name in ("DateTimeOriginal", "DateTimeDigitized") and val and not creation_date:
                            creation_date = str(val).strip()
                except Exception:
                    pass

        has_exif = bool(camera_make or camera_model or software or creation_date or gps_present)

        if has_exif:
            observations.append("Standard EXIF metadata block detected.")
            if camera_make or camera_model:
                device_str = " ".join(filter(None, [camera_make, camera_model]))
                observations.append(f"Recorded capture hardware: {device_str}")
            if software:
                observations.append(f"Recorded processing/editing software: {software}")
            if gps_present:
                observations.append("Geotagging metadata flag present.")
        else:
            observations.append("No EXIF metadata block present (common in web/messaging re-encoded media).")

        return MetadataSignals(
            available=has_exif,
            camera_make=camera_make,
            camera_model=camera_model,
            software=software,
            creation_date=creation_date,
            gps_present=gps_present,
            supporting_observations=observations,
        )
    except Exception as e:
        return MetadataSignals(
            available=False,
            camera_make=None,
            camera_model=None,
            software=None,
            creation_date=None,
            gps_present=False,
            supporting_observations=[f"Metadata extraction unavailable: {str(e)}"],
        )
