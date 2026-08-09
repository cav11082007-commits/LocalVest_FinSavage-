# 🏆 LocalVest — Nền Tảng Gọi Vốn Cộng Đồng Minh Bạch (MVP Vòng 2)

> **LocalVest** là nền tảng gọi vốn minh bạch kết hợp ký quỹ dòng tiền (Escrow), kiểm tra an toàn bằng AI (AI-Fraud Shield) và bản đồ tác động cộng đồng theo bán kính 3-5km (Hyperlocal Geofencing).

---

## 🏛️ TỔNG QUAN KIẾN TRÚC HỆ THỐNG (SYSTEM DESIGN)

Hệ thống được thiết kế theo mô hình **Modular Monolith (Python FastAPI)** tối ưu hóa cho chi phí vận hành **0 VNĐ**:

```
                              [ LocalVest Frontend ]
                      (HTML5 / CSS3 / Vanilla JS - Preserved Files)
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

## 📂 CẤU TRÚC THƯ MỤC (FOLDER STRUCTURE)


```text
LocalVest/
├── README.md                     # Tài liệu thiết kế hệ thống & hướng dẫn chạy
├── backend/                      # Python FastAPI Enterprise Backend
│   ├── main.py                   # App chính & Đăng ký API Routers
│   ├── run.py                    # Script chạy nhanh server (python run.py)
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

## HƯỚNG DẪN CHẠY DỰ ÁN

### 1. Khởi chạy Python Backend API
```bash
cd backend
pip install -r requirements.txt
python run.py
```

- **Backend API**: `http://127.0.0.1:8000`
- **Swagger Interactive API Docs**: `http://127.0.0.1:8000/docs`
- **Realtime WebSocket**: `ws://127.0.0.1:8000/ws/live-feed`

### 2. Mở Frontend Web App
Mở file `frontend/index.html` hoặc `frontend/home.html` bằng Live Server hoặc trình duyệt bất kỳ.

---

## 💎 ĐIỂM SÁNG ĐỀ XUẤT ĂN GIẢI VÒNG 2 (0đ COST STACK)

1. **Escrow Double-Entry Ledger**: Dòng tiền nằm ở ví Ký quỹ nội bộ, chỉ được giải ngân từng mốc sau khi Admin kiểm tra bằng chứng thực tế.
2. **AI Fraud Shield**: Chạy ngầm trong background quét từ khóa lừa đảo và ảnh trùng lặp, tính chỉ số `fraud_score` mà không chặn trải nghiệm người dùng.
3. **Hyperlocal Geofencing (3-5km)**: Công thức Haversine + PostGIS GIST Index truy vấn dự án xung quanh bán kính hiện tại trong `< 20ms`.
4. **WebSocket Live Feed**: Cập nhật tức thì các giao dịch tài trợ và quyết định giải ngân lên màn hình người dùng.
