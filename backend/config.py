"""
CrimeVision AI - Configuration Settings
"""
import os
from pathlib import Path

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
REPORTS_DIR = BASE_DIR / "reports"
FRONTEND_DIR = BASE_DIR / "frontend"

# Create directories
UPLOAD_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / "images").mkdir(exist_ok=True)
(UPLOAD_DIR / "audio").mkdir(exist_ok=True)
(UPLOAD_DIR / "video").mkdir(exist_ok=True)

# Server Config
HOST = os.getenv("CRIMEVISION_HOST", "0.0.0.0")
PORT = int(os.getenv("CRIMEVISION_PORT", "8000"))

# Analysis Config
IMAGE_ANALYSIS_CONFIDENCE = 0.45
VIDEO_FRAME_INTERVAL = 30  # Extract every Nth frame
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB

# Model Paths (will download automatically on first use)
YOLO_MODEL = "yolov8n.pt"

# Evidence categories
EVIDENCE_CATEGORIES = [
    "crime_scene", "surveillance", "forensic", 
    "witness", "documentary", "digital"
]

WEAPON_CLASSES = [
    "knife", "gun", "pistol", "rifle", "baseball bat",
    "bottle", "scissors", "sword"
]

VEHICLE_CLASSES = [
    "car", "motorcycle", "bus", "truck", "bicycle"
]

PERSON_ACTIONS = [
    "walking", "running", "standing", "fighting",
    "falling", "carrying", "pointing", "crouching"
]
