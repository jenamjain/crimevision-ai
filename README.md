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

## 🚀 Quick Start (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python run.py

# 3. (Optional) In a separate terminal, auto-load sample forensic evidence:
python load_sample_data.py
```

Open `http://localhost:8000` in your browser.
Interactive Swagger API documentation is available at `http://localhost:8000/docs`.

---

## 🐳 Docker Deployment

To build and run as a self-contained container:

```bash
# Using Docker Compose
docker compose up -d

# Or build manually
docker build -t crimevision-ai .
docker run -p 8000:8000 crimevision-ai
```

---

## ☁️ Cloud Deployment (1-Click)

### Option A: Render.com (Recommended Free Cloud Hosting)
1. Fork or push to your GitHub: `https://github.com/jenamjain/crimevision-ai`
2. Go to [render.com](https://render.com) -> **New +** -> **Blueprint**
3. Select your repository `crimevision-ai`. Render will automatically detect `render.yaml` and deploy your web service!

### Option B: Railway.app
1. Go to [railway.app](https://railway.app) -> **New Project**
2. Choose **Deploy from GitHub repo** and select `crimevision-ai`
3. Railway automatically detects `Procfile` / `Dockerfile` and deploys your live URL.

---

## 📋 Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Computer Vision**: OpenCV, YOLOv8 (Ultralytics)
- **Audio**: OpenAI Whisper, SpeechRecognition, PyDub
- **NLP**: spaCy, Transformers, Sentence-Transformers
- **Reports**: FPDF2, ReportLab
- **Frontend**: HTML5, Vanilla CSS3 (Dark-Mode Glassmorphism), Vanilla JS

