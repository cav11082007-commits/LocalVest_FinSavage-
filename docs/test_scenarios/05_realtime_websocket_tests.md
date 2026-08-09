# 🧪 Test Scenario 05: Realtime Live Feed WebSocket Push

## Overview
Kiểm thử tính năng đẩy thông báo dòng tiền tức thời qua WebSocket (`ws://127.0.0.1:8000/ws/live-feed`).

---

## Scenario 5.1: Realtime Transaction Push Notification
- **Steps**:
  1. Mở 2 tab trình duyệt song song: Tab 1 mở `dashboard.html`, Tab 2 mở `checkout.html`.
  2. Tại Tab 2 thực hiện đóng góp `100.000đ`.
- **Expected Results**:
  - Tab 1 lập tức xuất hiện hàng giao dịch mới nhấp nháy (Flash animation) mà **KHÔNG NÊN BẤM F5**.
  - Đồ thị dòng tiền & Tổng số tiền Ký quỹ cập nhật tức thời qua WebSocket.
