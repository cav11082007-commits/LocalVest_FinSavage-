
---

## 🚀 DANH SÁCH ĐƯỜNG DẪN HOẠT ĐỘNG (KHI SERVER ĐANG CHẠY)

| Loại Tài Nguyên | Đường Dẫn (URL) | Mô Tả |
| :--- | :--- | :--- |
| **🌐 Web Frontend App** | `http://127.0.0.1:8000/` | Trực tiếp mở ứng dụng LocalVest |
| **🔑 Trang Đăng Nhập / KYC** | `http://127.0.0.1:8000/login_page.html` | Đăng ký, đăng nhập & Tải KYC |
| **📖 Tài liệu Swagger API** | `http://127.0.0.1:8000/docs` | Kiểm thử 8 API Vòng 2 trực tiếp |
| **⚡ WebSocket Live Feed** | `ws://127.0.0.1:8000/ws/live-feed` | Kết nối đẩy tin tức thời |

---

## 🛠️ CẤU TRÚC 8 DỊCH VỤ TRÊN NHÁNH 

1. **Auth & User Service**: `/api/auth/register`, `/api/auth/login`, `/api/auth/kyc-upload`
2. **Campaign Service**: `/api/campaigns` (State machine `pending_review` ➔ `active` ➔ `funded`)
3. **Payment & Escrow Service**: `/api/payments/momo-webhook` (Ghi nhận Sổ cái Ledger Escrow)
4. **Location Service**: `/api/location/nearby` (Truy vấn bán kính 3-5km bằng Haversine)
5. **AI-Flag Service**: `/api/ai-flag/{project_id}` (Async Background Worker)
6. **Admin / Moderation Service**: `/api/admin/pending-projects`, `/api/admin/approve-project`, `/api/admin/release-milestone`
7. **Realtime Feed**: WebSocket `/ws/live-feed`
