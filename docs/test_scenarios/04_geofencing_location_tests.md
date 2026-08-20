# 🧪 Test Scenario 04: Hyperlocal Geofencing 3-5km Radius & Dynamic Expanding Query

## Overview
Kiểm thử tính năng định vị không gian 2 pha (Two-Phase Spatial Indexing: Bounding Box Filter + Haversine Formula) tìm kiếm dự án cộng đồng xung quanh người dùng trong bán kính 3-5km và cơ chế tự động mở rộng bán kính (Dynamic Auto-Expanding Radius).

---

## Scenario 4.1: Query Nearby Projects in HCM Q.1 (3km Radius)
- **Steps**:
  1. Mở trang [http://127.0.0.1:8000/home.html](http://127.0.0.1:8000/home.html).
  2. Bấm chọn bán kính lọc **3km** quanh vị trí trung tâm TP.HCM (Lat: `10.7769`, Lng: `106.7009`).
  3. Giao diện gọi API `GET /api/location/nearby?lat=10.7769&lng=106.7009&radius_km=3.0`.
- **Expected Results**:
  - API tính toán khoảng cách thực tế giữa tọa độ người dùng và tọa độ từng dự án bằng công thức Haversine:
    $$d = 2R \cdot \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \text{lat}}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta \text{lon}}{2}\right)}\right)$$
  - Trả về danh sách dự án nằm trong phạm vi 3km (ví dụ: dự án tại Tân Định `1.6 km`).
  - Danh sách được sắp xếp tăng dần theo khoảng cách gần nhất lên đầu.
  - Mỗi dự án trả về trường `distanceKm` (làm tròn 1 chữ số thập phân).

---

## Scenario 4.2: Dynamic Auto-Expanding Search Radius (Mở rộng bán kính tự động)
- **Steps**:
  1. Người dùng ở một tọa độ ngoại ô hoặc khu vực ít dự án (ví dụ: Lat: `10.8500`, Lng: `106.6000`).
  2. Chọn bán kính tìm kiếm ban đầu `3.0 km`.
  3. Trong bán kính 3km không có dự án nào (`count = 0`).
- **Expected Results**:
  - Hệ thống tự động kích hoạt cơ chế Fallback mở rộng bán kính tìm kiếm lên `10.0 km`.
  - Phản hồi API trả về `radius_km: 10.0` kèm theo các dự án tìm thấy ở bán kính mở rộng.
  - Người dùng không bị màn hình trắng/trống trơn, nâng cao trải nghiệm khám phá.

---

## Scenario 4.3: Two-Phase Spatial Filter Efficiency & Accuracy
- **Steps**:
  1. Gửi request `GET /api/location/nearby` với dữ liệu lớn nhiều dự án trên bản đồ.
- **Expected Results**:
  - **Pha 1 (Fast Bounding Box)**: Truy vấn SQL lọc nhanh theo hộp tọa độ `min_lat/max_lat` và `min_lon/max_lon` giúp giảm 90% tập dữ liệu cần tính toán.
  - **Pha 2 (Haversine Precision)**: Tính toán chính xác khoảng cách cầu mặt đất để loại bỏ các điểm ở góc hộp nằm ngoài đường tròn bán kính.
  - Thời gian xử lý API đạt hiệu năng cực cao `< 20ms`.
  - Toàn bộ metadata dự án (Badge xác thực `creator_verified`, ảnh bìa, tiến độ gọi vốn) được trả về đầy đủ.
