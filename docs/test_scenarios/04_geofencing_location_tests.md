# 🧪 Test Scenario 04: Hyperlocal Geofencing 3-5km Radius Query

## Overview
Kiểm thử tính năng định vị không gian PostGIS / Haversine tìm dự án cộng đồng trong bán kính 3-5km quanh người dùng.

---

## Scenario 4.1: Query Nearby Projects in HCM Q.1
- **Steps**:
  1. Mở trang `http://127.0.0.1:8000/home.html`.
  2. Bấm nút chọn bán kính `3km` hoặc `5km`.
  3. Hệ thống gửi request API `/api/location/nearby?lat=10.7769&lng=106.7009&radius_km=3.0`.
- **Expected Results**:
  - Trả về danh sách dự án trong bán kính 3km kèm chỉ số khoảng cách (VD: `1.2 km`, `2.8 km`).
  - Sắp xếp dự án theo khoảng cách gần nhất lên đầu.
