"""
LocalVest — Root Level One-Click Launcher (Branch: testv1)
Chạy 1 lệnh duy nhất để khởi động toàn bộ Frontend + Backend API + Swagger Docs + WebSocket Live Feed!
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

# Thêm thư mục backend vào sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

import uvicorn

if __name__ == "__main__":
    print("=" * 75)
    print(">>> [LOCALVEST SYSTEM LAUNCHER] -- NHANH TESTV1 <<<")
    print("=" * 75)
    print("[!] LU U Y CU C KY QUAN TRONG VE CAC DUONG DAN LINK:")
    print("-> Ban CHI CO THE MO cac duong dan link ben duoi KHI CUA SO NAY DANG CHAY!")
    print("-> Neu tat cua so Terminal nay, cac link http://127.0.0.1:8000 se bao loi ket noi.")
    print("-" * 75)
    print("[1] Giao dien Web Frontend:        http://127.0.0.1:8000/")
    print("[2] Trang Dang Nhap & KYC:        http://127.0.0.1:8000/login_page.html")
    print("[3] Tai lieu API Swagger (Docs): http://127.0.0.1:8000/docs")
    print("[4] WebSocket Realtime Live Feed:  ws://127.0.0.1:8000/ws/live-feed")
    print("=" * 75)
    print("[+] Dang tu dong mo trinh duyet web cho ban...")
    print("=" * 75)

    try:
        webbrowser.open("http://127.0.0.1:8000/docs")
        webbrowser.open("http://127.0.0.1:8000/")
    except Exception:
        pass

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
