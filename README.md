# CrimeVision AI – Intelligent Multimodal Forensic Analysis Platform

An advanced forensic intelligence system that automates crime scene reconstruction and digital evidence analysis using multimodal AI.

## 🔍 Features

- **Image Analysis** – Object detection (people, weapons, vehicles), scene classification
- **Audio Analysis** – Speech-to-text transcription, speaker identification, sentiment analysis
- **Video Analysis** – Frame-by-frame analysis, action recognition, timeline generation
- **Multimodal Fusion** – Cross-modal evidence correlation and unified timeline
- **AI Chat Interface** – Natural language querying of forensic evidence
- **PDF Reports** – Professional forensic report generation
- **Modern Dashboard** – Interactive evidence management UI

## 🏗️ Architecture

```
crimevision-ai/
├── backend/
│   ├── main.py              # FastAPI application entry
│   ├── config.py             # Configuration settings
│   ├── models/               # Data models
│   ├── modules/
│   │   ├── image_analysis/   # Image processing & detection
│   │   ├── audio_analysis/   # Audio transcription & NLP
│   │   ├── video_analysis/   # Video processing & timeline
│   │   ├── fusion/           # Multimodal fusion engine
│   │   ├── chat/             # AI chat interface
│   │   └── reports/          # PDF report generator
│   ├── api/                  # REST API routes
│   └── utils/                # Utility functions
├── frontend/
│   ├── index.html            # Main dashboard
│   ├── css/                  # Stylesheets
│   └── js/                   # JavaScript modules
├── uploads/                  # Uploaded evidence files
├── reports/                  # Generated reports
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python backend/main.py
```

Open `http://localhost:8000` in your browser.

## 📋 Tech Stack

- **Backend**: FastAPI (Python 3.8+)
- **Computer Vision**: OpenCV, YOLOv8 (Ultralytics)
- **Audio**: OpenAI Whisper, SpeechRecognition
- **NLP**: spaCy, Transformers, Sentence-Transformers
- **Reports**: FPDF2, ReportLab
- **Frontend**: HTML5, CSS3, Vanilla JS
