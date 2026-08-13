"""
LocalVest — Python Hybrid Data Store (Memory / SQLite / Supabase PostgreSQL)
Architected by Senior Backend Architect for 0-Cost Student Deployment.
"""

import math
from typing import Dict, List, Any
from datetime import datetime

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates 3-5km radius distance using Haversine formula."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class LocalVestStore:
    def __init__(self):
        self.users: List[Dict[str, Any]] = [
            {
                "id": "usr_admin",
                "email": "admin@localvest.vn",
                "full_name": "System Admin",
                "role": "admin",
                "kyc_status": "approved",
                "is_locked": False,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "usr_demo",
                "email": "demo@localvest.vn",
                "full_name": "Nguyễn Văn Demo",
                "role": "backer",
                "kyc_status": "approved",
                "is_locked": False,
                "created_at": datetime.now().isoformat()
            }
        ]
        self.projects: List[Dict[str, Any]] = [
            {
                "id": "proj_1",
                "name": "Phòng học miễn phí cho trẻ em xóm trọ",
                "category": "Giáo dục",
                "icon": "🎓",
                "cover": "cover-a",
                "location_name": "Phường Bình Hưng Hoà, Q. Bình Tân",
                "target_amount": 30000000.0,
                "raised_amount": 21000000.0,
                "status": "active",
                "lat": 10.7889,
                "lng": 106.6809,
                "description": "Cải tạo một phòng sinh hoạt cộng đồng thành lớp học miễn phí buổi tối cho khoảng 25 em nhỏ có hoàn cảnh khó khăn.",
                "creator_name": "Nguyễn Thị Mai",
                "creator_verified": True,
                "milestones": [
                    {"id": "m1", "name": "Sửa chữa phòng học, lắp bàn ghế", "target_amount": 12000000.0, "status": "released", "desc": "Đã giải ngân"},
                    {"id": "m2", "name": "Mua sách vở, dụng cụ học tập", "target_amount": 8000000.0, "status": "released", "desc": "Đã giải ngân"},
                    {"id": "m3", "name": "Duy trì chi phí điện nước 6 tháng", "target_amount": 10000000.0, "status": "locked", "desc": "Sẽ giải ngân khi vận hành"}
                ]
            },
            {
                "id": "proj_2",
                "name": "Trạm tái chế nhựa khu phố 4",
                "category": "Môi trường",
                "icon": "♻️",
                "cover": "cover-b",
                "location_name": "Phường Tân Định, Q.1",
                "target_amount": 45000000.0,
                "raised_amount": 45000000.0,
                "status": "funded",
                "lat": 10.7689,
                "lng": 106.7109,
                "description": "Lắp đặt trạm thu gom và phân loại rác nhựa tự động, kết nối đơn vị tái chế.",
                "creator_name": "Trần Văn Khoa",
                "creator_verified": True,
                "milestones": [
                    {"id": "m4", "name": "Mua thùng phân loại", "target_amount": 25000000.0, "status": "released", "desc": "Đã hoàn thành"},
                    {"id": "m5", "name": "Lắp mái che", "target_amount": 10000000.0, "status": "released", "desc": "Đã hoàn thành"},
                    {"id": "m6", "name": "Vận hành thử 3 tháng", "target_amount": 10000000.0, "status": "released", "desc": "Đã hoàn thành"}
                ]
            }
        ]
        self.ledger: List[Dict[str, Any]] = [
            {
                "id": "tx_1",
                "project_id": "proj_1",
                "user_name": "Trần Văn A",
                "amount": 500000.0,
                "type": "escrow_deposit",
                "gateway": "momo",
                "description": "+500.000đ từ Trần Văn A (Ký quỹ Escrow)",
                "created_at": datetime.now().isoformat()
            }
        ]
        self.ai_flags: List[Dict[str, Any]] = [
            {
                "id": "flag_1",
                "project_id": "proj_1",
                "fraud_score": 12,
                "is_suspicious": False,
                "reasons": ["Nội dung minh bạch", "Không phát hiện trùng lặp ảnh"]
            }
        ]
        self.kyc_docs: List[Dict[str, Any]] = []
        self.otp_store: Dict[str, Any] = {}

store = LocalVestStore()
