"""
CrimeVision AI - Chat Interface Module
Natural language querying of forensic evidence using keyword-based
intelligence matching (no external LLM required).
"""
import re
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from backend.models.schemas import (
    ChatRequest, ChatResponse, ChatMessage,
    FusedEvidence, ImageAnalysisResult, AudioAnalysisResult, VideoAnalysisResult
)


class ChatInterface:
    """AI-powered chat interface for querying forensic evidence."""

    def __init__(self):
        self.conversation_history: List[ChatMessage] = []
        self.evidence_store: Dict[str, Any] = {
            "images": [],
            "audio": [],
            "video": [],
            "fused": []
        }

    def register_evidence(self, evidence_type: str, result: Any):
        """Register analysis results for chat querying."""
        if evidence_type in self.evidence_store:
            self.evidence_store[evidence_type].append(result)

    def clear_evidence(self):
        """Clear all stored evidence."""
        self.evidence_store = {
            "images": [], "audio": [], "video": [], "fused": []
        }

    def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat message and return an intelligent response
        based on analyzed evidence.
        """
        user_msg = request.message.strip()
        self.conversation_history.append(ChatMessage(
            role="user", content=user_msg
        ))

        # Determine the query intent
        intent = self._classify_intent(user_msg)

        # Generate response based on intent
        response_text, refs, confidence, suggestions = self._generate_response(
            intent, user_msg, request.case_id
        )

        self.conversation_history.append(ChatMessage(
            role="assistant", content=response_text, evidence_refs=refs
        ))

        return ChatResponse(
            response=response_text,
            evidence_refs=refs,
            confidence=confidence,
            suggestions=suggestions
        )

    def _classify_intent(self, message: str) -> str:
        """Classify the user's query intent."""
        msg = message.lower()

        if any(w in msg for w in ["weapon", "knife", "gun", "armed", "dangerous"]):
            return "weapons"
        elif any(w in msg for w in ["person", "people", "individual", "suspect", "who"]):
            return "persons"
        elif any(w in msg for w in ["vehicle", "car", "truck", "drive", "drove"]):
            return "vehicles"
        elif any(w in msg for w in ["said", "heard", "audio", "transcript", "spoke", "speech", "conversation"]):
            return "audio"
        elif any(w in msg for w in ["video", "footage", "recording", "frame", "action"]):
            return "video"
        elif any(w in msg for w in ["timeline", "sequence", "when", "time", "order"]):
            return "timeline"
        elif any(w in msg for w in ["risk", "danger", "threat", "assessment", "severity"]):
            return "risk"
        elif any(w in msg for w in ["summary", "overview", "report", "findings", "what happened"]):
            return "summary"
        elif any(w in msg for w in ["help", "can you", "what can"]):
            return "help"
        else:
            return "general"

    def _generate_response(self, intent: str, message: str, case_id: Optional[str]):
        """Generate response based on classified intent."""
        refs = []
        suggestions = []
        confidence = 0.0

        images = self.evidence_store["images"]
        audio = self.evidence_store["audio"]
        video = self.evidence_store["video"]
        fused = self.evidence_store["fused"]

        has_evidence = bool(images or audio or video or fused)

        if not has_evidence:
            return (
                "No evidence has been uploaded and analyzed yet. "
                "Please upload image, audio, or video evidence first, then I can answer your forensic queries.",
                [], 0.9,
                ["Upload an image for analysis", "Upload audio evidence", "Upload video footage"]
            )

        if intent == "help":
            return self._help_response()

        elif intent == "weapons":
            return self._weapons_response(images, video)

        elif intent == "persons":
            return self._persons_response(images, video)

        elif intent == "vehicles":
            return self._vehicles_response(images, video)

        elif intent == "audio":
            return self._audio_response(audio)

        elif intent == "video":
            return self._video_response(video)

        elif intent == "timeline":
            return self._timeline_response(video, audio, fused)

        elif intent == "risk":
            return self._risk_response(images, video, fused)

        elif intent == "summary":
            return self._summary_response(images, audio, video, fused)

        else:
            return self._general_response(images, audio, video, fused)

    def _help_response(self):
        text = (
            "🔍 **CrimeVision AI Chat Assistant**\n\n"
            "I can help you query your forensic evidence. Try asking:\n\n"
            "• \"Were any weapons detected?\"\n"
            "• \"How many people are in the scene?\"\n"
            "• \"What did the audio transcript say?\"\n"
            "• \"Show me the timeline of events\"\n"
            "• \"What is the risk assessment?\"\n"
            "• \"Give me a summary of findings\"\n"
            "• \"Were any vehicles detected?\""
        )
        return (text, [], 1.0, [
            "Were any weapons detected?",
            "Give me a summary of findings",
            "What is the risk assessment?"
        ])

    def _weapons_response(self, images, video):
        weapons = []
        refs = []

        for img in images:
            for w in img.weapons_detected:
                weapons.append(f"- **{w.label}** detected in `{img.filename}` (confidence: {w.confidence:.1%})")
                refs.append(img.evidence_id)

        for vid in video:
            for frame in vid.keyframes:
                for d in frame.detections:
                    if d.category == "weapon":
                        weapons.append(
                            f"- **{d.label}** detected in `{vid.filename}` at {frame.timestamp:.1f}s "
                            f"(confidence: {d.confidence:.1%})"
                        )
                        refs.append(vid.evidence_id)

        if weapons:
            text = f"⚠️ **Weapon Detections Found:**\n\n" + "\n".join(weapons)
            text += "\n\n🔴 This is a critical finding — recommend immediate review."
            return (text, list(set(refs)), 0.9, [
                "What is the risk assessment?",
                "Show the timeline",
                "How many people are in the scene?"
            ])
        else:
            return (
                "✅ No weapons were detected in the analyzed evidence.",
                [], 0.85,
                ["How many people are in the scene?", "Give me a summary"]
            )

    def _persons_response(self, images, video):
        parts = []
        refs = []
        total = 0

        for img in images:
            if img.persons_count > 0:
                parts.append(f"- `{img.filename}`: **{img.persons_count}** person(s) detected")
                total += img.persons_count
                refs.append(img.evidence_id)

        for vid in video:
            if vid.persons_tracked > 0:
                parts.append(f"- `{vid.filename}`: **{vid.persons_tracked}** person(s) tracked across frames")
                total += vid.persons_tracked
                refs.append(vid.evidence_id)

        if parts:
            text = f"👤 **Person Detections** (Total: {total}):\n\n" + "\n".join(parts)
            return (text, list(set(refs)), 0.85, [
                "Were any weapons detected?",
                "Show the timeline"
            ])
        else:
            return (
                "No persons were detected in the analyzed evidence.",
                [], 0.8,
                ["Give me a summary", "Were any vehicles detected?"]
            )

    def _vehicles_response(self, images, video):
        parts = []
        refs = []

        for img in images:
            for v in img.vehicles_detected:
                parts.append(f"- **{v.label}** in `{img.filename}` (confidence: {v.confidence:.1%})")
                refs.append(img.evidence_id)

        for vid in video:
            for label, count in vid.objects_summary.items():
                if label in ("car", "truck", "bus", "motorcycle", "bicycle"):
                    parts.append(f"- **{label}** detected {count} time(s) in `{vid.filename}`")
                    refs.append(vid.evidence_id)

        if parts:
            text = "🚗 **Vehicle Detections:**\n\n" + "\n".join(parts)
            return (text, list(set(refs)), 0.85, [
                "How many people are in the scene?",
                "Show the timeline"
            ])
        else:
            return (
                "No vehicles were detected in the analyzed evidence.",
                [], 0.8, ["Give me a summary"]
            )

    def _audio_response(self, audio):
        if not audio:
            return (
                "No audio evidence has been analyzed yet.",
                [], 0.9, ["Upload audio evidence"]
            )

        parts = []
        refs = []
        for a in audio:
            refs.append(a.evidence_id)
            parts.append(f"**Recording: `{a.filename}`** ({a.duration:.1f}s, {a.speakers_count} speaker(s))\n")
            if a.full_transcript:
                transcript = a.full_transcript[:500]
                parts.append(f"📝 Transcript:\n> {transcript}")
            if a.key_phrases:
                parts.append(f"\n🔑 Key Phrases: {', '.join(a.key_phrases[:5])}")
            if a.sentiment_summary:
                parts.append(f"\n💬 Sentiment: {a.sentiment_summary}")

        text = "🎙️ **Audio Analysis Results:**\n\n" + "\n\n".join(parts)
        return (text, refs, 0.85, [
            "What is the risk assessment?",
            "Show the timeline"
        ])

    def _video_response(self, video):
        if not video:
            return (
                "No video evidence has been analyzed yet.",
                [], 0.9, ["Upload video evidence"]
            )

        parts = []
        refs = []
        for v in video:
            refs.append(v.evidence_id)
            parts.append(
                f"**`{v.filename}`** — {v.duration:.1f}s, {v.fps:.0f} FPS, "
                f"{v.total_frames} frames, {len(v.keyframes)} keyframes analyzed"
            )
            if v.actions_detected:
                parts.append(f"  Actions: {', '.join(v.actions_detected[:5])}")
            if v.objects_summary:
                summary_str = ", ".join(f"{k}: {v2}" for k, v2 in v.objects_summary.items())
                parts.append(f"  Objects: {summary_str}")

        text = "🎬 **Video Analysis Results:**\n\n" + "\n".join(parts)
        return (text, refs, 0.85, [
            "Show the timeline",
            "Were any weapons detected?"
        ])

    def _timeline_response(self, video, audio, fused):
        events = []

        for f in fused:
            events.extend(f.unified_timeline)

        if not events:
            for v in video:
                events.extend(v.timeline)
            for a in audio:
                for seg in a.segments:
                    from backend.models.schemas import TimelineEvent
                    events.append(TimelineEvent(
                        timestamp=seg.start_time,
                        time_label=f"{int(seg.start_time // 60):02d}:{int(seg.start_time % 60):02d}",
                        event_type="speech",
                        description=f"[{seg.speaker_id}] {seg.text}",
                        confidence=seg.confidence,
                        source="audio"
                    ))

        if not events:
            return (
                "No timeline events available. Upload video or audio evidence to generate a timeline.",
                [], 0.8, ["Upload video evidence"]
            )

        events.sort(key=lambda e: e.timestamp)
        parts = []
        for ev in events[:15]:
            icon = "🔴" if "weapon" in ev.event_type.lower() else "🔵"
            parts.append(f"{icon} **{ev.time_label}** [{ev.source}] — {ev.description}")

        text = "📊 **Forensic Timeline:**\n\n" + "\n".join(parts)
        if len(events) > 15:
            text += f"\n\n_...and {len(events) - 15} more events._"

        return (text, [], 0.85, [
            "What is the risk assessment?",
            "Give me a summary"
        ])

    def _risk_response(self, images, video, fused):
        risk_level = "low"

        for f in fused:
            risk_level = f.risk_assessment

        if risk_level == "low":
            for img in images:
                if img.scene.risk_level in ("critical", "high"):
                    risk_level = img.scene.risk_level
                elif img.scene.risk_level == "medium" and risk_level == "low":
                    risk_level = "medium"

        icons = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
        icon = icons.get(risk_level, "⚪")

        text = f"{icon} **Overall Risk Assessment: {risk_level.upper()}**\n\n"

        if risk_level == "critical":
            text += "⚠️ Critical threat indicators detected. Immediate review by senior investigator recommended."
        elif risk_level == "high":
            text += "Elevated risk indicators found. Recommend prioritized investigation."
        elif risk_level == "medium":
            text += "Moderate risk indicators. Standard investigation procedures apply."
        else:
            text += "No significant threat indicators detected. Low risk assessment."

        return (text, [], 0.9, [
            "Were any weapons detected?",
            "Give me a summary"
        ])

    def _summary_response(self, images, audio, video, fused):
        parts = ["📋 **Evidence Summary:**\n"]

        parts.append(f"- **Images analyzed:** {len(images)}")
        parts.append(f"- **Audio recordings analyzed:** {len(audio)}")
        parts.append(f"- **Video recordings analyzed:** {len(video)}")

        total_persons = sum(i.persons_count for i in images)
        total_weapons = sum(len(i.weapons_detected) for i in images)

        if total_persons > 0:
            parts.append(f"- **Persons detected (images):** {total_persons}")
        if total_weapons > 0:
            parts.append(f"- ⚠️ **Weapons detected:** {total_weapons}")

        for a in audio:
            if a.key_phrases:
                parts.append(f"\n🎙️ Key phrases from `{a.filename}`: {', '.join(a.key_phrases[:3])}")

        for v in video:
            if v.actions_detected:
                parts.append(f"\n🎬 Actions in `{v.filename}`: {', '.join(v.actions_detected[:3])}")

        if fused:
            for f in fused:
                if f.key_findings:
                    parts.append("\n🔍 **Key Findings:**")
                    for finding in f.key_findings[:5]:
                        parts.append(f"  • {finding}")

        text = "\n".join(parts)
        return (text, [], 0.85, [
            "Were any weapons detected?",
            "Show the timeline",
            "What is the risk assessment?"
        ])

    def _general_response(self, images, audio, video, fused):
        text = (
            "I can help you analyze your forensic evidence. Here are some things you can ask:\n\n"
            "• **Weapons**: \"Were any weapons detected?\"\n"
            "• **People**: \"How many people are in the scene?\"\n"
            "• **Audio**: \"What did the witnesses say?\"\n"
            "• **Timeline**: \"Show me the timeline of events\"\n"
            "• **Risk**: \"What is the risk assessment?\"\n"
            "• **Summary**: \"Give me an overview of findings\""
        )
        return (text, [], 0.5, [
            "Give me a summary of findings",
            "Were any weapons detected?",
            "Show the timeline"
        ])


# Singleton instance
chat_interface = ChatInterface()
