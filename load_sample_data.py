"""
CrimeVision AI - Sample Data Loader & Auto-Demo Script
Automatically uploads and analyzes sample forensic images, audio, and video,
then performs multimodal fusion and generates a court-ready report.
"""
import os
import requests

API_BASE = "http://localhost:8000/api"

SAMPLE_FILES = [
    ("sample_data/images/cctv_suspect_vehicle.jpg", "image/jpeg", "CCTV Camera 04 Night Surveillance"),
    ("sample_data/images/weapon_evidence_marker.jpg", "image/jpeg", "Forensic marker #1 knife evidence"),
    ("sample_data/audio/911_dispatch_call.wav", "audio/wav", "911 Dispatch Emergency Call"),
    ("sample_data/video/cctv_alley_monitoring.mp4", "video/mp4", "CCTV Alley Motion Tracking Video")
]

def main():
    print("==================================================")
    print("🔍 CrimeVision AI - Loading Sample Forensic Data")
    print("==================================================\n")

    # 1. Health check
    try:
        res = requests.get(f"{API_BASE}/health")
        if res.status_code != 200:
            print("❌ Server is not responding. Run `python run.py` first!")
            return
    except Exception:
        print("❌ Server is offline. Please start it using: python run.py")
        return

    # 2. Upload and analyze each evidence file
    uploaded_ids = []
    for filepath, mime, notes in SAMPLE_FILES:
        if not os.path.exists(filepath):
            print(f"⚠️ File missing: {filepath}")
            continue

        filename = os.path.basename(filepath)
        print(f"📥 Uploading {filename}...")

        with open(filepath, "rb") as f:
            res = requests.post(
                f"{API_BASE}/evidence/upload",
                files={"file": (filename, f, mime)},
                data={"notes": notes, "tags": "sample,demo"}
            )

        if res.status_code == 200:
            ev_id = res.json()["data"]["evidence_id"]
            uploaded_ids.append(ev_id)
            print(f"   -> Uploaded! (ID: {ev_id})")
            
            # Trigger analysis
            print(f"   -> Analyzing with Forensic AI...")
            analyze_res = requests.post(f"{API_BASE}/analyze/{ev_id}")
            if analyze_res.status_code == 200:
                print(f"   ✅ Analysis Complete!")
            else:
                print(f"   ⚠️ Analysis error: {analyze_res.text}")
        else:
            print(f"   ❌ Upload failed: {res.text}")

    # 3. Fuse evidence
    print("\n🧠 Running Multimodal Evidence Fusion...")
    fuse_res = requests.post(f"{API_BASE}/fusion/fuse")
    if fuse_res.status_code == 200:
        case = fuse_res.json()["data"]
        print(f"✅ Multimodal Synthesis Completed!")
        print(f"   • Case ID: {case['case_id']}")
        print(f"   • Threat Assessment: {case['risk_assessment'].upper()}")
        print(f"   • Corroborations Found: {len(case['cross_modal_correlations'])}")
    else:
        print(f"⚠️ Fusion note: {fuse_res.text}")

    # 4. Generate PDF Report
    print("\n📄 Generating Court-Ready Forensic PDF Report...")
    rep_res = requests.post(f"{API_BASE}/reports/generate")
    if rep_res.status_code == 200:
        rep_data = rep_res.json()["data"]
        print(f"✅ Report Generated: {rep_data['filename']}")
        print(f"   Download URL: http://localhost:8000{rep_data['download_url']}")

    print("\n🎉 All sample evidence successfully loaded!")
    print("👉 Open your browser at: http://localhost:8000 to interact with the dashboard!")

if __name__ == "__main__":
    main()
