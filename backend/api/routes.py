"""
CrimeVision AI - API Routes
REST API endpoints for evidence management, analysis, fusion, chat, and reports.
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from backend.config import UPLOAD_DIR, REPORTS_DIR
from backend.models.schemas import (
    APIResponse, EvidenceItem, EvidenceType, AnalysisStatus,
    ImageAnalysisResult, AudioAnalysisResult, VideoAnalysisResult,
    FusedEvidence, ChatRequest, ChatResponse
)
from backend.utils.helpers import classify_evidence_type, get_upload_path, get_file_hash
from backend.modules.image_analysis import image_analyzer
from backend.modules.audio_analysis import audio_analyzer
from backend.modules.video_analysis import video_analyzer
from backend.modules.fusion import fusion_engine
from backend.modules.chat import chat_interface
from backend.modules.reports import report_generator

router = APIRouter(prefix="/api")

# In-memory store for evidence items and analysis results
# (can easily be persisted or extended to a database)
evidence_db: dict[str, EvidenceItem] = {}
analysis_results_db: dict[str, dict] = {
    "image": {},
    "audio": {},
    "video": {},
}
fused_cases_db: dict[str, FusedEvidence] = {}


@router.get("/health", response_model=APIResponse)
async def health_check():
    """System health and status check."""
    return APIResponse(
        success=True,
        message="CrimeVision AI Core Engine Online",
        data={
            "status": "operational",
            "version": "1.0.0",
            "modules": {
                "image_analysis": True,
                "audio_analysis": True,
                "video_analysis": True,
                "multimodal_fusion": True,
                "chat_intelligence": True,
                "report_generation": True
            },
            "evidence_count": len(evidence_db)
        }
    )


@router.get("/stats", response_model=APIResponse)
async def get_stats():
    """Retrieve system and evidence summary statistics."""
    total_images = sum(1 for e in evidence_db.values() if e.evidence_type == EvidenceType.IMAGE)
    total_audio = sum(1 for e in evidence_db.values() if e.evidence_type == EvidenceType.AUDIO)
    total_video = sum(1 for e in evidence_db.values() if e.evidence_type == EvidenceType.VIDEO)
    analyzed_count = sum(1 for e in evidence_db.values() if e.status == AnalysisStatus.COMPLETED)

    # Count detections
    weapons_count = 0
    persons_count = 0
    for res in analysis_results_db["image"].values():
        if isinstance(res, ImageAnalysisResult):
            weapons_count += len(res.weapons_detected)
            persons_count += res.persons_count

    return APIResponse(
        success=True,
        message="System statistics retrieved",
        data={
            "total_evidence": len(evidence_db),
            "analyzed_count": analyzed_count,
            "counts_by_type": {
                "image": total_images,
                "audio": total_audio,
                "video": total_video
            },
            "threats_detected": weapons_count,
            "persons_identified": persons_count,
            "fused_cases_count": len(fused_cases_db)
        }
    )


# ─── Evidence Endpoints ──────────────────────────────────────────

@router.get("/evidence", response_model=APIResponse)
async def list_evidence(type: Optional[str] = None):
    """List all uploaded evidence, optionally filtered by type."""
    items = list(evidence_db.values())
    if type:
        items = [i for i in items if i.evidence_type.value == type.lower()]
    
    # Sort newest first
    items.sort(key=lambda x: x.uploaded_at, reverse=True)
    return APIResponse(
        success=True,
        message=f"Found {len(items)} evidence item(s)",
        data=[item.model_dump() for item in items]
    )


@router.get("/evidence/{evidence_id}", response_model=APIResponse)
async def get_evidence(evidence_id: str):
    """Get single evidence details and its analysis result."""
    if evidence_id not in evidence_db:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    item = evidence_db[evidence_id]
    return APIResponse(
        success=True,
        message="Evidence details retrieved",
        data=item.model_dump()
    )


@router.post("/evidence/upload", response_model=APIResponse)
async def upload_evidence(
    file: UploadFile = File(...),
    notes: Optional[str] = Form(""),
    tags: Optional[str] = Form("")
):
    """Upload a new piece of digital evidence (image, audio, or video)."""
    raw_type = classify_evidence_type(file.filename)
    if not raw_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Please upload an image, audio, or video file."
        )

    evidence_type = EvidenceType(raw_type)
    evidence_id = str(uuid.uuid4())

    dest_path = get_upload_path(evidence_type.value, file.filename)
    
    # Save file to disk
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(dest_path)
    parsed_tags = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    item = EvidenceItem(
        evidence_id=evidence_id,
        filename=file.filename,
        evidence_type=evidence_type,
        file_path=str(dest_path),
        file_size=file_size,
        uploaded_at=datetime.utcnow(),
        status=AnalysisStatus.PENDING,
        notes=notes or "",
        tags=parsed_tags
    )
    evidence_db[evidence_id] = item

    return APIResponse(
        success=True,
        message="Evidence uploaded successfully",
        data=item.model_dump()
    )


@router.delete("/evidence/{evidence_id}", response_model=APIResponse)
async def delete_evidence(evidence_id: str):
    """Delete an evidence item and its associated files."""
    if evidence_id not in evidence_db:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    item = evidence_db[evidence_id]
    if os.path.exists(item.file_path):
        try:
            os.remove(item.file_path)
        except OSError:
            pass
            
    # Remove from analysis stores
    ev_type = item.evidence_type.value
    if evidence_id in analysis_results_db.get(ev_type, {}):
        del analysis_results_db[ev_type][evidence_id]
        
    del evidence_db[evidence_id]
    return APIResponse(success=True, message="Evidence deleted successfully")


# ─── Analysis Endpoints ──────────────────────────────────────────

@router.post("/analyze/{evidence_id}", response_model=APIResponse)
async def analyze_evidence(evidence_id: str):
    """Run forensic analysis on an uploaded evidence item."""
    if evidence_id not in evidence_db:
        raise HTTPException(status_code=404, detail="Evidence not found")

    item = evidence_db[evidence_id]
    item.status = AnalysisStatus.PROCESSING

    try:
        if item.evidence_type == EvidenceType.IMAGE:
            result = image_analyzer.analyze(item.file_path, evidence_id=evidence_id)
            analysis_results_db["image"][evidence_id] = result
            chat_interface.register_evidence("images", result)

        elif item.evidence_type == EvidenceType.AUDIO:
            result = audio_analyzer.analyze(item.file_path, evidence_id=evidence_id)
            analysis_results_db["audio"][evidence_id] = result
            chat_interface.register_evidence("audio", result)

        elif item.evidence_type == EvidenceType.VIDEO:
            result = video_analyzer.analyze(item.file_path, evidence_id=evidence_id)
            analysis_results_db["video"][evidence_id] = result
            chat_interface.register_evidence("video", result)
        else:
            raise HTTPException(status_code=400, detail="Unknown evidence type")

        item.status = AnalysisStatus.COMPLETED
        item.analysis_result = result.model_dump()

        return APIResponse(
            success=True,
            message=f"{item.evidence_type.value.capitalize()} forensic analysis complete",
            data=item.model_dump()
        )

    except Exception as e:
        item.status = AnalysisStatus.FAILED
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/all", response_model=APIResponse)
async def analyze_all_pending():
    """Trigger analysis for all pending evidence items."""
    processed = []
    for ev_id, item in list(evidence_db.items()):
        if item.status == AnalysisStatus.PENDING:
            try:
                if item.evidence_type == EvidenceType.IMAGE:
                    res = image_analyzer.analyze(item.file_path, evidence_id=ev_id)
                    analysis_results_db["image"][ev_id] = res
                    chat_interface.register_evidence("images", res)
                elif item.evidence_type == EvidenceType.AUDIO:
                    res = audio_analyzer.analyze(item.file_path, evidence_id=ev_id)
                    analysis_results_db["audio"][ev_id] = res
                    chat_interface.register_evidence("audio", res)
                elif item.evidence_type == EvidenceType.VIDEO:
                    res = video_analyzer.analyze(item.file_path, evidence_id=ev_id)
                    analysis_results_db["video"][ev_id] = res
                    chat_interface.register_evidence("video", res)

                item.status = AnalysisStatus.COMPLETED
                item.analysis_result = res.model_dump()
                processed.append(ev_id)
            except Exception as e:
                item.status = AnalysisStatus.FAILED

    return APIResponse(
        success=True,
        message=f"Analyzed {len(processed)} pending item(s)",
        data={"analyzed_ids": processed}
    )


# ─── Fusion Endpoints ────────────────────────────────────────────

@router.post("/fusion/fuse", response_model=APIResponse)
async def fuse_multimodal_evidence(case_id: Optional[str] = Form(None)):
    """Run multimodal fusion across all analyzed images, audio, and video."""
    images = list(analysis_results_db["image"].values())
    audio = list(analysis_results_db["audio"].values())
    video = list(analysis_results_db["video"].values())

    if not images and not audio and not video:
        raise HTTPException(
            status_code=400,
            detail="No analyzed evidence available to fuse. Please analyze evidence first."
        )

    fused = fusion_engine.fuse(
        image_results=images,
        audio_results=audio,
        video_results=video,
        case_id=case_id
    )
    
    fused_cases_db[fused.case_id] = fused
    chat_interface.register_evidence("fused", fused)

    return APIResponse(
        success=True,
        message=f"Multimodal evidence fused successfully into Case {fused.case_id}",
        data=fused.model_dump()
    )


@router.get("/fusion/cases", response_model=APIResponse)
async def list_fused_cases():
    """List all fused forensic cases."""
    cases = [c.model_dump() for c in fused_cases_db.values()]
    return APIResponse(
        success=True,
        message=f"Found {len(cases)} fused case(s)",
        data=cases
    )


@router.get("/fusion/cases/{case_id}", response_model=APIResponse)
async def get_fused_case(case_id: str):
    """Get single fused forensic case details."""
    if case_id not in fused_cases_db:
        raise HTTPException(status_code=404, detail="Case not found")
    return APIResponse(
        success=True,
        message="Case details retrieved",
        data=fused_cases_db[case_id].model_dump()
    )


# ─── AI Chat Endpoints ───────────────────────────────────────────

@router.post("/chat", response_model=APIResponse)
async def chat_with_intelligence(request: ChatRequest):
    """Interact with the forensic AI chat intelligence agent."""
    response = chat_interface.chat(request)
    return APIResponse(
        success=True,
        message="Chat response generated",
        data=response.model_dump()
    )


@router.get("/chat/history", response_model=APIResponse)
async def get_chat_history():
    """Get conversation history."""
    history = [m.model_dump() for m in chat_interface.conversation_history]
    return APIResponse(
        success=True,
        message="Chat history retrieved",
        data=history
    )


# ─── Report Endpoints ────────────────────────────────────────────

@router.post("/reports/generate", response_model=APIResponse)
async def generate_report(case_id: Optional[str] = Form(None)):
    """Generate a comprehensive forensic PDF report for a case or all current evidence."""
    images = list(analysis_results_db["image"].values())
    audio = list(analysis_results_db["audio"].values())
    video = list(analysis_results_db["video"].values())
    
    fused = None
    if case_id and case_id in fused_cases_db:
        fused = fused_cases_db[case_id]
    elif fused_cases_db:
        # Take the most recent case
        fused = list(fused_cases_db.values())[-1]

    if not images and not audio and not video and not fused:
        raise HTTPException(
            status_code=400,
            detail="No analyzed evidence available to generate report. Upload and analyze evidence first."
        )

    file_path = report_generator.generate_report(
        case_id=case_id or (fused.case_id if fused else None),
        image_results=images,
        audio_results=audio,
        video_results=video,
        fused=fused
    )

    filename = os.path.basename(file_path)
    return APIResponse(
        success=True,
        message="Forensic report generated successfully",
        data={
            "filename": filename,
            "download_url": f"/api/reports/download/{filename}"
        }
    )


@router.get("/reports/download/{filename}")
async def download_report(filename: str):
    """Download a generated forensic report."""
    file_path = REPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    media_type = "application/pdf" if filename.endswith(".pdf") else "text/plain"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )


# ─── Static Evidence Serving ─────────────────────────────────────

@router.get("/evidence/file/{evidence_id}")
async def serve_evidence_file(evidence_id: str):
    """Serve the original media file for preview in frontend."""
    if evidence_id not in evidence_db:
        raise HTTPException(status_code=404, detail="Evidence not found")
        
    item = evidence_db[evidence_id]
    if not os.path.exists(item.file_path):
        raise HTTPException(status_code=404, detail="File on disk not found")
        
    return FileResponse(item.file_path)
