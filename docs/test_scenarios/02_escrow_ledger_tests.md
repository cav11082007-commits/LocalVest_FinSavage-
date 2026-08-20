# 🧪 Test Scenario 02: Escrow Double-Entry Ledger, HMAC-SHA256 & AI Milestone Disbursement

## Overview
Kiểm thử tính toàn vẹn của mô hình ví Ký quỹ nội bộ (Escrow), cơ chế xác thực chữ ký số HMAC-SHA256, khả năng chống tấn công nạp trùng (Idempotency), khóa sổ khi đạt mục tiêu và quy trình giải ngân theo cột mốc tích hợp **Mô hình AI Đánh giá rủi ro dòng tiền (AI Disbursement Risk Auditor ONNX)**.

---

## Scenario 2.1: Backer Financial Deposit into Escrow via MoMo Webhook
- **Preconditions**: Dự án "Phòng học miễn phí cho trẻ em xóm trọ" (`proj_1`) đang ở trạng thái `active`.
- **Steps**:
  1. Mở trang [http://127.0.0.1:8000/checkout.html?id=proj_1](http://127.0.0.1:8000/checkout.html?id=proj_1).
  2. Chọn phương thức thanh toán **MoMo Sandbox QR**.
  3. Nhập số tiền ủng hộ: `200.000đ`, Tên người ủng hộ: `Trần Văn An`.
  4. Nhấn **Xác nhận thanh toán MoMo**.
- **Expected Results**:
  - Frontend/Backend sinh chữ ký số bảo mật `HMAC-SHA256(secret_key, "amount=200000&gatewayTxnId=...&projectId=proj_1")`.
  - Webhook `POST /api/payments/momo-webhook` xác thực chữ ký hợp lệ.
  - Sổ cái kế toán kép `ledger` ghi nhận bút toán Nợ/Có: `+200.000đ từ Trần Văn An (Ký quỹ Escrow)`.
  - Tổng số tiền gọi vốn `raised_amount` của dự án tăng thêm `200.000đ`.
  - Tiền được giữ tại ví Ký quỹ an toàn, chủ dự án KHÔNG THỂ tự ý rút tiền.

---

## Scenario 2.2: Idempotency Protection & Replay Attack Prevention
- **Steps**:
  1. Giả lập một kẻ tấn công gửi lại cùng một Webhook request với cùng `gatewayTxnId` (Replay Attack).
  2. Gửi request đến `POST /api/payments/momo-webhook` với `gatewayTxnId` đã được xử lý ở Scenario 2.1.
- **Expected Results**:
  - Hệ thống kiểm tra `store.check_txn_exists(gatewayTxnId)` trong O(1).
  - Trả về status `"success"` với thông điệp: `"Giao dịch đã tồn tại, bỏ qua xử lý lặp."`
  - Số dư quỹ Escrow và Sổ cái Ledger **KHÔNG bị tăng khống lần thứ hai**.

---

## Scenario 2.3: Auto-Lock When Campaign Goal is Reached (Funded Protection)
- **Steps**:
  1. Dự án có `target_amount = 30.000.000đ` và hiện đã nhận đủ `30.000.000đ`.
  2. Trạng thái dự án tự động chuyển sang `funded`.
  3. Cố tình gửi thêm một giao dịch ủng hộ `500.000đ` qua MoMo Webhook.
- **Expected Results**:
  - Webhook từ chối với HTTP 400: `"Dự án này đã đạt đủ mục tiêu tài chính. Hệ thống tự động khóa sổ, không nhận thêm Quyên góp."`
  - Đảm bảo tính minh bạch, chống huy động vốn vượt mức cam kết ban đầu.

---

## Scenario 2.4: Escrow Balance Overdraw Protection
- **Steps**:
  1. Dự án có tổng tiền quyên góp `raised_amount = 21.000.000đ`, đã giải ngân mốc 1 (`12.000.000đ`) và mốc 2 (`8.000.000đ`).
  2. Số dư khả dụng còn lại trong ví Escrow là `1.000.000đ`.
  3. Admin hoặc Chủ dự án yêu cầu giải ngân mốc 3 có giá trị `10.000.000đ`.
- **Expected Results**:
  - Backend kiểm tra `available_balance < milestone.target_amount`.
  - Trả về HTTP 400: `"Quỹ không đủ! Khả dụng: 1,000,000đ, Cần: 10,000,000đ"` (hoặc `"Số dư quỹ Escrow không đủ!"`).
  - Tuyệt đối ngăn chặn hành vi rút thấu chi hoặc bội chi ví Ký quỹ.

---

## Scenario 2.5: Admin Audit & Milestone Release Approval
- **Steps**:
  1. Đăng nhập tài khoản Admin `admin@gmail.com`, mở `http://127.0.0.1:8000/admin.html`.
  2. Chọn mục **Kiểm duyệt Giải ngân Ký quỹ (Escrow Release)**.
  3. Kiểm tra chứng từ thi công mốc hợp lệ.
  4. Bấm nút **Phê duyệt Giải ngân Mốc**.
- **Expected Results**:
  - Gọi API `POST /api/admin/release-milestone`.
  - Mốc Milestone chuyển từ `locked` ➔ `released` kèm thời gian `released_at`.
  - Tạo bút toán chi trong Sổ cái Ledger: `-X.000.000đ Giải ngân mốc [Tên mốc]`.
  - Phát sự kiện WebSocket `MILESTONE_RELEASED` tới toàn bộ người dùng đang theo dõi Live Feed.
  - Gửi thông báo hệ thống Notification tới chủ dự án.

---

## Scenario 2.6: AI-Powered Milestone Disbursement Pre-Audit (ONNX Auditor)
- **Steps**:
  1. Gọi API giải ngân mốc `POST /api/payments/disburse/{project_id}` với `milestone_index`.
  2. Hệ thống chuyển 11 chỉ số vận tốc dòng tiền & tỷ lệ rút vốn vào mô hình AI `fraud_score_model.onnx`.
  3. **Trường hợp An toàn** *(tỷ lệ rút vốn tự nhiên, KYC đầy đủ)*:
     - AI Risk Score `< 30%` ➔ Status `SAFE`, Action `AUTO_APPROVE`.
     - Giải ngân thành công và cập nhật Sổ cái.
  4. **Trường hợp Rủi ro / Bất thường** *(rút vốn đột biến > 40% hoặc phát hiện rửa tiền)*:
     - AI Risk Score `> 50%` (ví dụ: `99.99%`) ➔ Status `FRAUD`, Action `AUTO_BLOCK`.
     - API trả về HTTP 403 Forbidden kèm toàn bộ báo cáo AI Audit Report:
       ```json
       {
         "project_id": "proj_1",
         "risk_score_percent": 99.99,
         "status": "FRAUD",
         "action": "AUTO_BLOCK",
         "explanations": [
           "Tỷ lệ tài khoản ảo (clone) nạp tiền chiếm tỷ trọng quá lớn (>90%).",
           "Mô hình dòng tiền trùng khớp với hành vi rửa tiền đã từng bị cảnh báo."
         ]
       }
       ```
     - Tự động phạt cộng thêm `+30` điểm vào `ai_flags.fraud_score` của dự án và gắn cờ cảnh báo quản trị viên.
