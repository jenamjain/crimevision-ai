"""
CrimeVision AI - Image Analysis Module
Performs object detection, scene analysis, and forensic annotation on images.
"""
import os
import time
import uuid
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

from backend.models.schemas import (
    ImageAnalysisResult, DetectedObject, BoundingBox,
    SceneDescription
)
from backend.config import IMAGE_ANALYSIS_CONFIDENCE, WEAPON_CLASSES, VEHICLE_CLASSES


class ImageAnalyzer:
    """Analyzes crime scene images for objects, persons, weapons, and scene context."""

    # COCO class names for YOLO
    COCO_CLASSES = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
        'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
        'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
        'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
        'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
        'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
        'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
        'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
        'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
        'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
        'hair drier', 'toothbrush'
    ]

    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load YOLO model for object detection."""
        if YOLO_AVAILABLE:
            try:
                self.model = YOLO("yolov8n.pt")
                print("[ImageAnalyzer] YOLOv8 model loaded successfully.")
            except Exception as e:
                print(f"[ImageAnalyzer] Could not load YOLO model: {e}")
                self.model = None
        else:
            print("[ImageAnalyzer] YOLO not available. Using simulated detection.")

    def analyze(self, image_path: str, evidence_id: str = None) -> ImageAnalysisResult:
        """
        Perform full forensic image analysis.
        
        Args:
            image_path: Path to the image file
            evidence_id: Unique evidence identifier
            
        Returns:
            ImageAnalysisResult with all detections and scene analysis
        """
        start_time = time.time()
        evidence_id = evidence_id or str(uuid.uuid4())
        filename = os.path.basename(image_path)

        # Get image dimensions
        dimensions = self._get_dimensions(image_path)

        # Run object detection
        if self.model and CV2_AVAILABLE:
            detected_objects = self._detect_objects_yolo(image_path)
        else:
            detected_objects = self._simulate_detection(image_path, dimensions)

        # Categorize detections
        persons = [o for o in detected_objects if o.category == "person"]
        weapons = [o for o in detected_objects if o.category == "weapon"]
        vehicles = [o for o in detected_objects if o.category == "vehicle"]

        # Generate scene description
        scene = self._analyze_scene(image_path, detected_objects, dimensions)

        # Generate forensic notes
        forensic_notes = self._generate_forensic_notes(
            detected_objects, persons, weapons, vehicles, scene
        )

        duration = time.time() - start_time

        return ImageAnalysisResult(
            evidence_id=evidence_id,
            filename=filename,
            timestamp=datetime.utcnow(),
            dimensions=dimensions,
            detected_objects=detected_objects,
            persons_count=len(persons),
            weapons_detected=weapons,
            vehicles_detected=vehicles,
            scene=scene,
            forensic_notes=forensic_notes,
            analysis_duration=round(duration, 3)
        )

    def _get_dimensions(self, image_path: str) -> Dict[str, int]:
        """Get image dimensions."""
        if CV2_AVAILABLE:
            try:
                img = cv2.imread(image_path)
                if img is not None:
                    h, w = img.shape[:2]
                    return {"width": w, "height": h}
            except Exception:
                pass
        
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                return {"width": img.width, "height": img.height}
        except Exception:
            return {"width": 1920, "height": 1080}

    def _detect_objects_yolo(self, image_path: str) -> List[DetectedObject]:
        """Run YOLOv8 object detection."""
        detections = []
        try:
            results = self.model(image_path, conf=IMAGE_ANALYSIS_CONFIDENCE, verbose=False)
            
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                    
                for i in range(len(boxes)):
                    box = boxes[i]
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    label = self.COCO_CLASSES[cls_id] if cls_id < len(self.COCO_CLASSES) else f"class_{cls_id}"

                    # Categorize
                    category = "object"
                    if label == "person":
                        category = "person"
                    elif label in WEAPON_CLASSES or label in ["knife", "scissors", "baseball bat"]:
                        category = "weapon"
                    elif label in VEHICLE_CLASSES or label in ["car", "truck", "bus", "motorcycle", "bicycle"]:
                        category = "vehicle"

                    detections.append(DetectedObject(
                        label=label,
                        confidence=round(conf, 4),
                        bbox=BoundingBox(
                            x1=round(x1, 2), y1=round(y1, 2),
                            x2=round(x2, 2), y2=round(y2, 2),
                            width=round(x2 - x1, 2),
                            height=round(y2 - y1, 2)
                        ),
                        category=category,
                        attributes={"model": "yolov8n", "class_id": cls_id}
                    ))
        except Exception as e:
            print(f"[ImageAnalyzer] YOLO detection error: {e}")
            
        return detections

    def _simulate_detection(self, image_path: str, dimensions: Dict[str, int]) -> List[DetectedObject]:
        """Simulate object detection for demo purposes when YOLO is not available."""
        w = dimensions.get("width", 1920)
        h = dimensions.get("height", 1080)

        possible_detections = [
            {"label": "person", "category": "person", "conf_range": (0.75, 0.98)},
            {"label": "person", "category": "person", "conf_range": (0.65, 0.95)},
            {"label": "car", "category": "vehicle", "conf_range": (0.70, 0.96)},
            {"label": "knife", "category": "weapon", "conf_range": (0.55, 0.88)},
            {"label": "backpack", "category": "object", "conf_range": (0.60, 0.92)},
            {"label": "cell phone", "category": "object", "conf_range": (0.65, 0.90)},
            {"label": "bottle", "category": "object", "conf_range": (0.58, 0.87)},
            {"label": "chair", "category": "object", "conf_range": (0.72, 0.94)},
        ]

        # Select 3-6 random detections
        random.seed(hash(image_path) % 2**32)
        num_detections = random.randint(3, 6)
        selected = random.sample(possible_detections, min(num_detections, len(possible_detections)))

        detections = []
        for det in selected:
            x1 = random.uniform(0.05 * w, 0.6 * w)
            y1 = random.uniform(0.05 * h, 0.5 * h)
            bw = random.uniform(0.08 * w, 0.3 * w)
            bh = random.uniform(0.1 * h, 0.4 * h)
            conf = random.uniform(*det["conf_range"])

            detections.append(DetectedObject(
                label=det["label"],
                confidence=round(conf, 4),
                bbox=BoundingBox(
                    x1=round(x1, 2), y1=round(y1, 2),
                    x2=round(x1 + bw, 2), y2=round(y1 + bh, 2),
                    width=round(bw, 2), height=round(bh, 2)
                ),
                category=det["category"],
                attributes={"model": "simulated", "demo_mode": True}
            ))

        return detections

    def _analyze_scene(self, image_path: str, detections: List[DetectedObject], 
                       dimensions: Dict[str, int]) -> SceneDescription:
        """Analyze the overall scene context."""
        has_persons = any(d.category == "person" for d in detections)
        has_weapons = any(d.category == "weapon" for d in detections)
        has_vehicles = any(d.category == "vehicle" for d in detections)

        # Determine risk level
        if has_weapons and has_persons:
            risk = "critical"
        elif has_weapons:
            risk = "high"
        elif has_persons and len(detections) > 4:
            risk = "medium"
        else:
            risk = "low"

        # Generate description
        obj_labels = [d.label for d in detections]
        unique_labels = list(set(obj_labels))
        desc_parts = []

        person_count = sum(1 for d in detections if d.category == "person")
        if person_count > 0:
            desc_parts.append(f"{person_count} person(s) detected in the scene")
        if has_weapons:
            weapon_labels = [d.label for d in detections if d.category == "weapon"]
            desc_parts.append(f"Weapon(s) identified: {', '.join(set(weapon_labels))}")
        if has_vehicles:
            vehicle_labels = [d.label for d in detections if d.category == "vehicle"]
            desc_parts.append(f"Vehicle(s) present: {', '.join(set(vehicle_labels))}")
        
        other_objects = [d.label for d in detections if d.category == "object"]
        if other_objects:
            desc_parts.append(f"Other objects: {', '.join(set(other_objects))}")

        description = ". ".join(desc_parts) if desc_parts else "Scene analysis completed with no significant detections."

        # Determine environment heuristics
        outdoor_indicators = {"car", "truck", "bus", "motorcycle", "bicycle", "traffic light", "stop sign", "fire hydrant"}
        indoor_indicators = {"couch", "bed", "dining table", "tv", "refrigerator", "microwave", "toilet"}
        
        labels_set = set(obj_labels)
        if labels_set & outdoor_indicators:
            environment = "outdoor"
        elif labels_set & indoor_indicators:
            environment = "indoor"
        else:
            environment = "undetermined"

        tags = unique_labels + ([f"risk:{risk}"] if risk in ("high", "critical") else [])

        return SceneDescription(
            description=description,
            environment=environment,
            lighting="undetermined",
            risk_level=risk,
            tags=tags
        )

    def _generate_forensic_notes(self, all_detections, persons, weapons, vehicles, scene) -> List[str]:
        """Generate forensic notes based on analysis results."""
        notes = []
        
        notes.append(f"Total objects detected: {len(all_detections)}")
        
        if persons:
            notes.append(f"PERSONS: {len(persons)} individual(s) identified in the scene")
            for i, p in enumerate(persons):
                notes.append(
                    f"  - Person #{i+1}: Located at ({p.bbox.x1:.0f}, {p.bbox.y1:.0f}), "
                    f"confidence: {p.confidence:.1%}"
                )
        
        if weapons:
            notes.append(f"⚠️ WEAPONS ALERT: {len(weapons)} weapon(s) detected")
            for w in weapons:
                notes.append(
                    f"  - {w.label.upper()}: confidence {w.confidence:.1%}, "
                    f"location ({w.bbox.x1:.0f}, {w.bbox.y1:.0f})"
                )
        
        if vehicles:
            notes.append(f"VEHICLES: {len(vehicles)} vehicle(s) detected")
            for v in vehicles:
                notes.append(f"  - {v.label}: confidence {v.confidence:.1%}")
        
        notes.append(f"Scene Risk Assessment: {scene.risk_level.upper()}")
        notes.append(f"Environment: {scene.environment}")
        
        return notes


# Singleton instance
image_analyzer = ImageAnalyzer()
