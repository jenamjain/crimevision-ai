"""
CrimeVision AI - Data Models
Pydantic models for evidence, analysis results, and API responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class EvidenceType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── Detection Models ───────────────────────────────────────────

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    width: float = 0
    height: float = 0


class DetectedObject(BaseModel):
    object_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    label: str
    confidence: float
    bbox: BoundingBox
    category: str = "object"  # person, weapon, vehicle, object
    attributes: Dict[str, Any] = {}


class SceneDescription(BaseModel):
    description: str
    environment: str = ""  # indoor, outdoor, urban, rural
    lighting: str = ""  # daylight, night, artificial
    weather: str = ""
    risk_level: str = "low"  # low, medium, high, critical
    tags: List[str] = []


# ─── Image Analysis Models ───────────────────────────────────────

class ImageAnalysisResult(BaseModel):
    evidence_id: str
    filename: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dimensions: Dict[str, int] = {}
    detected_objects: List[DetectedObject] = []
    persons_count: int = 0
    weapons_detected: List[DetectedObject] = []
    vehicles_detected: List[DetectedObject] = []
    scene: SceneDescription = SceneDescription(description="")
    forensic_notes: List[str] = []
    analysis_duration: float = 0.0


# ─── Audio Analysis Models ────────────────────────────────────────

class SpeakerSegment(BaseModel):
    speaker_id: str
    start_time: float
    end_time: float
    text: str
    confidence: float = 0.0
    sentiment: str = "neutral"  # positive, negative, neutral
    emotion: str = "neutral"


class AudioAnalysisResult(BaseModel):
    evidence_id: str
    filename: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration: float = 0.0
    full_transcript: str = ""
    segments: List[SpeakerSegment] = []
    speakers_count: int = 0
    key_phrases: List[str] = []
    entities: List[Dict[str, str]] = []
    sentiment_summary: Dict[str, float] = {}
    language: str = "en"
    analysis_duration: float = 0.0


# ─── Video Analysis Models ────────────────────────────────────────

class VideoFrame(BaseModel):
    frame_number: int
    timestamp: float  # seconds
    detections: List[DetectedObject] = []
    action: str = ""
    description: str = ""
    is_keyframe: bool = False


class TimelineEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float
    time_label: str = ""
    event_type: str = ""  # detection, action, speech, anomaly
    description: str
    confidence: float = 0.0
    source: str = ""  # image, audio, video
    evidence_id: str = ""
    details: Dict[str, Any] = {}


class VideoAnalysisResult(BaseModel):
    evidence_id: str
    filename: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration: float = 0.0
    fps: float = 0.0
    resolution: Dict[str, int] = {}
    total_frames: int = 0
    keyframes: List[VideoFrame] = []
    timeline: List[TimelineEvent] = []
    persons_tracked: int = 0
    objects_summary: Dict[str, int] = {}
    actions_detected: List[str] = []
    analysis_duration: float = 0.0


# ─── Fusion & Intelligence Models ─────────────────────────────────

class FusedEvidence(BaseModel):
    case_id: str = Field(default_factory=lambda: f"CASE-{str(uuid.uuid4())[:8].upper()}")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    evidence_items: List[str] = []
    unified_timeline: List[TimelineEvent] = []
    cross_modal_correlations: List[Dict[str, Any]] = []
    intelligence_summary: str = ""
    risk_assessment: str = "low"
    key_findings: List[str] = []
    recommendations: List[str] = []


# ─── Chat Models ──────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    evidence_refs: List[str] = []


class ChatRequest(BaseModel):
    message: str
    case_id: Optional[str] = None
    context_evidence: List[str] = []


class ChatResponse(BaseModel):
    response: str
    evidence_refs: List[str] = []
    confidence: float = 0.0
    suggestions: List[str] = []


# ─── API Response Models ─────────────────────────────────────────

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EvidenceItem(BaseModel):
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    evidence_type: EvidenceType
    file_path: str
    file_size: int = 0
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    status: AnalysisStatus = AnalysisStatus.PENDING
    analysis_result: Optional[Any] = None
    tags: List[str] = []
    notes: str = ""
