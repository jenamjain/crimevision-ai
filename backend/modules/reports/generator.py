"""
CrimeVision AI - PDF Report Generator
Generates professional forensic analysis reports in PDF format.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Any

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

from backend.config import REPORTS_DIR
from backend.models.schemas import (
    FusedEvidence, ImageAnalysisResult, AudioAnalysisResult, VideoAnalysisResult
)


class ForensicPDF(FPDF if FPDF_AVAILABLE else object):
    """Custom FPDF class with forensic report styling."""

    def __init__(self, case_id: str = ""):
        if FPDF_AVAILABLE:
            super().__init__()
            self.case_id = case_id
            self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 58, 138)
        self.cell(0, 10, "CRIMEVISION AI", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Forensic Intelligence Report", new_x="LMARGIN", new_y="NEXT", align="C")
        if self.case_id:
            self.cell(0, 6, f"Case ID: {self.case_id}", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_draw_color(30, 58, 138)
        self.set_line_width(0.5)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(8)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f"CrimeVision AI - Confidential Forensic Report", align="L")
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", align="R")

    @staticmethod
    def _clean(text: str) -> str:
        """Sanitize text to safe latin-1 characters for FPDF."""
        if not text:
            return ""
        replacements = {
            "•": "-", "⚠️": "[ALERT]", "🔗": "[LINK]", "🚨": "[ALERT]",
            "💡": "[TIP]", "📄": "[DOC]", "👤": "[PERSON]", "🎬": "[VIDEO]",
            "🎙️": "[AUDIO]", "📷": "[IMAGE]", "✅": "[OK]", "—": "-", "–": "-"
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        # Fallback to ascii ignore for any remaining high unicode
        return text.encode("latin-1", "ignore").decode("latin-1")

    def section_title(self, title: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 58, 138)
        self.cell(0, 8, self._clean(title), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(30, 58, 138)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def subsection_title(self, title: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(55, 65, 81)
        self.cell(0, 7, self._clean(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(55, 65, 81)
        self.multi_cell(0, 5, self._clean(text))
        self.ln(2)

    def bullet_point(self, text: str, indent: int = 10):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(55, 65, 81)
        self.set_x(15)
        self.multi_cell(180, 5, f"-  {self._clean(text)}")

    def alert_box(self, text: str, level: str = "info"):
        text = self._clean(text)
        colors = {
            "critical": (220, 38, 38),
            "warning": (234, 179, 8),
            "info": (59, 130, 246),
            "success": (34, 197, 94)
        }
        bg_colors = {
            "critical": (254, 226, 226),
            "warning": (254, 249, 195),
            "info": (219, 234, 254),
            "success": (220, 252, 231)
        }
        r, g, b = colors.get(level, colors["info"])
        br, bg, bb = bg_colors.get(level, bg_colors["info"])

        self.set_fill_color(br, bg, bb)
        self.set_draw_color(r, g, b)
        self.set_text_color(r, g, b)
        self.set_font("Helvetica", "B", 10)

        y_start = self.get_y()
        self.rect(10, y_start, 190, 12, style="DF")
        self.set_xy(15, y_start + 2)
        self.multi_cell(180, 5, text)
        self.ln(4)


class ReportGenerator:
    """Generates forensic PDF reports from analysis results."""

    def generate_report(
        self,
        case_id: str = None,
        image_results: List[ImageAnalysisResult] = None,
        audio_results: List[AudioAnalysisResult] = None,
        video_results: List[VideoAnalysisResult] = None,
        fused: FusedEvidence = None,
        output_filename: str = None
    ) -> str:
        """
        Generate a complete forensic PDF report.

        Returns:
            Path to the generated PDF file
        """
        if not FPDF_AVAILABLE:
            return self._generate_text_report(
                case_id, image_results, audio_results, video_results, fused, output_filename
            )

        image_results = image_results or []
        audio_results = audio_results or []
        video_results = video_results or []
        case_id = case_id or (fused.case_id if fused else f"CASE-{str(uuid.uuid4())[:8].upper()}")

        pdf = ForensicPDF(case_id=case_id)
        pdf.alias_nb_pages()
        pdf.add_page()

        # ─── Report Metadata ───
        pdf.section_title("1. Report Information")
        pdf.body_text(f"Case ID: {case_id}")
        pdf.body_text(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        pdf.body_text(f"Evidence Items: {len(image_results) + len(audio_results) + len(video_results)}")
        pdf.body_text(f"  - Images: {len(image_results)}")
        pdf.body_text(f"  - Audio Recordings: {len(audio_results)}")
        pdf.body_text(f"  - Video Recordings: {len(video_results)}")

        # ─── Risk Assessment ───
        risk = "low"
        if fused:
            risk = fused.risk_assessment
        else:
            for img in image_results:
                if img.scene.risk_level in ("critical", "high"):
                    risk = img.scene.risk_level
                    break

        risk_levels = {
            "critical": ("CRITICAL", "critical"),
            "high": ("HIGH", "warning"),
            "medium": ("MEDIUM", "info"),
            "low": ("LOW", "success")
        }
        label, level = risk_levels.get(risk, ("LOW", "success"))
        pdf.ln(3)
        pdf.alert_box(f"OVERALL RISK ASSESSMENT: {label}", level)

        # ─── Image Analysis ───
        if image_results:
            pdf.section_title("2. Image Analysis Results")
            for i, img in enumerate(image_results, 1):
                pdf.subsection_title(f"2.{i} {img.filename}")
                pdf.body_text(f"Evidence ID: {img.evidence_id}")
                pdf.body_text(f"Dimensions: {img.dimensions.get('width', 'N/A')} x {img.dimensions.get('height', 'N/A')}")
                pdf.body_text(f"Analysis Duration: {img.analysis_duration:.3f}s")
                pdf.body_text(f"Scene: {img.scene.description}")
                pdf.body_text(f"Environment: {img.scene.environment}")
                pdf.body_text(f"Risk Level: {img.scene.risk_level.upper()}")

                pdf.subsection_title("Detected Objects")
                for det in img.detected_objects:
                    pdf.bullet_point(
                        f"{det.label} ({det.category}) - Confidence: {det.confidence:.1%} "
                        f"at ({det.bbox.x1:.0f}, {det.bbox.y1:.0f})"
                    )

                if img.weapons_detected:
                    pdf.alert_box(
                        f"WEAPONS DETECTED: {', '.join(w.label for w in img.weapons_detected)}",
                        "critical"
                    )

                pdf.subsection_title("Forensic Notes")
                for note in img.forensic_notes:
                    pdf.bullet_point(note)
                pdf.ln(3)

        # ─── Audio Analysis ───
        if audio_results:
            section_num = 3 if image_results else 2
            pdf.section_title(f"{section_num}. Audio Analysis Results")
            for i, audio in enumerate(audio_results, 1):
                pdf.subsection_title(f"{section_num}.{i} {audio.filename}")
                pdf.body_text(f"Evidence ID: {audio.evidence_id}")
                pdf.body_text(f"Duration: {audio.duration:.1f} seconds")
                pdf.body_text(f"Speakers: {audio.speakers_count}")
                pdf.body_text(f"Language: {audio.language}")

                pdf.subsection_title("Transcript")
                transcript = audio.full_transcript[:1000]
                if len(audio.full_transcript) > 1000:
                    transcript += "... [truncated]"
                pdf.body_text(transcript)

                if audio.key_phrases:
                    pdf.subsection_title("Key Phrases")
                    for phrase in audio.key_phrases[:8]:
                        pdf.bullet_point(phrase)

                if audio.entities:
                    pdf.subsection_title("Extracted Entities")
                    for ent in audio.entities[:10]:
                        pdf.bullet_point(f"[{ent['type']}] {ent['value']}")

                pdf.subsection_title("Sentiment Analysis")
                for sentiment, score in audio.sentiment_summary.items():
                    pdf.bullet_point(f"{sentiment}: {score:.1%}")
                pdf.ln(3)

        # ─── Video Analysis ───
        if video_results:
            section_num = 2 + bool(image_results) + bool(audio_results)
            pdf.section_title(f"{section_num}. Video Analysis Results")
            for i, vid in enumerate(video_results, 1):
                pdf.subsection_title(f"{section_num}.{i} {vid.filename}")
                pdf.body_text(f"Evidence ID: {vid.evidence_id}")
                pdf.body_text(f"Duration: {vid.duration:.1f}s | FPS: {vid.fps:.0f} | Frames: {vid.total_frames}")
                pdf.body_text(f"Resolution: {vid.resolution.get('width', 'N/A')} x {vid.resolution.get('height', 'N/A')}")
                pdf.body_text(f"Persons Tracked: {vid.persons_tracked}")
                pdf.body_text(f"Keyframes Analyzed: {len(vid.keyframes)}")

                if vid.actions_detected:
                    pdf.subsection_title("Detected Actions")
                    for action in vid.actions_detected:
                        pdf.bullet_point(action)

                if vid.objects_summary:
                    pdf.subsection_title("Object Summary")
                    for obj, count in vid.objects_summary.items():
                        pdf.bullet_point(f"{obj}: {count} detection(s)")
                pdf.ln(3)

        # ─── Fusion / Intelligence ───
        if fused:
            section_num = 2 + bool(image_results) + bool(audio_results) + bool(video_results)
            pdf.section_title(f"{section_num}. Multimodal Fusion & Intelligence")

            if fused.key_findings:
                pdf.subsection_title("Key Findings")
                for finding in fused.key_findings:
                    pdf.bullet_point(finding)

            if fused.cross_modal_correlations:
                pdf.subsection_title("Cross-Modal Correlations")
                for corr in fused.cross_modal_correlations:
                    pdf.bullet_point(
                        f"[{corr.get('type', 'N/A')}] {corr.get('description', '')} "
                        f"(confidence: {corr.get('confidence', 0):.0%})"
                    )

            if fused.recommendations:
                pdf.subsection_title("Recommendations")
                for rec in fused.recommendations:
                    pdf.bullet_point(rec)

            if fused.intelligence_summary:
                pdf.subsection_title("Full Intelligence Summary")
                pdf.body_text(fused.intelligence_summary)

        # ─── Timeline ───
        timeline_events = []
        if fused and fused.unified_timeline:
            timeline_events = fused.unified_timeline
        elif video_results:
            for vid in video_results:
                timeline_events.extend(vid.timeline)

        if timeline_events:
            pdf.add_page()
            pdf.section_title("Forensic Timeline")
            timeline_events.sort(key=lambda e: e.timestamp)
            for ev in timeline_events[:30]:
                icon = "[!]" if "weapon" in ev.event_type.lower() else "[ ]"
                pdf.bullet_point(
                    f"{icon} {ev.time_label} [{ev.source}] {ev.description} "
                    f"(confidence: {ev.confidence:.0%})"
                )

        # ─── Save ───
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        output_filename = output_filename or f"report_{case_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = str(REPORTS_DIR / output_filename)
        pdf.output(output_path)

        return output_path

    def _generate_text_report(
        self, case_id, image_results, audio_results, video_results, fused, output_filename
    ) -> str:
        """Fallback: generate a plain text report if FPDF is not available."""
        image_results = image_results or []
        audio_results = audio_results or []
        video_results = video_results or []
        case_id = case_id or (fused.case_id if fused else f"CASE-{str(uuid.uuid4())[:8].upper()}")

        lines = [
            "=" * 60,
            "CRIMEVISION AI - FORENSIC INTELLIGENCE REPORT",
            "=" * 60,
            f"Case ID: {case_id}",
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Evidence Items: {len(image_results) + len(audio_results) + len(video_results)}",
            ""
        ]

        if fused:
            lines.append(fused.intelligence_summary)

        for img in image_results:
            lines.append(f"\n[IMAGE] {img.filename}")
            lines.append(f"  Scene: {img.scene.description}")
            for note in img.forensic_notes:
                lines.append(f"  {note}")

        for audio in audio_results:
            lines.append(f"\n[AUDIO] {audio.filename}")
            lines.append(f"  Transcript: {audio.full_transcript[:500]}")

        for vid in video_results:
            lines.append(f"\n[VIDEO] {vid.filename}")
            lines.append(f"  Duration: {vid.duration:.1f}s, Actions: {', '.join(vid.actions_detected[:5])}")

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        output_filename = output_filename or f"report_{case_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        output_path = str(REPORTS_DIR / output_filename)

        with open(output_path, "w") as f:
            f.write("\n".join(lines))

        return output_path


# Singleton instance
report_generator = ReportGenerator()
