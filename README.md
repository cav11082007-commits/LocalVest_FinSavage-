# 🏆 LocalVest — Nền Tảng Gọi Vốn Cộng Đồng Minh Bạch (MVP Vòng 2) — Nhánh testv1

> **LocalVest** là nền tảng gọi vốn minh bạch kết hợp ký quỹ dòng tiền (Escrow), kiểm tra an toàn bằng AI (AI-Fraud Shield) và bản đồ tác động cộng đồng theo bán kính 3-5km (Hyperlocal Geofencing).

---

## ⚠️ GHI CHÚ QUAN TRỌNG: VỀ CÁC ĐƯỜNG DẪN LINK (SWAGGER / WEBSOCKET)

> [!WARNING]
> Nếu bạn bấm vào link `http://127.0.0.1:8000/docs` hoặc `ws://127.0.0.1:8000/ws/live-feed` mà trình duyệt báo lỗi **"Không thể kết nối / Trang web không hoạt động"**:
> 
> **NGUYÊN NHÂN**: Do Server Python chưa được khởi động trong Terminal nên cổng `8000` chưa lắng nghe.
> 
> **CÁCH MỞ LINK THÀNH CÔNG**:
> 1. Mở Terminal tại thư mục `LocalVest` và gõ:
>    ```bash
>    python run.py
>    ```
> 2. Giữ nguyên cửa sổ Terminal đó đang chạy, hệ thống sẽ tự động mở trình duyệt web lên cho bạn. Lúc này các đường dẫn link sẽ truy cập được 100%!

---

## 🏛️ TỔNG QUAN KIẾN TRÚC HỆ THỐNG (SYSTEM DESIGN)

Hệ thống được thiết kế theo mô hình **Modular Monolith (Python FastAPI)** trên nhánh `testv1`, tối ưu hóa cho chi phí vận hành **0 VNĐ**:

```
                              [ LocalVest Frontend ]
                      (HTML5 / CSS3 / Vanilla JS - Giữ Nguyên Tên File Gốc)
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
        [ HTTP REST API (FastAPI) ]            [ Realtime WebSocket ]
        • Auth & KYC Service                   • Live Feed dòng tiền
        • Campaign State Machine               • Cập nhật mốc giải ngân
        • Escrow & Ledger Service
        • Location 3-5km Service
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
 [ Supabase PostgreSQL ]   [ Async AI Worker ]
 (PostGIS Spatial Index)  (Anti-Fraud Anomaly)
```

---

## 📂 CẤU TRÚC THƯ MỤC CHUYÊN NGHIỆP (ENTERPRISE FOLDER STRUCTURE)

Toàn bộ tên file giao diện frontend được **giữ nguyên 100%** để đảm bảo tham chiếu liên kết giữa các trang web hoạt động hoàn hảo:

```text
LocalVest/
├── run.py                        # Launcher 1-Click duy nhất (python run.py)
├── README.md                     # Tài liệu thiết kế hệ thống & hướng dẫn chạy
├── backend.md                    # Tài liệu ghi chú API & giải thích đường dẫn link
├── backend/                      # Python FastAPI Enterprise Backend
│   ├── main.py                   # App chính, Phục vụ tĩnh Frontend & API Routers
│   ├── run.py                    # Script chạy backend folder
│   ├── requirements.txt          # Khai báo các thư viện Python
│   └── app/
│       ├── config.py             # Cấu hình môi trường & JWT Settings
│       ├── api/                  # 8 API Routers tương ứng 8 dịch vụ Vòng 2
│       │   ├── auth.py           # 1. Auth, RBAC & Hồ sơ KYC
│       │   ├── campaigns.py      # 2. Campaign CRUD & State Machine
│       │   ├── payments.py       # 3. MoMo Webhook & Sổ cái Escrow
│       │   ├── location.py       # 4. Location Service 3-5km Radius
│       │   ├── ai_flag.py        # 5. AI-Flag Anomaly Detection Result
│       │   └── admin.py          # 6. Admin Phê duyệt & Giải ngân
│       ├── core/
│       │   └── security.py       # Xử lý JWT Token & Phân quyền
│       ├── schemas/
│       │   └── schemas.py        # Pydantic DTO Contract Models
│       ├── services/
│       │   ├── store.py          # Hybrid Store (Memory / PostgreSQL)
│       │   ├── ai_worker.py      # Background Task AI Fraud Checker
│       │   └── realtime.py       # Connection Manager WebSocket Live Feed
│       └── database/
│           └── schema.sql        # DDL PostgreSQL + PostGIS Extension
└── frontend/                     # Giữ nguyên 100% tên file gốc
    ├── index.html                # Trang chuyển hướng chính
    ├── login_page.html           # Đăng nhập / Đăng ký & KYC
    ├── home.html                 # Khám phá dự án quanh tôi
    ├── project.html              # Chi tiết dự án & Cột mốc giải ngân
    ├── submit_project.html       # Đăng dự án mới
    ├── checkout.html             # Đóng góp ký quỹ Escrow (MoMo/VNPay)
    ├── dashboard.html            # Bảng điều khiển dòng tiền minh bạch
    ├── admin.html                # Quản trị viên & Phê duyệt giải ngân
    ├── css/                      # Stylesheet
    └── js/
        └── app.js                # Core JS logic & Client Storage
```

---

## ⚡ HƯỚNG DẪN KHỞI CHẠY HỆ THỐNG (1 LỆNH DUY NHẤT)

```bash
python run.py
```

- **🌐 Frontend Web App**: `http://127.0.0.1:8000/`
- **🔑 Đăng nhập / KYC**: `http://127.0.0.1:8000/login_page.html`
- **📖 Swagger Interactive API Docs**: `http://127.0.0.1:8000/docs`
- **⚡ Realtime Live Feed WebSocket**: `ws://127.0.0.1:8000/ws/live-feed`
