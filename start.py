"""
MicroSetu - One-Click Application Launcher
Initializes dataset, trains/loads ML models, starts the FastAPI server,
and launches the interactive web application in your default browser.
"""

import sys
import time
import webbrowser
import uvicorn
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))

def main():
    print("=" * 70)
    print("  MicroSetu (Jan-Setu) | AI Underwriting & Smart POS for Informal Workers")
    print("=" * 70)
    print("Starting MicroSetu Intelligence Server...")
    
    # Auto-open browser after a short delay
    def open_browser():
        time.sleep(1.2)
        print("🌐 Opening MicroSetu Dashboard at http://127.0.0.1:8000 ...")
        webbrowser.open("http://127.0.0.1:8000")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    from server import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
