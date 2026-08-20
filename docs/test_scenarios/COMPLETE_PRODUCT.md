# 📦 LocalVest — Mô Tả Chi Tiết Tính Năng Sản Phẩm Hoàn Chỉnh (Product Specification)

> **LocalVest** là giải pháp nền tảng gọi vốn minh bạch thế hệ mới dành cho các dự án cộng đồng địa phương, giải quyết triệt để rủi ro gian lận tài chính nhờ mô hình **Ví Ký Quỹ Escrow**, **Lá Chắn AI Anti-Fraud Đa Tầng (NLP, pHash & Deep Learning ONNX)**, **Bản Đồ Bán Kính 3-5km (Geofencing)** và **Hệ Thống Thông Báo Thời Gian Thực (WebSocket Dual-Channel Hub)**.

---

## 🌟 1. CÁC TÍNH NĂNG CỐT LÕI (CORE FEATURES)

### 🔑 1.1. Hệ thống Auth, Phân quyền RBAC, OTP & Bảo Mật Mật Khẩu
- **Xác thực số điện thoại & Email OTP**: Gửi mã OTP 6 chữ số đảm bảo người dùng là thật, chống tài khoản ảo spam.
- **Bảo mật OTP Đa Tầng**:
  - Rate-limiting: Tối đa 5 lần gửi OTP / phút (HTTP 429).
  - Brute-force Lockout: Tự động khóa tạm thời 15 phút nếu nhập sai mã OTP 5 lần liên tiếp (HTTP 401).
- **Chính sách mật khẩu mạnh (Password Regex)**: Tối thiểu 8 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt.
- **Phân quyền 3 vai trò (RBAC)**:
  - `backer`: Người ủng hộ xem dự án, đóng góp Escrow, xem đồ thị dòng tiền Chart.js.
  - `project_owner`: Chủ dự án đăng bài, nộp hồ sơ KYC, tạo danh sách cột mốc giải ngân.
  - `admin`: Quản trị viên duyệt KYC, duyệt dự án lên sàn, giải ngân từng mốc, khóa tài khoản vi phạm.
- **Quy trình KYC Toàn Diện**: Tải ảnh CCCD 2 mặt, thông tin tài khoản ngân hàng, link mạng xã hội, địa chỉ cư trú; Admin phê duyệt cấp huy hiệu `creator_verified`.

---

### 🔒 1.2. Ví Ký Quỹ Nội Bộ (Escrow Double-Entry Ledger) & Bảo Vệ Tài Chính
- **Ký quỹ an toàn**: Tiền quyên góp của Backer được giữ an toàn tại ví Ký quỹ Escrow. Chủ dự án **KHÔNG THỂ tự ý rút tiền**.
- **Xác thực chữ ký số MoMo (HMAC-SHA256)**: Mọi giao dịch nạp tiền qua Webhook đều được xác minh chữ ký mã hóa chống giả mạo dữ liệu truyền tải.
- **Chống nạp trùng (Idempotency)**: Lưu vết `gatewayTxnId` kiểm tra O(1) ngăn chặn triệt để tấn công Replay Attack / Double-spending.
- **Khóa sổ tự động (Funded Lock)**: Khi dự án đạt 100% mục tiêu tài chính, hệ thống tự động khóa nhận quyên góp để đảm bảo tôn trọng cam kết ban đầu.
- **Chống rút thấu chi (Overdraw Protection)**: Kiểm tra nghiêm ngặt `available_balance >= milestone_amount` trước khi cho phép giải ngân.

---

### 🛡️ 1.3. Lá Chắn AI Anti-Fraud Đa Tầng (Multimodal AI Shield)
- **NLP Text Anomaly Scanner**:
  - Phân tích từ khóa nghi vấn tiếng Việt có trọng số (`lua dao` +35, `chuyen khoan ca nhan` +25, `xac thuc gia` +30, `crypto` +20, `gap lam` +10).
  - Xử lý né tránh kiểu Leetspeak (`l.u.a d.a.0`, `cr¥pto`) và chèn khoảng trắng/ký tự đặc biệt.
  - Xử lý ngữ cảnh phủ định (*"tuyệt đối không lừa đảo"* ➔ Chiết khấu 75% điểm phạt).
- **Perceptual Hashing (pHash) Reverse Image Search**:
  - Tính 64-bit perceptual hash của ảnh dự án, so khớp khoảng cách Hamming `<= 8` với cơ sở dữ liệu.
  - Hỗ trợ phát hiện ảnh bị **lật ngang (mirror-flipped)** để trốn kiểm duyệt (+40 điểm phạt).
- **Deep Learning ONNX Image Classifier (`image_fraud_model.onnx`)**:
  - Phân loại ảnh CCCD và ảnh hiện trường thành 3 nhãn: `ai_generated`, `edited`, `real`.
  - Phát hiện CCCD giả mạo bằng AI hoặc Photoshop (+50 điểm phạt).
- **Mô Hình AI Kiểm Toán Giải Ngân (`fraud_score_model.onnx`)**:
  - Phân tích 11 chỉ số vận tốc dòng tiền & tỷ lệ rút vốn trước khi giải ngân.
  - Tự động chặn giải ngân (`AUTO_BLOCK`) và sinh báo cáo AI Audit nếu điểm rủi ro `risk_score >= 50%` hoặc rút vốn đột biến > 40%.
- **Chạy ngầm phi phong bế (Non-blocking BackgroundTasks)**: Phản hồi API `< 150ms`, không làm gián đoạn trải nghiệm người dùng.

---

### 🗺️ 1.4. Định Vị Không Gian 3-5km (Hyperlocal Geofencing)
- **Truy vấn không gian 2 pha**:
  1. *Pha 1 (Bounding Box)*: Lọc nhanh bằng hộp tọa độ trong SQL.
  2. *Pha 2 (Haversine Formula)*: Tính toán khoảng cách mặt đất chính xác đến từng 0.1km.
- **Tự động mở rộng bán kính (Dynamic Auto-Expanding Radius)**: Nếu trong bán kính ban đầu (3km) không có dự án nào, hệ thống tự động mở rộng lên 10km để đảm bảo người dùng luôn tìm thấy dự án lân cận.

---

### ⚡ 1.5. Realtime Live Feed (WebSocket Broadcast)
- Đẩy dữ liệu tức thời qua kết nối WebSocket (`/ws/live-feed`).
- Hỗ trợ các sự kiện phát sóng:
  - `NEW_TRANSACTION`: Đẩy giao dịch ủng hộ mới (hiệu ứng Flash animation trên bảng điều khiển dòng tiền).
  - `PROJECT_APPROVED` / `PROJECT_REJECTED`: Cập nhật trạng thái duyệt dự án của Admin.
  - `MILESTONE_RELEASED`: Cập nhật tiến độ giải ngân cột mốc.
  - `NOTIFICATION`: Đẩy thông báo tức thời tới Notification Center.

---

### 🔔 1.6. Hệ Thống Thông Báo Đa Kênh (Dual-Channel Notification Hub)
- **Lưu trữ bền vững**: Ghi nhận toàn bộ thông báo vào bảng `notifications` trong SQLite (`donation`, `approval`, `milestone`, `info`).
- **Đẩy tức thời**: Phát song song qua WebSocket tới tài khoản người nhận.
- **Quản lý hộp thư**: Hỗ trợ đếm số thông báo chưa đọc (`unreadCount`), đánh dấu đã đọc từng tin hoặc đánh dấu tất cả đã đọc.

---

### 📊 1.7. Đồ Thị Dòng Tiền Trực Quan (Cash Flow Visualizer Chart.js)
- Hiển thị biểu đồ dạng Cột & Đường trực quan (Tổng mục tiêu, Tiền đã gọi vốn, Tiền trong Escrow, Tiền đã giải ngân).
- Minh bạch hóa 100% dòng tiền quyên góp và minh chứng thi công.

---

## 🎨 2. NGHỆ THUẬT PHÂN CHIA GIAO DIỆN & THUẬT NGỮ (UI & TERMINOLOGY)

| Tiêu chí | Giao diện Người Dùng (Backer / Owner) | Giao diện Quản trị viên (Admin Executive Hub) |
| :--- | :--- | :--- |
| **Tài khoản test** | `demo@localvest.vn` / `Demo@1234` | `admin@gmail.com` / `Admin123@gmail.com` |
| **Phong cách thiết kế** | Thân thiện, ấm áp, màu xanh hy vọng cộng đồng, sử dụng thẻ card Bo tròn mềm mại | Độc quyền Executive Dark Gold / Navy Executive, thiết kế dạng Bảng điều khiển kiểm toán cao cấp |
| **Thuật ngữ Dòng tiền** | *"Dòng tiền theo thời gian thực", "Số dư bảo đảm ký quỹ"* | *"Cập nhật thời gian thực từ tầng Gold (Medallion Lakehouse)", "Escrow Double-Entry Audit", "pHash Anomaly Score"* |
| **Quyền truy cập** | Ẩn hoàn toàn các nút Quản trị | Hiển thị đầy đủ ảnh KYC CCCD, lý do AI cảnh báo, công cụ Khóa tài khoản & Giải ngân mốc |

---

## 📚 3. DANH MỤC BỘ KỊCH BẢN KIỂM THỬ (TEST SCENARIOS INDEX)

| Mã Kịch Bản | File Kịch Bản | Nội dung trọng tâm |
| :--- | :--- | :--- |
| **TS-01** | [`01_auth_kyc_tests.md`](file:///d:/LocalVest/docs/test_scenarios/01_auth_kyc_tests.md) | Đăng ký, Đăng nhập, RBAC, Mật khẩu mạnh, Rate-limit OTP, Lockout & Thẩm định KYC |
| **TS-02** | [`02_escrow_ledger_tests.md`](file:///d:/LocalVest/docs/test_scenarios/02_escrow_ledger_tests.md) | Ký quỹ MoMo, HMAC-SHA256, Idempotency, Khóa sổ Funded, Chống rút thấu chi & AI Disbursement |
| **TS-03** | [`03_ai_fraud_shield_tests.md`](file:///d:/LocalVest/docs/test_scenarios/03_ai_fraud_shield_tests.md) | NLP Anomaly, Leetspeak, pHash trùng ảnh, Ảnh lật ngang, Deep Learning ONNX & Khóa tài khoản |
| **TS-04** | [`04_geofencing_location_tests.md`](file:///d:/LocalVest/docs/test_scenarios/04_geofencing_location_tests.md) | Định vị Bán kính 3-5km, Bounding-box + Haversine & Tự động mở rộng bán kính 10km |
| **TS-05** | [`05_realtime_websocket_tests.md`](file:///d:/LocalVest/docs/test_scenarios/05_realtime_websocket_tests.md) | Kênh WebSocket, Sự kiện New Txn, Duyệt dự án, Giải ngân mốc & Notification push |
| **TS-06** | [`06_notification_service_tests.md`](file:///d:/LocalVest/docs/test_scenarios/06_notification_service_tests.md) | Danh sách thông báo, Badge đếm chưa đọc, Đánh dấu đã đọc & Cơ chế phân phối đa kênh |
| **TS-07** | [`07_e2e_campaign_lifecycle_tests.md`](file:///d:/LocalVest/docs/test_scenarios/07_e2e_campaign_lifecycle_tests.md) | Kịch bản tích hợp toàn trình (E2E) từ Đăng ký, Tạo chiến dịch, Quét AI, Duyệt đến Giải ngân |
