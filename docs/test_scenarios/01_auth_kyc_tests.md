# 🧪 Test Scenario 01: Auth, Role-Based Access Control (RBAC) & KYC Verification

## Overview
Xác minh luồng Đăng ký, Đăng nhập, Phân quyền RBAC (`backer`, `project_owner`, `admin`), Xác thực số điện thoại OTP, Google/Apple OAuth và Quy trình tải hồ sơ KYC.

---

## Scenario 1.1: Register New User & Send OTP Verification
- **Preconditions**: Server Python đang chạy tại `http://127.0.0.1:8000`.
- **Steps**:
  1. Mở trang [http://127.0.0.1:8000/login_page.html](http://127.0.0.1:8000/login_page.html).
  2. Chọn tab **Đăng ký**.
  3. Nhập Họ tên: `Trần Văn An`, Email: `an.tran@gmail.com`, Mật khẩu: `123456`, Số điện thoại: `0901234567`.
  4. Nhấn nút **Gửi mã OTP**.
  5. Nhập mã OTP gồm 6 chữ số: `888999`.
  6. Nhấn nút **Xác nhận OTP & Đăng ký**.
- **Expected Results**:
  - Thông báo "Xác thực OTP thành công! Đã tạo tài khoản."
  - Token JWT được tạo và lưu vào `localStorage.getItem('lv_token')`.
  - Tự động chuyển hướng về trang Khám phá `home.html`.

---

## Scenario 1.2: Login as Admin & Verify Admin Access Control
- **Preconditions**: Tài khoản Admin sẵn có: Email `admin@gmail.com`, Mật khẩu `admin@gmail.com`.
- **Steps**:
  1. Mở trang `http://127.0.0.1:8000/login_page.html`.
  2. Nhập Email: `admin@gmail.com`, Mật khẩu: `admin@gmail.com`.
  3. Nhấn **Đăng nhập**.
- **Expected Results**:
  - Đăng nhập thành công với `role: "admin"`.
  - Trên Thanh điều hướng Navbar xuất hiện nút **"🛡️ Quản trị Admin"**.
  - Truy cập trang `admin.html` hiển thị giao diện **Dark Gold / Navy Executive Moderation Hub**.

---

## Scenario 1.3: Non-Admin Access Blocking
- **Steps**:
  1. Đăng nhập với tài khoản Backer thường (`an.tran@gmail.com`).
  2. Cố tình nhập URL `http://127.0.0.1:8000/admin.html`.
- **Expected Results**:
  - Hệ thống hiển thị Toast cảnh báo: "Bị từ chối: Quyền Quản trị viên mới được phép truy cập!"
  - Tự động đẩy người dùng quay lại `home.html`.
