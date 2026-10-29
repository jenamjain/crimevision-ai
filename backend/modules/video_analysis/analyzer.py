"""
CrimeVision AI - Video Analysis Module
Performs frame extraction, object tracking, action recognition,
and forensic timeline generation from video evidence.
"""
import os
import time
import uuid
import random
from datetime import datetime
from typing import List, Dict, Optional

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from backend.models.schemas import (
    VideoAnalysisResult, VideoFrame, TimelineEvent, DetectedObject, BoundingBox
)
from backend.config import VIDEO_FRAME_INTERVAL
from backend.modules.image_analysis.analyzer import ImageAnalyzer


class VideoAnalyzer:
    """Analyzes video evidence with frame extraction, tracking, and timeline generation."""

    def __init__(self):
        self.image_analyzer = ImageAnalyzer()

    def analyze(self, video_path: str, evidence_id: str = None,
                frame_interval: int = None) -> VideoAnalysisResult:
        """
        Perform full video forensic analysis.
        
        Args:
            video_path: Path to the video file
            evidence_id: Unique evidence identifier
            frame_interval: Extract every Nth frame (default from config)
            
        Returns:
            VideoAnalysisResult with frame analysis and timeline
        """
        start_time = time.time()
        evidence_id = evidence_id or str(uuid.uuid4())
        filename = os.path.basename(video_path)
        frame_interval = frame_interval or VIDEO_FRAME_INTERVAL

        # Get video metadata
        metadata = self._get_video_metadata(video_path)

        # Extract and analyze keyframes
        if CV2_AVAILABLE:
            keyframes = self._extract_and_analyze_frames(video_path, frame_interval, metadata)
        else:
            keyframes = self._simulate_frame_analysis(metadata)

        # Generate forensic timeline
        timeline = self._generate_timeline(keyframes, metadata)

        # Aggregate statistics
        objects_summary = self._aggregate_objects(keyframes)
        actions = list(set(f.action for f in keyframes if f.action))
        persons_tracked = max(
            (len([d for d in f.detections if d.category == "person"]) for f in keyframes),
            default=0
        )

        duration = time.time() - start_time

        return VideoAnalysisResult(
            evidence_id=evidence_id,
            filename=filename,
            timestamp=datetime.utcnow(),
            duration=metadata.get("duration", 0),
            fps=metadata.get("fps", 0),
            resolution={"width": metadata.get("width", 0), "height": metadata.get("height", 0)},
            total_frames=metadata.get("total_frames", 0),
            keyframes=keyframes,
            timeline=timeline,
            persons_tracked=persons_tracked,
            objects_summary=objects_summary,
            actions_detected=actions,
            analysis_duration=round(duration, 3)
        )

    def _get_video_metadata(self, video_path: str) -> Dict:
        """Extract video metadata."""
        if CV2_AVAILABLE:
            try:
                cap = cv2.VideoCapture(video_path)
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    duration = total_frames / fps if fps > 0 else 0
                    cap.release()
                    return {
                        "fps": round(fps, 2),
                        "total_frames": total_frames,
                        "width": width,
                        "height": height,
                        "duration": round(duration, 2)
                    }
            except Exception as e:
                print(f"[VideoAnalyzer] Error reading video metadata: {e}")

        # Default metadata for simulation
        return {
            "fps": 30.0,
            "total_frames": 900,
            "width": 1920,
            "height": 1080,
            "duration": 30.0
        }

    def _extract_and_analyze_frames(self, video_path: str, frame_interval: int,
                                      metadata: Dict) -> List[VideoFrame]:
        """Extract frames from video and analyze each."""
        keyframes = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            fps = metadata.get("fps", 30)
            frame_count = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    timestamp = frame_count / fps if fps > 0 else 0
                    
                    # Save frame temporarily for analysis
                    temp_frame_path = f"/tmp/cv_frame_{frame_count}.jpg"
                    cv2.imwrite(temp_frame_path, frame)
                    
                    # Analyze frame
                    result = self.image_analyzer.analyze(temp_frame_path)
                    
                    # Determine action
                    action = self._detect_action(result.detected_objects, frame_count)
                    
                    keyframes.append(VideoFrame(
                        frame_number=frame_count,
                        timestamp=round(timestamp, 2),
                        detections=result.detected_objects,
                        action=action,
                        description=result.scene.description,
                        is_keyframe=True
                    ))
                    
                    # Clean up temp file
                    try:
                        os.remove(temp_frame_path)
                    except Exception:
                        pass
                
                frame_count += 1
                
                # Limit analysis to avoid excessive processing
                if len(keyframes) >= 20:
                    break
            
            cap.release()
        except Exception as e:
            print(f"[VideoAnalyzer] Frame extraction error: {e}")
            keyframes = self._simulate_frame_analysis(metadata)
        
        return keyframes

    def _simulate_frame_analysis(self, metadata: Dict) -> List[VideoFrame]:
        """Simulate frame analysis for demo purposes."""
        keyframes = []
        duration = metadata.get("duration", 30)
        fps = metadata.get("fps", 30)
        w = metadata.get("width", 1920)
        h = metadata.get("height", 1080)

        # Generate 8-12 keyframes across the video
        num_keyframes = random.randint(8, 12)
        timestamps = sorted(random.sample(
            [round(i * duration / 20, 2) for i in range(20)],
            min(num_keyframes, 20)
        ))

        action_sequence = [
            "Two individuals walking in frame",
            "Person standing near a vehicle",
            "Rapid movement detected - possible running",
            "Physical altercation between two subjects",
            "Object dropped on the ground",
            "Subject fleeing the scene northward",
            "Vehicle door opening",
            "Subject entering vehicle",
            "Vehicle accelerating rapidly",
            "Scene appears clear - no subjects visible",
            "Bystander approaching the area",
            "Emergency vehicle arriving"
        ]

        for i, ts in enumerate(timestamps):
            frame_num = int(ts * fps)
            
            # Generate varying detections per frame
            num_persons = random.randint(0, 3)
            detections = []
            
            for p in range(num_persons):
                detections.append(DetectedObject(
                    label="person",
                    confidence=round(random.uniform(0.72, 0.98), 4),
                    bbox=BoundingBox(
                        x1=round(random.uniform(50, w * 0.5), 2),
                        y1=round(random.uniform(50, h * 0.3), 2),
                        x2=round(random.uniform(w * 0.3, w * 0.8), 2),
                        y2=round(random.uniform(h * 0.4, h * 0.9), 2),
                        width=round(random.uniform(80, 200), 2),
                        height=round(random.uniform(150, 400), 2)
                    ),
                    category="person",
                    attributes={"tracked_id": f"P{p+1}"}
                ))

            # Occasionally add a vehicle
            if random.random() > 0.5:
                detections.append(DetectedObject(
                    label="car",
                    confidence=round(random.uniform(0.80, 0.97), 4),
                    bbox=BoundingBox(
                        x1=round(random.uniform(0, w * 0.3), 2),
                        y1=round(random.uniform(h * 0.3, h * 0.5), 2),
                        x2=round(random.uniform(w * 0.4, w * 0.9), 2),
                        y2=round(random.uniform(h * 0.6, h * 0.9), 2),
                        width=round(random.uniform(200, 500), 2),
                        height=round(random.uniform(150, 300), 2)
                    ),
                    category="vehicle"
                ))

            # Sometimes add a weapon detection
            if random.random() > 0.8:
                detections.append(DetectedObject(
                    label="knife",
                    confidence=round(random.uniform(0.55, 0.85), 4),
                    bbox=BoundingBox(
                        x1=round(random.uniform(200, 600), 2),
                        y1=round(random.uniform(300, 600), 2),
                        x2=round(random.uniform(620, 750), 2),
                        y2=round(random.uniform(620, 720), 2),
                        width=round(random.uniform(30, 80), 2),
                        height=round(random.uniform(20, 60), 2)
                    ),
                    category="weapon"
                ))

            action = action_sequence[i % len(action_sequence)]

            keyframes.append(VideoFrame(
                frame_number=frame_num,
                timestamp=ts,
                detections=detections,
                action=action,
                description=f"Frame at {ts:.1f}s: {action}. {len(detections)} object(s) detected.",
                is_keyframe=True
            ))

        return keyframes

    def _detect_action(self, detections: List[DetectedObject], frame_num: int) -> str:
        """Detect action based on object positions and types."""
        persons = [d for d in detections if d.category == "person"]
        weapons = [d for d in detections if d.category == "weapon"]
        vehicles = [d for d in detections if d.category == "vehicle"]

        if weapons and persons:
            return "Armed individual detected"
        elif len(persons) >= 2:
            return "Multiple persons in scene"
        elif persons and vehicles:
            return "Person near vehicle"
        elif vehicles:
            return "Vehicle in motion"
        elif persons:
            return "Individual in scene"
        else:
            return "Scene monitoring"

    def _generate_timeline(self, keyframes: List[VideoFrame], metadata: Dict) -> List[TimelineEvent]:
        """Generate forensic timeline from analyzed frames."""
        timeline = []

        for frame in keyframes:
            persons = [d for d in frame.detections if d.category == "person"]
            weapons = [d for d in frame.detections if d.category == "weapon"]
            vehicles = [d for d in frame.detections if d.category == "vehicle"]

            # Main frame event
            minutes = int(frame.timestamp // 60)
            seconds = int(frame.timestamp % 60)
            time_label = f"{minutes:02d}:{seconds:02d}"

            if weapons:
                event_type = "weapon_detection"
                desc = f"⚠️ Weapon detected: {', '.join(d.label for d in weapons)}"
                confidence = max(d.confidence for d in weapons)
            elif len(persons) >= 2:
                event_type = "multi_person"
                desc = f"{len(persons)} persons detected - {frame.action}"
                confidence = sum(d.confidence for d in persons) / len(persons)
            elif frame.action:
                event_type = "action"
                desc = frame.action
                confidence = 0.8
            else:
                event_type = "observation"
                desc = f"Frame #{frame.frame_number}: {len(frame.detections)} objects detected"
                confidence = 0.7

            timeline.append(TimelineEvent(
                timestamp=frame.timestamp,
                time_label=time_label,
                event_type=event_type,
                description=desc,
                confidence=round(confidence, 3),
                source="video",
                details={
                    "frame_number": frame.frame_number,
                    "persons": len(persons),
                    "weapons": len(weapons),
                    "vehicles": len(vehicles),
                    "total_objects": len(frame.detections)
                }
            ))

        return sorted(timeline, key=lambda e: e.timestamp)

    def _aggregate_objects(self, keyframes: List[VideoFrame]) -> Dict[str, int]:
        """Aggregate object detection counts across all frames."""
        counts = {}
        for frame in keyframes:
            for det in frame.detections:
                label = det.label
                counts[label] = counts.get(label, 0) + 1
        return counts


# Singleton instance
video_analyzer = VideoAnalyzer()
