# 🗄️ LocalVest Database & Data Architecture Guide (DB_GUIDE.md)

> Hướng dẫn cấu trúc dữ liệu mô hình SQLite / PostgreSQL cho LocalVest (Lấy cảm hứng từ chuẩn thiết kế TripleE/AVE & Clean Architecture).

---

## 📐 1. ERD SPECIFICATION & THỰC THỂ DỮ LIỆU

### 1.1. User & Session (`users`, `user_sessions`)
Lưu trữ thông tin người dùng, phân quyền RBAC và phiên làm việc.
- `id`: TEXT / UUID (Primary Key)
- `email`: VARCHAR(255) UNIQUE
- `password_hash`: VARCHAR(255)
- `full_name`: VARCHAR(100)
- `phone`: VARCHAR(20)
- `alt_emails`: TEXT (JSON Array các email/SĐT liên kết phụ)
- `role`: VARCHAR(20) (`backer`, `project_owner`, `admin`)
- `kyc_status`: VARCHAR(20) (`pending`, `approved`, `rejected`)
- `is_locked`: BOOLEAN DEFAULT false
- `created_at`, `updated_at`: TIMESTAMP

### 1.2. Evidence File & KYC (`kyc_documents`, `evidence_files`)
Lưu trữ minh chứng KYC (CCCD) và minh chứng thi công cột mốc do chủ dự án tải lên.
- `id`: TEXT / UUID (Primary Key)
- `user_id`: TEXT (Foreign Key ➔ users)
- `doc_type`: VARCHAR(50) (`cccd`, `cmnd`, `passport`)
- `front_image_url`: TEXT NOT NULL
- `back_image_url`: TEXT
- `dob`: TEXT (Ngày tháng năm sinh)
- `current_address`: TEXT
- `social_link`: TEXT
- `bank_info`: TEXT (JSON object lưu `bank_name`, `account_number`, `account_name`)
- `status`: VARCHAR(20) (`pending`, `approved`, `rejected`)
- `submitted_at`: TIMESTAMP

### 1.3. Audit Finding & AI Fraud Shield (`ai_flags`)
Lưu trữ kết quả đánh giá rủi ro gian lận từ AI Worker (NLP, pHash, ONNX).
- `id`: TEXT / UUID (Primary Key)
- `project_id`: TEXT (Foreign Key ➔ projects)
- `fraud_score`: INT (0 - 100)
- `is_suspicious`: BOOLEAN
- `reasons`: TEXT (JSON Array danh sách lý do trùng ảnh hoặc từ khóa nghi vấn)
- `status`: VARCHAR(20) (`pending_review`, `dismissed`, `confirmed_fraud`)
- `created_at`: TIMESTAMP

### 1.4. Campaign & Execution Plan (`projects`, `milestones`)
Lưu trữ kế hoạch thực thi dự án và các mốc giải ngân.
- `projects`: `id`, `owner_id`, `name`, `category`, `icon`, `cover`, `images` (JSON Array), `description`, `location_name`, `target_amount`, `raised_amount`, `status` (`draft`, `pending_review`, `active`, `funded`, `completed`, `rejected`), `lat`, `lng`, `creator_name`, `creator_verified`, `created_at`, `updated_at`.
- `milestones`: `id`, `project_id`, `name`, `target_amount`, `released_amount`, `status` (`locked`, `pending`, `released`), `description`, `order_index`, `released_at`.

### 1.5. Financial Ledger & Escrow Account (`ledger`)
Sổ cái kế toán kép lưu trữ biến động dòng tiền ký quỹ.
- `id`: TEXT / UUID (Primary Key)
- `project_id`: TEXT (Foreign Key ➔ projects)
- `user_name`: VARCHAR(100)
- `amount`: DECIMAL(15,2)
- `type`: VARCHAR(20) (`escrow_deposit`, `milestone_release`, `refund`)
- `gateway`: VARCHAR(50) (`momo`, `bank`, `vnpay`)
- `gateway_txn_id`: VARCHAR(100) (Idempotency Key)
- `description`: TEXT
- `created_at`: TIMESTAMP

### 1.6. Notification Center (`notifications`)
Lưu trữ các thông báo hệ thống được đẩy tới người dùng.
- `id`: TEXT / UUID (Primary Key)
- `user_id`: TEXT NOT NULL (Foreign Key ➔ users)
- `title`: TEXT NOT NULL
- `message`: TEXT NOT NULL
- `type`: VARCHAR(50) (`donation`, `approval`, `milestone`, `info`)
- `is_read`: BOOLEAN DEFAULT false
- `created_at`: TIMESTAMP

---

## 🛢️ 2. DDL SQL SCHEMA

- **SQLite Schema (MVP Active DB)**: [`backend/app/database/sqlite_schema.sql`](file:///d:/LocalVest/backend/app/database/sqlite_schema.sql)
- **PostgreSQL / PostGIS Schema (Production Ready)**: [`backend/app/database/schema.sql`](file:///d:/LocalVest/backend/app/database/schema.sql)

---

## 🧪 3. BỘ KỊCH BẢN KIỂM THỬ HỆ THỐNG (TEST SCENARIOS DIRECTORY)

Chi tiết từng kịch bản kiểm thử (Test Scenarios) độc lập cho từng phân hệ được tổ chức tại thư mục `docs/test_scenarios/`:

1. **[`01_auth_kyc_tests.md`](file:///d:/LocalVest/docs/test_scenarios/01_auth_kyc_tests.md)**: Xác thực Auth, Phân quyền RBAC, Mật khẩu mạnh, Rate-limit OTP, Lockout & Thẩm định KYC.
2. **[`02_escrow_ledger_tests.md`](file:///d:/LocalVest/docs/test_scenarios/02_escrow_ledger_tests.md)**: Ví Ký quỹ Escrow, HMAC-SHA256, Chống nạp trùng Idempotency, Funded Lock & ONNX AI Pre-Audit giải ngân.
3. **[`03_ai_fraud_shield_tests.md`](file:///d:/LocalVest/docs/test_scenarios/03_ai_fraud_shield_tests.md)**: NLP Text Anomaly, Leetspeak, pHash Reverse-image, Ảnh lật ngang & Deep Learning ONNX Classifier.
4. **[`04_geofencing_location_tests.md`](file:///d:/LocalVest/docs/test_scenarios/04_geofencing_location_tests.md)**: Định vị Bán kính 3-5km Bounding Box + Haversine & Tự động mở rộng bán kính 10km.
5. **[`05_realtime_websocket_tests.md`](file:///d:/LocalVest/docs/test_scenarios/05_realtime_websocket_tests.md)**: Live Feed WebSocket, Giao dịch tức thời, Phê duyệt dự án & Đẩy thông báo.
6. **[`06_notification_service_tests.md`](file:///d:/LocalVest/docs/test_scenarios/06_notification_service_tests.md)**: Trung tâm thông báo, Đếm chưa đọc, Đánh dấu đã đọc & Phân phối đa kênh.
7. **[`07_e2e_campaign_lifecycle_tests.md`](file:///d:/LocalVest/docs/test_scenarios/07_e2e_campaign_lifecycle_tests.md)**: Kịch bản tích hợp toàn trình (E2E) từ Đăng ký, Tạo chiến dịch đến Hoàn tất giải ngân.
