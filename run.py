"""
CrimeVision AI - Runner Script
Run this script to start the local development server:
    python run.py
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from backend.config import HOST, PORT

if __name__ == "__main__":
    print(f"\n========================================================")
    print(f"🛡️  CrimeVision AI - Multimodal Forensic Intelligence")
    print(f"🚀  Running on: http://localhost:{PORT}")
    print(f"📖  Swagger API: http://localhost:{PORT}/docs")
    print(f"========================================================\n")
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
