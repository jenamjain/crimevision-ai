"""
CrimeVision AI - Multimodal Fusion Engine
Correlates evidence across image, audio, and video modalities
to generate unified intelligence reports and timelines.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from backend.models.schemas import (
    FusedEvidence, TimelineEvent,
    ImageAnalysisResult, AudioAnalysisResult, VideoAnalysisResult
)


class FusionEngine:
    """Fuses multimodal evidence into unified forensic intelligence."""

    def fuse(
        self,
        image_results: List[ImageAnalysisResult] = None,
        audio_results: List[AudioAnalysisResult] = None,
        video_results: List[VideoAnalysisResult] = None,
        case_id: str = None
    ) -> FusedEvidence:
        """
        Fuse evidence from multiple modalities into unified intelligence.
        
        Args:
            image_results: List of image analysis results
            audio_results: List of audio analysis results
            video_results: List of video analysis results
            case_id: Existing case ID or auto-generated
            
        Returns:
            FusedEvidence with unified timeline and intelligence
        """
        image_results = image_results or []
        audio_results = audio_results or []
        video_results = video_results or []

        case_id = case_id or f"CASE-{str(uuid.uuid4())[:8].upper()}"

        # Collect all evidence IDs
        evidence_items = (
            [r.evidence_id for r in image_results] +
            [r.evidence_id for r in audio_results] +
            [r.evidence_id for r in video_results]
        )

        # Build unified timeline
        unified_timeline = self._build_unified_timeline(
            image_results, audio_results, video_results
        )

        # Find cross-modal correlations
        correlations = self._find_correlations(
            image_results, audio_results, video_results
        )

        # Generate intelligence summary
        summary = self._generate_intelligence_summary(
            image_results, audio_results, video_results, correlations
        )

        # Assess risk
        risk = self._assess_overall_risk(
            image_results, audio_results, video_results
        )

        # Key findings
        findings = self._extract_key_findings(
            image_results, audio_results, video_results, correlations
        )

        # Recommendations
        recommendations = self._generate_recommendations(
            findings, risk, correlations
        )

        return FusedEvidence(
            case_id=case_id,
            created_at=datetime.utcnow(),
            evidence_items=evidence_items,
            unified_timeline=unified_timeline,
            cross_modal_correlations=correlations,
            intelligence_summary=summary,
            risk_assessment=risk,
            key_findings=findings,
            recommendations=recommendations
        )

    def _build_unified_timeline(
        self,
        image_results: List[ImageAnalysisResult],
        audio_results: List[AudioAnalysisResult],
        video_results: List[VideoAnalysisResult]
    ) -> List[TimelineEvent]:
        """Merge all timelines into one chronological sequence."""
        events = []

        # Image events (point-in-time analysis)
        for img in image_results:
            risk = img.scene.risk_level
            event_type = "weapon_detection" if img.weapons_detected else "scene_analysis"
            
            events.append(TimelineEvent(
                timestamp=0,
                time_label=img.timestamp.strftime("%H:%M:%S"),
                event_type=event_type,
                description=img.scene.description,
                confidence=max((d.confidence for d in img.detected_objects), default=0),
                source="image",
                evidence_id=img.evidence_id,
                details={
                    "filename": img.filename,
                    "persons": img.persons_count,
                    "weapons": len(img.weapons_detected),
                    "risk_level": risk
                }
            ))

        # Audio events (from transcript segments)
        for audio in audio_results:
            for seg in audio.segments:
                events.append(TimelineEvent(
                    timestamp=seg.start_time,
                    time_label=f"{int(seg.start_time // 60):02d}:{int(seg.start_time % 60):02d}",
                    event_type="speech",
                    description=f"[{seg.speaker_id}] {seg.text}",
                    confidence=seg.confidence,
                    source="audio",
                    evidence_id=audio.evidence_id,
                    details={
                        "speaker": seg.speaker_id,
                        "sentiment": seg.sentiment,
                        "emotion": seg.emotion,
                        "duration": round(seg.end_time - seg.start_time, 2)
                    }
                ))

        # Video events
        for vid in video_results:
            events.extend(vid.timeline)

        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)

        return events

    def _find_correlations(
        self,
        image_results: List[ImageAnalysisResult],
        audio_results: List[AudioAnalysisResult],
        video_results: List[VideoAnalysisResult]
    ) -> List[Dict[str, Any]]:
        """Find cross-modal evidence correlations."""
        correlations = []

        # Collect all mentioned entities
        image_objects = set()
        for img in image_results:
            for det in img.detected_objects:
                image_objects.add(det.label.lower())

        audio_entities = set()
        for audio in audio_results:
            for ent in audio.entities:
                audio_entities.add(ent["value"].lower())

        video_objects = set()
        for vid in video_results:
            for label, count in vid.objects_summary.items():
                video_objects.add(label.lower())

        # Cross-reference: Objects seen in images that are mentioned in audio
        visual_audio_overlap = image_objects & audio_entities
        if visual_audio_overlap:
            correlations.append({
                "type": "visual_audio_match",
                "description": f"Objects detected in images and mentioned in audio transcripts: {', '.join(visual_audio_overlap)}",
                "matched_items": list(visual_audio_overlap),
                "confidence": 0.85,
                "modalities": ["image", "audio"]
            })

        # Cross-reference: Objects in images and video
        visual_video_overlap = image_objects & video_objects
        if visual_video_overlap:
            correlations.append({
                "type": "visual_consistency",
                "description": f"Consistent object detections across image and video evidence: {', '.join(visual_video_overlap)}",
                "matched_items": list(visual_video_overlap),
                "confidence": 0.90,
                "modalities": ["image", "video"]
            })

        # Person count correlation
        img_persons = sum(img.persons_count for img in image_results)
        vid_persons = sum(vid.persons_tracked for vid in video_results)
        if img_persons > 0 and vid_persons > 0:
            correlations.append({
                "type": "person_tracking",
                "description": f"Person detections: {img_persons} in images, {vid_persons} tracked in video",
                "confidence": 0.80,
                "modalities": ["image", "video"]
            })

        # Weapon correlation across modalities
        img_weapons = set()
        for img in image_results:
            for w in img.weapons_detected:
                img_weapons.add(w.label.lower())

        audio_weapon_refs = set()
        for audio in audio_results:
            for ent in audio.entities:
                if ent["type"] == "WEAPON":
                    audio_weapon_refs.add(ent["value"].lower())

        weapon_overlap = img_weapons | audio_weapon_refs
        if len(weapon_overlap) > 0 and (img_weapons and audio_weapon_refs):
            correlations.append({
                "type": "weapon_corroboration",
                "description": f"Weapon evidence corroborated across modalities: visual ({', '.join(img_weapons)}), verbal ({', '.join(audio_weapon_refs)})",
                "confidence": 0.92,
                "modalities": ["image", "audio"],
                "critical": True
            })

        return correlations

    def _generate_intelligence_summary(
        self,
        image_results: List[ImageAnalysisResult],
        audio_results: List[AudioAnalysisResult],
        video_results: List[VideoAnalysisResult],
        correlations: List[Dict]
    ) -> str:
        """Generate comprehensive intelligence summary."""
        parts = []
        
        parts.append("=== CRIMEVISION AI - FORENSIC INTELLIGENCE SUMMARY ===\n")

        # Evidence overview
        total_evidence = len(image_results) + len(audio_results) + len(video_results)
        parts.append(f"Total evidence items analyzed: {total_evidence}")
        parts.append(f"  - Images: {len(image_results)}")
        parts.append(f"  - Audio recordings: {len(audio_results)}")
        parts.append(f"  - Video recordings: {len(video_results)}")

        # Image findings
        if image_results:
            total_persons = sum(img.persons_count for img in image_results)
            total_weapons = sum(len(img.weapons_detected) for img in image_results)
            parts.append(f"\n[IMAGE ANALYSIS]")
            parts.append(f"  Persons identified: {total_persons}")
            parts.append(f"  Weapons detected: {total_weapons}")
            for img in image_results:
                parts.append(f"  Scene ({img.filename}): {img.scene.description}")

        # Audio findings
        if audio_results:
            parts.append(f"\n[AUDIO ANALYSIS]")
            for audio in audio_results:
                parts.append(f"  Recording: {audio.filename} ({audio.duration:.1f}s)")
                parts.append(f"  Speakers identified: {audio.speakers_count}")
                if audio.key_phrases:
                    parts.append(f"  Key phrases: {'; '.join(audio.key_phrases[:5])}")
                parts.append(f"  Sentiment: {audio.sentiment_summary}")

        # Video findings
        if video_results:
            parts.append(f"\n[VIDEO ANALYSIS]")
            for vid in video_results:
                parts.append(f"  Recording: {vid.filename} ({vid.duration:.1f}s)")
                parts.append(f"  Persons tracked: {vid.persons_tracked}")
                parts.append(f"  Actions: {', '.join(vid.actions_detected[:5])}")

        # Correlations
        if correlations:
            parts.append(f"\n[CROSS-MODAL CORRELATIONS]")
            for corr in correlations:
                parts.append(f"  • {corr['description']} (confidence: {corr.get('confidence', 0):.0%})")

        return "\n".join(parts)

    def _assess_overall_risk(
        self,
        image_results: List[ImageAnalysisResult],
        audio_results: List[AudioAnalysisResult],
        video_results: List[VideoAnalysisResult]
    ) -> str:
        """Determine overall risk assessment."""
        risk_scores = {
            "low": 1, "medium": 2, "high": 3, "critical": 4
        }
        max_risk = 1

        # Image risk
        for img in image_results:
            max_risk = max(max_risk, risk_scores.get(img.scene.risk_level, 1))

        # Audio risk (negative sentiment)
        for audio in audio_results:
            neg = audio.sentiment_summary.get("negative", 0)
            if neg > 0.5:
                max_risk = max(max_risk, 3)
            elif neg > 0.3:
                max_risk = max(max_risk, 2)

        # Video risk
        for vid in video_results:
            weapon_count = vid.objects_summary.get("knife", 0) + vid.objects_summary.get("gun", 0)
            if weapon_count > 0:
                max_risk = max(max_risk, 4)

        risk_map = {1: "low", 2: "medium", 3: "high", 4: "critical"}
        return risk_map.get(max_risk, "low")

    def _extract_key_findings(
        self,
        image_results: List[ImageAnalysisResult],
        audio_results: List[AudioAnalysisResult],
        video_results: List[VideoAnalysisResult],
        correlations: List[Dict]
    ) -> List[str]:
        """Extract key forensic findings."""
        findings = []

        # Critical: Weapon detections
        for img in image_results:
            if img.weapons_detected:
                weapons = ", ".join(w.label for w in img.weapons_detected)
                findings.append(f"⚠️ CRITICAL: Weapon(s) detected in image evidence ({img.filename}): {weapons}")

        # Person count
        total_persons = sum(img.persons_count for img in image_results)
        if total_persons > 0:
            findings.append(f"Total of {total_persons} person(s) identified across image evidence")

        # Audio key phrases
        for audio in audio_results:
            if audio.key_phrases:
                findings.append(f"Key witness statements from {audio.filename}: '{audio.key_phrases[0]}'")

        # Video actions
        for vid in video_results:
            if vid.actions_detected:
                findings.append(f"Video analysis ({vid.filename}) detected actions: {', '.join(vid.actions_detected[:3])}")

        # Correlation findings
        for corr in correlations:
            if corr.get("critical"):
                findings.append(f"🔗 CORROBORATED: {corr['description']}")

        return findings

    def _generate_recommendations(
        self,
        findings: List[str],
        risk: str,
        correlations: List[Dict]
    ) -> List[str]:
        """Generate investigative recommendations."""
        recommendations = []

        if risk in ("high", "critical"):
            recommendations.append("PRIORITY: Immediate review by senior investigator recommended due to high risk assessment")
            recommendations.append("Secure and preserve all original evidence files")

        if any("weapon" in f.lower() for f in findings):
            recommendations.append("Cross-reference weapon detections with local crime databases")
            recommendations.append("Request ballistics or forensic lab analysis for identified weapons")

        if any("person" in f.lower() for f in findings):
            recommendations.append("Run facial recognition against person-of-interest databases")
            recommendations.append("Attempt to identify all individuals present at the scene")

        if correlations:
            recommendations.append("Review cross-modal correlations for investigative leads")

        recommendations.append("Generate comprehensive PDF report for case file documentation")
        recommendations.append("Schedule follow-up analysis with additional evidence if available")

        return recommendations


# Singleton instance
fusion_engine = FusionEngine()
