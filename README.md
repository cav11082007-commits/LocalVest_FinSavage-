# 🏆 LocalVest — Nền Tảng Gọi Vốn Cộng Đồng Minh Bạch (MVP)

> **LocalVest** là nền tảng gọi vốn minh bạch kết hợp ký quỹ dòng tiền (Escrow), kiểm tra an toàn bằng AI (AI-Fraud Shield) và bản đồ tác động cộng đồng theo bán kính 3-5km (Hyperlocal Geofencing).

---

## ⚠️ GHI CHÚ QUAN TRỌNG: VỀ CÁC ĐƯỜNG DẪN LINK VÀ TỆP KHỞI ĐỘNG

> [!WARNING]
> Nếu bấm vào link `http://127.0.0.1:8000/docs` hoặc `ws://127.0.0.1:8000/ws/live-feed` mà trình duyệt báo lỗi **"Không thể kết nối / Trang web không hoạt động"**:
> 
> **NGUYÊN NHÂN**: Do Server Python chưa được khởi động trong Terminal nên cổng `8000` chưa lắng nghe.
> 
> **CÁCH MỞ LINK THÀNH CÔNG**:
> 1. Mở Terminal tại thư mục `LocalVest` (thư mục gốc chứa file `run.py`) và gõ:
>    ```bash
>    python run.py
>    ```
> 2. Giữ nguyên cửa sổ Terminal đó đang chạy, hệ thống sẽ tự động mở trình duyệt web lên cho bạn. Lúc này các đường dẫn link sẽ truy cập được 100%!
---

## 🏛️ TỔNG QUAN KIẾN TRÚC HỆ THỐNG (SYSTEM DESIGN)

Hệ thống được thiết kế theo mô hình **Modular Monolith**:

```
                              [ LocalVest Frontend ]
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

## 📂 CẤU TRÚC THƯ MỤC

```text
LocalVest/
├── run.py                        # Launcher 1-Click duy nhất (python run.py)
├── README.md                     # Tài liệu thiết kế hệ thống & hướng dẫn chạy
├── backend.md                    # Tài liệu ghi chú API & giải thích đường dẫn link
├── backend/                      # Python FastAPI Enterprise Backend
│   ├── main.py                   # App chính, Phục vụ tĩnh Frontend & API Routers
│   ├── start_server.py           # Script chạy backend folder 
│   ├── requirements.txt          # Khai báo các thư viện Python
│   └── app/
│       ├── config.py             # Cấu hình môi trường & JWT Settings
│       ├── api/                  # 8 API Routers tương ứng 8 dịch vụ
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
└── frontend/                     # Frontend
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

## HƯỚNG DẪN KHỞI CHẠY HỆ THỐNG - Scripts
```command prompt
clone https://github.com/cav11082007-commits/LocalVest_FinSavage-.git
cd LocalVest
code . 
```terminal
python run.py
```
---

## HƯỚNG PHÁT TRIỂN VỀ AI SAU NÀY CỦA NHÓM

Để tiếp tục hoàn thiện và đưa LocalVest lên một tầm cao mới sau phiên bản MVP này, dưới đây là các gợi ý phát triển sâu hơn về AI mà nhóm chúng em sẽ thực hiện:

1. **AI Knowledge Graph (GraphDB Fraud Detection)**:
   - Thay vì chỉ check trùng lặp 1-1, chúng ta có thể xây dựng đồ thị tri thức (Knowledge Graph) liên kết Số điện thoại - IP - CCCD - STK Ngân hàng. AI sẽ phát hiện ra các đường dây tạo chiến dịch ảo và chặn hàng loạt thay vì chặn đơn lẻ.
2. **Generative AI Project Assistant**:
   - Tích hợp mô hình ngôn ngữ lớn (LLM) vào form tạo dự án. Chủ dự án chỉ cần gõ vài dòng ngắn gọn, AI sẽ tự động sinh ra một bản kế hoạch huy động vốn chi tiết, chuyên nghiệp, hấp dẫn người đọc nhưng vẫn đúng sự thật.
3. **Hyper-Personalized Recommendation**:
   - Sử dụng Collaborative Filtering AI (tương tự thuật toán của Tiktok) kết hợp với PostGIS Geofencing để gợi ý các dự án phù hợp nhất với sở thích đóng góp và lịch sử tương tác của từng user.
4. **Computer Vision - AI Audit Milestone**:
   - Nâng cấp tính năng giải ngân tự động: Khi chủ dự án upload ảnh nghiệm thu (vd: ảnh phòng học đã lắp xong bàn ghế), AI Object Detection sẽ đếm số lượng bàn ghế trong ảnh xem có khớp với cam kết trong Milestone hay không trước khi báo cáo Admin duyệt.



