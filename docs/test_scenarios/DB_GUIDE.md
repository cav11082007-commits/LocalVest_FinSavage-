# 🗄️ LocalVest Database & Data Architecture Guide (DB_GUIDE.md)

> Hướng dẫn cấu trúc dữ liệu mô hình PostgreSQL / SQLite cho LocalVest (Lấy cảm hứng từ chuẩn thiết kế TripleE/AVE).

---

## 📐 1. ERD SPECIFICATION & THỰC THỂ DỮ LIỆU

### 1.1. User & Session (`users`, `user_sessions`)
Lưu trữ thông tin người dùng, phân quyền RBAC và phiên làm việc.
- `id`: UUID (Primary Key)
- `email`: VARCHAR(255) UNIQUE
- `password_hash`: VARCHAR(255)
- `full_name`: VARCHAR(100)
- `phone_number`: VARCHAR(20)
- `is_phone_verified`: BOOLEAN DEFAULT false
- `role`: VARCHAR(20) (`backer`, `project_owner`, `admin`)
- `kyc_status`: VARCHAR(20) (`pending`, `approved`, `rejected`)
- `is_locked`: BOOLEAN DEFAULT false

### 1.2. Evidence File & KYC (`kyc_documents`, `evidence_files`)
Lưu trữ minh chứng KYC (CCCD) và minh chứng thi công cột mốc do chủ dự án tải lên.
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key ➔ users)
- `project_id`: UUID (Foreign Key ➔ projects)
- `file_type`: VARCHAR(50) (`kyc_front`, `kyc_back`, `milestone_receipt`, `site_photo`)
- `file_url`: TEXT NOT NULL
- `uploaded_at`: TIMESTAMP WITH TIME ZONE

### 1.3. Audit Finding & AI Fraud Shield (`ai_flags`)
Lưu trữ kết quả đánh giá rủi ro gian lận từ AI Worker.
- `id`: UUID (Primary Key)
- `project_id`: UUID (Foreign Key ➔ projects)
- `fraud_score`: INT (0 - 100)
- `is_suspicious`: BOOLEAN
- `reasons`: JSONB (Danh sách lý do trùng ảnh hoặc từ khóa nghi vấn)
- `status`: VARCHAR(20) (`pending_review`, `dismissed`, `confirmed_fraud`)

### 1.4. Campaign & Execution Plan (`projects`, `milestones`)
Lưu trữ kế hoạch thực thi dự án và các mốc giải ngân.
- `projects`: `id`, `owner_id`, `name`, `category`, `description`, `location_name`, `target_amount`, `raised_amount`, `status` (`draft`, `pending_review`, `active`, `funded`, `closed`), `lat`, `lng`, `geom` (PostGIS Point)
- `milestones`: `id`, `project_id`, `name`, `target_amount`, `released_amount`, `status` (`locked`, `pending`, `released`), `description`, `order_index`

### 1.5. Financial Ledger & Escrow Account (`ledger`)
Sổ cái kế toán kép lưu trữ biến động dòng tiền ký quỹ.
- `id`: UUID (Primary Key)
- `project_id`: UUID (Foreign Key ➔ projects)
- `user_id`: UUID (Foreign Key ➔ users)
- `amount`: DECIMAL(15,2)
- `type`: VARCHAR(20) (`escrow_deposit`, `milestone_release`, `refund`)
- `gateway`: VARCHAR(50) (`momo`, `vnpay`)
- `gateway_txn_id`: VARCHAR(100)
- `created_at`: TIMESTAMP WITH TIME ZONE

### 1.6. Knowledge Base (`knowledge_base`)
Lưu trữ cơ sở dữ liệu mẫu về các vụ lừa đảo gọi vốn cộng đồng để AI so sánh đối chiếu.

---

## 🛢️ 2. DDL SQL SCHEMA

Cấu trúc chi tiết lệnh khởi tạo PostgreSQL / PostGIS được lưu tại [`backend/app/database/schema.sql`](file:///d:/LocalVest/backend/app/database/schema.sql).

---

## 🧪 3. HƯỚNG DẪN TEST SẢN PHẨM LOCALVEST (USER SCENARIOS)

Dưới đây là kịch bản test nghiệm thu hệ thống (UAT) cho người dùng cuối và quản trị viên:

### Kịch bản 1: User đăng nhập & Xác thực OTP
1. Mở `http://127.0.0.1:8000/`. Hệ thống sẽ tự động chuyển hướng đến trang đăng nhập.
2. Chọn **Đăng nhập bằng Email** -> Nhập email bất kỳ (VD: `test@gmail.com`).
3. Nếu email chưa tồn tại, hệ thống chuyển sang Form Đăng ký. Điền đủ thông tin, SĐT và mật khẩu.
4. (Demo OTP) Để test luồng có sẵn tài khoản: Dùng email `demo@localvest.vn` -> Nhập mật khẩu tùy ý -> Nhập OTP là `123456`.
5. Đăng nhập thành công sẽ chuyển vào trang **Khám phá** (Home).

### Kịch bản 2: User xem Dự án & Dòng tiền
1. Sau khi vào trang Khám phá, kéo xuống danh sách dự án xung quanh (đã áp dụng Geofencing).
2. Click vào **Xem chi tiết** một dự án (VD: "Phòng học miễn phí cho trẻ em xóm trọ").
3. Chuyển sang tab **Dòng tiền** (Dashboard), bạn sẽ thấy giao diện **Chart.js** hiển thị đồ thị thân thiện: *Tiền đã gọi vốn, Đang ký quỹ, Đã giải ngân*. Mọi thông tin đều rõ ràng, không khô khan.

### Kịch bản 3: Phân quyền & Quản trị viên (Admin Premium)
1. Đăng xuất tài khoản User.
2. Đăng nhập lại bằng Email: `admin@gmail.com`, Mật khẩu: `admin@123gmail.com`, OTP: `123456`.
3. Nhận thấy điều hướng chuyển sang **Giao diện Admin Premium** (Dark Mode sang trọng).
4. Khám phá Dashboard Admin hiển thị: Đồ thị Escrow Ledger cao cấp, Cảnh báo AI Fraud Score, Ảnh CCCD/Minh chứng của các User. User thường sẽ KHÔNG thấy được menu "Quản trị" này.
