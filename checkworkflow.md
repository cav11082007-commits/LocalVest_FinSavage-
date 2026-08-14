========================================================================================================================
                               SƠ ĐỒ CHI TIẾT LUỒNG TƯƠNG TÁC FILE-SANG-FILE (BACKEND <--> FRONTEND)
========================================================================================================================
1. KÍCH HOẠT HỆ THỐNG & PHỤC VỤ STATIC FILES
------------------------------------------------------------------------------------------------------------------------
[run.py]
   │
   └──► [backend/main.py]
           │
           ├──► Load Config: [backend/app/config.py]
           ├──► Serves Static: [frontend/*.html], [frontend/js/app.js], [frontend/css/*]
           └──► Register API Routers: [backend/app/api/*.py]
2. LUỒNG XÁC THỰC & ĐĂNG NHẬP (AUTH & KYC)
------------------------------------------------------------------------------------------------------------------------
[frontend/login_page.html] ──(Thao tác form)──► [frontend/js/app.js]
                                                      │
                                                      │ HTTP POST /api/auth/login
                                                      ▼
                                           [backend/app/api/auth.py]
                                                      │
                                                      ├──► Kiểm tra DB/Memory: [backend/app/services/store.py]
                                                      ├──► Xác thực Mật khẩu & Tạo Token: [backend/app/core/security.py]
                                                      └──► Validate DTO Schema: [backend/app/schemas/schemas.py]
                                                      │
                                                      ▼ Trả về JWT Token
                                            [frontend/js/app.js] (Lưu Token vào localStorage)
3. LUỒNG TÌM KIẾM DỰ ÁN QUANH BÁN KÍNH 3-5KM (GEOFENCING LOCATION)
------------------------------------------------------------------------------------------------------------------------
[frontend/home.html] ──(Lấy toạ độ GPS)──► [frontend/js/app.js]
                                                │
                                                │ HTTP GET /api/location/nearby?lat=...&lng=...
                                                ▼
                                    [backend/app/api/location.py]
                                                │
                                                ├──► Tính khoảng cách Haversine / PostGIS: [backend/app/services/store.py]
                                                └──► Cấu trúc dữ liệu DB: [backend/app/database/schema.sql]
                                                │
                                                ▼ Trả về danh sách dự án gần đây
                                    [frontend/home.html] (Hiển thị UI Danh sách / Bản đồ)
4. LUỒNG ĐĂNG DỰ ÁN & KIỂM TRA PHÁT HIỆN GIAN LẬN AI (AI FRAUD SCREENING)
------------------------------------------------------------------------------------------------------------------------
[frontend/submit_project.html] ──(Gửi Form)──► [frontend/js/app.js]
                                                     │
                                                     │ HTTP POST /api/campaigns
                                                     ▼
                                         [backend/app/api/campaigns.py]
                                                     │
                                                     ├──► Lưu trạng thái 'pending_review': [backend/app/services/store.py]
                                                     └──► Trích xuất & Kiểm tra Async AI: [backend/app/services/ai_worker.py]
                                                                                                  │
                                                                                                  ▼
                                                                                   [backend/app/api/ai_flag.py] (Ghi nhận Fraud Score)
5. LUỒNG THANH TOÁN KÝ QUỸ ESCROW & BROADCAST TIME THỰC
------------------------------------------------------------------------------------------------------------------------
[frontend/checkout.html] ──(Quyên góp MoMo/VNPay)──► [frontend/js/app.js]
                                                           │
                                                           │ HTTP POST /api/payments/momo-webhook
                                                           ▼
                                               [backend/app/api/payments.py]
                                                           │
                                                           ├──► Ghi nhận Sổ cái Escrow Ledger: [backend/app/services/store.py]
                                                           │
                                                           ▼ Đẩy thông báo Event
                                               [backend/app/services/realtime.py]
                                                           │
                                                           │ WebSocket Broadcast (ws://127.0.0.1:8000/ws/live-feed)
                                                           ▼
                                               [frontend/js/app.js]
                                                           │
                                                           ▼ Cập nhật thanh tiến trình & Live Feed không cần F5
                                               [frontend/dashboard.html] / [frontend/project.html]
6. LUỒNG QUẢN TRỊ VIÊN PHÊ DUYỆT & GIẢI NGÂN MỐC (ADMIN DISBURSEMENT)
------------------------------------------------------------------------------------------------------------------------
[frontend/admin.html] ──(Duyệt giải ngân)──► [frontend/js/app.js]
                                                   │
                                                   │ HTTP POST /api/admin/release-milestone
                                                   ▼
                                       [backend/app/api/admin.py]
                                                   │
                                                   ├──► Kiểm tra quyền Admin (RBAC): [backend/app/core/security.py]
                                                   ├──► Cập nhật trạng thái mốc & Trừ ví Escrow: [backend/app/services/store.py]
                                                   │
                                                   ▼ Đẩy sự kiện giải ngân
                                       [backend/app/services/realtime.py] ──(WebSocket)──► [frontend/dashboard.html]
========================================================================================================================