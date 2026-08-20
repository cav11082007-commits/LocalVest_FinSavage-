# 🧪 Test Scenario 01: Auth, Role-Based Access Control (RBAC), OTP Security & KYC Verification

## Overview
Bộ kịch bản kiểm thử toàn diện cho hệ thống Authentication, Authorization (RBAC: `backer`, `project_owner`, `admin`), Bảo mật mã OTP (Rate-limiting, Brute-force Lockout), Chính sách mật khẩu mạnh và Quy trình thẩm định hồ sơ định danh KYC (CCCD, Địa chỉ, Liên kết MXH, Tài khoản ngân hàng).

---

## Scenario 1.1: Register New User with Strong Password & OTP
- **Preconditions**: Server Backend đang chạy tại `http://127.0.0.1:8000`.
- **Steps**:
  1. Mở trang [http://127.0.0.1:8000/login_page.html](http://127.0.0.1:8000/login_page.html).
  2. Chọn tab **Đăng ký**.
  3. Nhập Họ tên: `Trần Văn An`, Email: `an.tran@gmail.com`, SĐT: `0901234567`.
  4. Nhập Mật khẩu hợp chuẩn: `AnTran@2026` *(tối thiểu 8 ký tự, gồm chữ hoa, chữ thường, số/ký tự đặc biệt)*.
  5. Nhấn nút **Đăng ký tài khoản**.
- **Expected Results**:
  - API `POST /api/auth/register` trả về HTTP 200 với payload chứa `access_token`, `token_type: "bearer"` và thông tin user.
  - JWT Token được lưu an toàn vào `localStorage.getItem('lv_token')`.
  - Hiển thị thông báo thành công và chuyển hướng về trang Khám phá `home.html`.

---

## Scenario 1.2: Password Strength Policy Enforcement
- **Steps**:
  1. Mở form Đăng ký tại `login_page.html`.
  2. Thử nhập mật khẩu yếu: `123456` hoặc `password`.
  3. Nhấn **Đăng ký**.
- **Expected Results**:
  - Backend Validator chặn request với HTTP 422: `"Mật khẩu phải có tối thiểu 8 ký tự, gồm chữ hoa, chữ thường và ký tự đặc biệt."`
  - Hệ thống không tạo user rác vào cơ sở dữ liệu.

---

## Scenario 1.3: OTP Generation & Multi-Channel Delivery (SMS / Email)
- **Steps**:
  1. Mở trang `login_page.html` chọn tab **Đăng nhập OTP**.
  2. Nhập Identifier: `0901234567` (hoặc email `an.tran@gmail.com`).
  3. Bấm **Gửi mã OTP**.
- **Expected Results**:
  - API `POST /api/auth/send-otp` sinh mã OTP 6 chữ số ngẫu nhiên (TTL 300s = 5 phút).
  - Đối với SĐT: Ghi nhận log tại `sms_outbox.txt` và in console `[MOCK-OTP] Gửi tới <0901234567>: XXXXXX`.
  - Đối với Email: Gửi qua SMTP Gmail (nếu cấu hình) hoặc lưu log tại `email_inbox.txt`.
  - Nếu Identifier chưa từng đăng ký: Trả về HTTP 404 `"Email/Số điện thoại này chưa được đăng ký. Vui lòng tạo tài khoản trước khi đăng nhập."`

---

## Scenario 1.4: OTP Rate Limiting & Brute-Force Lockout Defense
- **Steps (Rate Limit)**:
  1. Gửi liên tiếp 6 yêu cầu OTP trong vòng dưới 60 giây cho cùng 1 SĐT/Email.
- **Expected Results (Rate Limit)**:
  - Lần gửi thứ 6 bị chặn với HTTP 429: `"Bạn đã yêu cầu gửi OTP quá 5 lần trong 1 phút. Vui lòng thử lại sau!"`

- **Steps (Brute-Force Lockout)**:
  1. Gửi OTP đến `0901234567`.
  2. Cố tình nhập sai mã OTP 5 lần liên tiếp qua API `POST /api/auth/verify-otp`.
- **Expected Results (Brute-Force Lockout)**:
  - Lần sai 1-4: Trả về HTTP 401 thông báo `"Mã OTP không chính xác. Còn X lần thử!"`.
  - Lần sai thứ 5: Kích hoạt cơ chế tạm khóa 15 phút (900 giây), HTTP 401: `"Bạn đã nhập sai mã OTP quá 5 lần liên tiếp. Khóa tạm thời 15 phút!"`.
  - Mọi nỗ lực xác thực trong thời gian khóa đều bị từ chối.

---

## Scenario 1.5: Login as Admin & Verify Admin Access Control
- **Preconditions**: Tài khoản Admin mặc định: Email `admin@gmail.com` / `admin@localvest.vn`, Mật khẩu `Admin123@gmail.com`.
- **Steps**:
  1. Mở `http://127.0.0.1:8000/login_page.html`.
  2. Nhập Email: `admin@gmail.com`, Mật khẩu: `Admin123@gmail.com`.
  3. Nhấn **Đăng nhập**.
- **Expected Results**:
  - Đăng nhập thành công với `role: "admin"`.
  - Thanh Navbar xuất hiện nút **"🛡️ Quản trị Admin"**.
  - Truy cập `admin.html` thành công, hiển thị giao diện Quản trị Dark Gold / Navy Executive Moderation Hub.

---

## Scenario 1.6: Non-Admin RBAC Access Blocking
- **Steps**:
  1. Đăng nhập với tài khoản Backer thông thường (`an.tran@gmail.com`).
  2. Cố tình nhập trực tiếp URL `http://127.0.0.1:8000/admin.html` hoặc gọi API Admin `GET /api/admin/pending-projects`.
- **Expected Results**:
  - Giao diện web hiển thị Toast cảnh báo: `"Bị từ chối: Quyền Quản trị viên mới được phép truy cập!"` và tự động redirect về `home.html`.
  - API Backend trả về HTTP 403 Forbidden: `"Chỉ Quản trị viên mới có quyền thực hiện thao tác này"`.

---

## Scenario 1.7: Full KYC Submission & Admin Approval Workflow
- **Steps**:
  1. User đăng nhập tài khoản Owner/Backer.
  2. Mở form tải hồ sơ KYC tại `submit_project.html` hoặc gọi `POST /api/auth/kyc-upload`.
  3. Tải ảnh CCCD mặt trước (`kyc_front`), mặt sau (`kyc_back`), nhập Ngày sinh, Địa chỉ hiện tại, Link Facebook/LinkedIn và Thông tin STK Ngân hàng.
  4. Đăng nhập tài khoản Admin `admin@gmail.com`, mở `admin.html` tab **Duyệt hồ sơ KYC**.
  5. Admin xem ảnh đối soát CCCD, bấm **Duyệt hồ sơ**.
- **Expected Results**:
  - Gọi API `POST /api/admin/kyc/{kyc_id}/status` với `{"status": "approved"}`.
  - Cập nhật trường `kyc_status = 'approved'` trong bảng `users`.
  - Cập nhật cờ `creator_verified = 1` cho tất cả dự án thuộc sở hữu của chủ tài khoản này.
  - Dự án hiển thị Badge xanh **"Đã xác thực danh tính chính chủ"** trên toàn sàn.
