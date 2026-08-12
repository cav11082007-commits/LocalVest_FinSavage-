"""
LocalVest — Backend Server Direct Launcher
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
    print(">>> [LOCALVEST BACKEND SERVER] <<<")
    print("=" * 75)
    print("[!] Lưu ý quan trọng về dường dẫn link:")
    print("-> Bạn chỉ có thể mở đường dẫn link bên dưới khi Terminal này đang chạy")
    print("-" * 75)
    print("[1] Giao diện Web Frontend:        http://127.0.0.1:8000/")
    print("[2] Tài liệu API Swagger (Docs):   http://127.0.0.1:8000/docs")
    print("[3] WebSocket Realtime Live Feed:  ws://127.0.0.1:8000/ws/live-feed")
    print("=" * 75)

    try:
        webbrowser.open("http://127.0.0.1:8000/docs")
    except Exception:
        pass

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
