# 🧪 Test Scenario 03: AI Fraud Shield Anomaly Detection

## Overview
Kiểm thử tính năng quét gian lận tự động (Non-Blocking Background Worker) bằng thuật toán NLP & pHash Similarity.

---

## Scenario 3.1: Submitting Suspicious Campaign
- **Steps**:
  1. Đăng nhập tài khoản Project Owner.
  2. Mở trang `http://127.0.0.1:8000/submit_project.html`.
  3. Nhập tên dự án: `Bếp ăn 0 đồng gấp lắm chuyển khoản cá nhân`.
  4. Nhập mô tả có chứa từ khóa nghi vấn: `Cần tiền gấp lắm, lừa đảo copy crypto chuyển khoản cá nhân ngay`.
  5. Bấm **Gửi duyệt dự án**.
- **Expected Results**:
  - Dự án ở trạng thái `pending_review` (chờ duyệt).
  - Background worker `async_ai_flag_checker` kích hoạt ngầm, không làm treo UI.
  - Điểm nguy cơ gian lận `fraud_score` tăng lên `> 50%` (VD: 80%).

---

## Scenario 3.2: Admin Fraud Inspection & One-Click Account Lock
- **Steps**:
  1. Đăng nhập Admin `admin@gmail.com` và truy cập `admin.html`.
  2. Tại hàng dự án nghi vấn, cột **Điểm nguy cơ AI** hiển thị Badge màu đỏ `80%`.
  3. Bấm xem chi tiết lý do AI: `Phát hiện từ khóa nghi vấn: 'chuyển khoản cá nhân', 'lừa đảo'`.
  4. Nhấn nút **Từ chối / Khóa tài khoản gian lận**.
- **Expected Results**:
  - Dự án chuyển trạng thái `rejected`.
  - Tài khoản gian lận bị đặt `is_locked: True`.
  - Nếu tài khoản này cố tình đăng nhập lại sẽ nhận thông báo: "Tài khoản đã bị khóa do gian lận."
