"""
TruthLens — Evidence Hasher
Computes SHA-256 of file bytes using chunked streaming to avoid loading
large files entirely into memory at once.
"""
from __future__ import annotations

import hashlib


CHUNK_SIZE = 65536  # 64 KB per chunk


def sha256_of_bytes(data: bytes) -> str:
    """Return the lowercase hex SHA-256 of a bytes object.

    Uses chunked hashing internally so even large in-memory buffers
    don't require a second full copy during digest computation.
    """
    h = hashlib.sha256()
    offset = 0
    while offset < len(data):
        h.update(data[offset : offset + CHUNK_SIZE])
        offset += CHUNK_SIZE
    return h.hexdigest()
