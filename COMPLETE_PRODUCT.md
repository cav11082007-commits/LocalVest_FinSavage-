# 📦 LocalVest — Mô Tả Chi Tiết Tính Năng Sản Phẩm Hoàn Chỉnh (Product Specification)

> **LocalVest** là giải pháp nền tảng gọi vốn minh bạch thế hệ mới dành cho các dự án cộng đồng địa phương, giải quyết triệt để rủi ro gian lận tài chính nhờ mô hình **Ví Ký Quỹ Escrow**, **Lá Chắn AI Anti-Fraud** và **Bản Đồ Bán Kính 3-5km (Geofencing)**.

---

## 🌟 1. CÁC TÍNH NĂNG CỐT LÕI (CORE FEATURES)

### 🔑 1.1. Hệ thống Auth, Phân quyền RBAC & Xác thực OTP / OAuth
- **Xác thực số điện thoại OTP**: Gửi mã OTP 6 chữ số đảm bảo người dùng là thật (Real User verification), chống tài khoản ảo spam.
- **Đăng nhập Mạng xã hội 0đ**: Tích hợp Google Sign-In & Apple OAuth qua Supabase/Firebase Auth Free Tier.
- **Phân quyền 3 vai trò (RBAC)**:
  - `backer`: Người ủng hộ xem dự án, đóng góp Escrow, xem đồ thị dòng tiền Viz.
  - `project_owner`: Chủ dự án đăng bài, tạo danh sách cột mốc giải ngân.
  - `admin`: Quản trị viên duyệt KYC, duyệt dự án lên sàn, giải ngân từng mốc, khóa tài khoản vi phạm.

### 🔒 1.2. Ví Ký Quỹ Nội Bộ (Escrow Double-Entry Ledger)
- Tiền quyên góp của Backer được giữ an toàn tại ví Ký quỹ Escrow.
- Chủ dự án **KHÔNG THỂ tự rút toàn bộ tiền** mà phải gửi minh chứng thi công từng cột mốc (Milestones).
- Admin kiểm duyệt bằng chứng thực tế trước khi bấm **Giải ngân**. Nếu dự án thất bại, cơ chế hoàn tiền (Refund) được kích hoạt tự động.

### 🛡️ 1.3. Lá Chắn AI Anti-Fraud (Non-Blocking Background Worker)
- **Computer Vision & pHash**: So sánh ảnh đính kèm dự án với cơ sở dữ liệu ảnh lừa đảo trên mạng.
- **NLP Text Anomaly Scan**: Phân tích cú pháp mô tả dự án để tìm các từ khóa rủi ro (như *lừa đảo, chuyển khoản cá nhân, crypto, gấp lắm*).
- **Chạy ngầm (Non-blocking)**: Xử lý bằng `BackgroundTasks` không làm gián đoạn luồng người dùng, trả về chỉ số nguy cơ `fraud_score` (0-100%) kèm danh sách lý do cụ thể trên Bảng quản trị Admin.

### 🗺️ 1.4. Định Vị Không Gian 3-5km (Hyperlocal Geofencing)
- Sử dụng thuật toán Haversine kết hợp chỉ mục không gian PostGIS `ST_DWithin` cho tốc độ phản hồi `< 20ms`.
- Giúp Backer dễ dàng lọc và tìm kiếm các dự án cộng đồng (lớp học xóm trọ, trạm tái chế nhựa) ngay trong khu phố mình sống.

### ⚡ 1.5. Realtime Live Feed (WebSocket / SSE)
- Đẩy dữ liệu tức thời qua kết nối WebSocket (`/ws/live-feed`).
- Khi có lượt tài trợ mới hoặc một cột mốc được giải ngân, màn hình Dòng tiền sẽ tự động cập nhật ngay lập tức mà **không cần bấm F5 / Refresh**.

### 📊 1.6. Đồ Thị Dòng Tiền Trực Quan (Cash Flow Visualizer Chart.js)
- Dành cho người dùng thông thường không muốn đọc các con số khô khan.
- Hiển thị biểu đồ dạng Cột & Đường trực quan (Tổng mục tiêu, Tiền đã gọi vốn, Tiền trong Escrow, Tiền đã giải ngân, Tiến độ dự phóng tương lai).

---

## 🎨 2. NGHỆ THUẬT PHÂN CHIA GIAO DIỆN & THUẬT NGỮ (UI & TERMINOLOGY)

| Tiêu chí | Giao diện Người Dùng (Backer / Owner) | Giao diện Quản trị viên (Admin Hub) |
| :--- | :--- | :--- |
| **Tài khoản test** | `demo@localvest.vn` | `admin@gmail.com` / `admin@gmail.com` |
| **Phong cách thiết kế** | Thân thiện, ấm áp, màu xanh hy vọng cộng đồng, sử dụng thẻ card Bo tròn mềm mại | Độc quyền Executive Dark Gold / Navy Executive, thiết kế dạng Bảng điều khiển kiểm toán cao cấp |
| **Thuật ngữ Dòng tiền** | *"Dòng tiền theo thời gian thực", "Số dư bảo đảm ký quỹ"* | *"Cập nhật thời gian thực từ tầng Gold (Medallion Lakehouse)", "Escrow Double-Entry Audit", "pHash Anomaly Score"* |
| **Quyền truy cập** | Ẩn hoàn toàn các nút Quản trị | Hiển thị đầy đủ ảnh KYC, lý do AI cảnh báo, công cụ Khóa tài khoản & Giải ngân mốc |
