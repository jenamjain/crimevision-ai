"""
CrimeVision AI - Utility Functions
Common helper functions used across the platform.
"""
import os
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.config import UPLOAD_DIR, MAX_UPLOAD_SIZE


def generate_evidence_id() -> str:
    """Generate a unique evidence identifier."""
    return str(uuid.uuid4())


def get_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file for integrity verification."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension without the dot."""
    return Path(filename).suffix.lower().lstrip(".")


def classify_evidence_type(filename: str) -> Optional[str]:
    """Classify evidence type based on file extension."""
    ext = get_file_extension(filename)
    image_exts = {"jpg", "jpeg", "png", "bmp", "gif", "tiff", "webp"}
    audio_exts = {"mp3", "wav", "m4a", "ogg", "flac", "aac", "wma"}
    video_exts = {"mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"}

    if ext in image_exts:
        return "image"
    elif ext in audio_exts:
        return "audio"
    elif ext in video_exts:
        return "video"
    return None


def get_upload_path(evidence_type: str, filename: str) -> Path:
    """Get the upload path for a given evidence type and filename."""
    subdir = UPLOAD_DIR / evidence_type
    subdir.mkdir(parents=True, exist_ok=True)
    # Prepend timestamp to avoid collisions
    safe_name = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
    return subdir / safe_name


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}h {mins}m {secs}s"


def validate_file_size(file_size: int) -> bool:
    """Check if file size is within allowed limits."""
    return file_size <= MAX_UPLOAD_SIZE
