"""
LocalVest — Backend Server Direct Launcher (Branch: testv1)
File: backend/start_server.py (Renamed from backend/run.py to avoid filename duplication with root run.py)
"""

import sys
import os
import webbrowser

# Khắc phục lỗi mã hóa Windows Console (UnicodeEncodeError)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)

import uvicorn

if __name__ == "__main__":
    print("=" * 75)
    print(">>> [LOCALVEST BACKEND SERVER] -- NHANH TESTV1 <<<")
    print("=" * 75)
    print("[!] LU U Y CU C KY QUAN TRONG VE CAC DUONG DAN LINK:")
    print("-> Ban CHI CO THE MO cac duong dan link ben duoi KHI TERMINAL NAY DANG CHAY!")
    print("-" * 75)
    print("[1] Giao dien Web Frontend:        http://127.0.0.1:8000/")
    print("[2] Tai lieu API Swagger (Docs):   http://127.0.0.1:8000/docs")
    print("[3] WebSocket Realtime Live Feed:  ws://127.0.0.1:8000/ws/live-feed")
    print("=" * 75)

    try:
        webbrowser.open("http://127.0.0.1:8000/docs")
    except Exception:
        pass

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
