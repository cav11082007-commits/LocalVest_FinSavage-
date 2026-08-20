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
    print(">>> [LOCALVEST SYSTEM LAUNCHER] -- CHẠY THỬ NGHIỆM HỆ THỐNG <<<")
    print("=" * 75)
    print("[!]LƯU Ý QUAN TRỌNG VỀ ĐƯỜNG DẪN LINK:")
    print("-> BẠN CHỈ CÓ THỂ MỞ CÁC ĐƯỜNG LINK BÊN DƯỚI ĐÂY KHI CỬA SỔ NÀY ĐANG MỞ!")
    print("-" * 75)
    print("[1] Giao dien Web Frontend:        http://127.0.0.1:8000/")
    print("[2] Trang đăng nhập & KYC :        http://127.0.0.1:8000/login_page.html")
    print("[3] Tài Liệu API SWAGGER  : http://127.0.0.1:8000/docs")
    print("[4] WebSocket Realtime Live Feed:  ws://127.0.0.1:8000/ws/live-feed")
    print("=" * 75)
    print("[+] Đang tự động mở cửa sổ trình duyệt cho bạn...")
    print("=" * 75)

    try:
        webbrowser.open("http://127.0.0.1:8000/docs")
        webbrowser.open("http://127.0.0.1:8000/")
    except Exception:
        pass

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
