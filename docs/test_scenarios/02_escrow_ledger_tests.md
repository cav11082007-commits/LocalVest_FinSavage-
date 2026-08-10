# 🧪 Test Scenario 02: Escrow Double-Entry Ledger & Milestone Disbursement

## Overview
Kiểm thử tính minh bạch của ví Ký quỹ nội bộ (Escrow) và quy trình giải ngân tiền theo từng cột mốc (Milestone Disbursement).

---

## Scenario 2.1: Backer Financial Deposit into Escrow
- **Preconditions**: Dự án "Phòng học miễn phí cho trẻ em xóm trọ" đang ở trạng thái `active`.
- **Steps**:
  1. Mở trang `http://127.0.0.1:8000/checkout.html?id=proj_1`.
  2. Chọn phương thức thanh toán **MoMo Sandbox QR**.
  3. Nhập số tiền ủng hộ: `200.000đ`.
  4. Nhấn **Xác nhận thanh toán MoMo**.
- **Expected Results**:
  - Webhook `/api/payments/momo-webhook` được gọi.
  - Sổ cái `ledger` tăng ghi nhận dòng tiền `+200.000đ từ Backer (Ký quỹ Escrow)`.
  - Tiền nằm ở tài khoản Escrow an toàn, chủ dự án KHÔNG THỂ tự ý rút tiền.

---

## Scenario 2.2: Admin Audit & Milestone Release Approval
- **Steps**:
  1. Đăng nhập tài khoản Admin `admin@gmail.com`.
  2. Mở Bảng Quản trị Admin `http://127.0.0.1:8000/admin.html`.
  3. Chọn mục **Kiểm duyệt Giải ngân Ký quỹ (Escrow Release)**.
  4. Kiểm tra chứng từ thi công mốc "Sửa chữa phòng học, lắp bàn ghế" (`12.000.000đ`).
  5. Bấm nút **Phê duyệt Giải ngân Mốc 1**.
- **Expected Results**:
  - Mốc Milestone chuyển từ `locked` ➔ `released`.
  - Tạo bút toán giải ngân trong Sổ cái Ledger: `-12.000.000đ Giải ngân mốc Sửa chữa phòng học`.
  - WebSocket phát sự kiện `MILESTONE_RELEASED` tới toàn bộ người dùng đang xem Live Feed.
