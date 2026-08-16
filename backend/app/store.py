"""
LocalVest — Database Store Wrapper (SQLite)
Architected by Senior Backend Architect for MVP Persistence.
"""

import math
import json
from datetime import datetime
from typing import Dict, List, Any
from app.core.security import hash_password
from app.config import settings
from app.database.db import get_db_connection, is_db_empty, init_db

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
        self.otp_store: Dict[str, Any] = {}
        if is_db_empty():
            self._seed_data()

    def _seed_data(self):
        conn = get_db_connection()
        cur = conn.cursor()
        now = datetime.now().isoformat()
        
        # Seed users
        admin_pass = hash_password(settings.DEFAULT_ADMIN_PASSWORD)
        demo_pass = hash_password("Demo@1234")
        cur.executemany(
            "INSERT INTO users (id, email, password_hash, full_name, role, kyc_status, is_locked, alt_emails, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("usr_admin", "admin@localvest.vn", admin_pass, "System Admin", "admin", "approved", False, json.dumps(["admin@gmail.com"]), now, now),
                ("usr_demo", "demo@localvest.vn", demo_pass, "Nguyễn Văn Demo", "backer", "approved", False, "[]", now, now)
            ]
        )

        # Seed projects
        cur.executemany(
            "INSERT INTO projects (id, owner_id, name, category, icon, cover, description, location_name, target_amount, raised_amount, status, lat, lng, creator_name, creator_verified, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("proj_1", "usr_demo", "Phòng học miễn phí cho trẻ em xóm trọ", "Giáo dục", "🎓", "cover-a", "Cải tạo một phòng sinh hoạt cộng đồng thành lớp học miễn phí buổi tối cho khoảng 25 em nhỏ có hoàn cảnh khó khăn.", "Phường Bình Hưng Hoà, Q. Bình Tân", 30000000.0, 21000000.0, "active", 10.7889, 106.6809, "Nguyễn Thị Mai", True, now, now),
                ("proj_2", "usr_demo", "Trạm tái chế nhựa khu phố 4", "Môi trường", "♻️", "cover-b", "Lắp đặt trạm thu gom và phân loại rác nhựa tự động, kết nối đơn vị tái chế.", "Phường Tân Định, Q.1", 45000000.0, 45000000.0, "funded", 10.7689, 106.7109, "Trần Văn Khoa", True, now, now)
            ]
        )

        # Seed milestones
        cur.executemany(
            "INSERT INTO milestones (id, project_id, name, target_amount, released_amount, status, description, order_index, released_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("m1", "proj_1", "Sửa chữa phòng học, lắp bàn ghế", 12000000.0, 12000000.0, "released", "Đã giải ngân", 1, now),
                ("m2", "proj_1", "Mua sách vở, dụng cụ học tập", 8000000.0, 8000000.0, "released", "Đã giải ngân", 2, now),
                ("m3", "proj_1", "Duy trì chi phí điện nước 6 tháng", 10000000.0, 0, "locked", "Sẽ giải ngân khi vận hành", 3, None),
                ("m4", "proj_2", "Mua thùng phân loại", 25000000.0, 25000000.0, "released", "Đã hoàn thành", 1, now),
                ("m5", "proj_2", "Lắp mái che", 10000000.0, 10000000.0, "released", "Đã hoàn thành", 2, now),
                ("m6", "proj_2", "Vận hành thử 3 tháng", 10000000.0, 10000000.0, "released", "Đã hoàn thành", 3, now)
            ]
        )

        # Seed ledger
        cur.executemany(
            "INSERT INTO ledger (id, project_id, user_name, amount, type, gateway, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("tx_1_in", "proj_1", "Trần Văn A", 21000000.0, "escrow_deposit", "momo", "+21.000.000đ từ Trần Văn A (Ký quỹ Escrow)", now),
                ("tx_1_out_1", "proj_1", "Hệ thống", 12000000.0, "milestone_release", "bank", "Giải ngân mốc: Sửa chữa phòng học, lắp bàn ghế", now),
                ("tx_1_out_2", "proj_1", "Hệ thống", 8000000.0, "milestone_release", "bank", "Giải ngân mốc: Mua sách vở, dụng cụ học tập", now),
                
                ("tx_2_in", "proj_2", "Nguyễn Thị B", 45000000.0, "escrow_deposit", "momo", "+45.000.000đ từ Nguyễn Thị B (Ký quỹ Escrow)", now),
                ("tx_2_out_1", "proj_2", "Hệ thống", 25000000.0, "milestone_release", "bank", "Giải ngân mốc: Mua thùng phân loại", now),
                ("tx_2_out_2", "proj_2", "Hệ thống", 10000000.0, "milestone_release", "bank", "Giải ngân mốc: Lắp mái che", now),
                ("tx_2_out_3", "proj_2", "Hệ thống", 10000000.0, "milestone_release", "bank", "Giải ngân mốc: Vận hành thử 3 tháng", now)
            ]
        )

        # Seed ai_flags
        cur.execute(
            "INSERT INTO ai_flags (id, project_id, fraud_score, is_suspicious, reasons, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("flag_1", "proj_1", 12, False, json.dumps(["Nội dung minh bạch", "Không phát hiện trùng lặp ảnh"]), "pending_review", now)
        )

        conn.commit()
        conn.close()

    def find_user_by_identifier(self, target: str):
        target = (target or "").strip().lower()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = [dict(row) for row in cur.fetchall()]
        conn.close()

        for u in users:
            if u["email"].lower() == target:
                u["alt_emails"] = json.loads(u["alt_emails"]) if u["alt_emails"] else []
                return u
            alt_emails = json.loads(u["alt_emails"]) if u["alt_emails"] else []
            if target in [e.lower() for e in alt_emails]:
                u["alt_emails"] = alt_emails
                return u
        return None

    def get_user_by_id(self, user_id: str):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            u = dict(row)
            u["alt_emails"] = json.loads(u["alt_emails"]) if u["alt_emails"] else []
            return u
        return None

    def create_user(self, user_data: dict):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (id, email, password_hash, full_name, role, kyc_status, alt_emails, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_data["id"], user_data["email"], user_data["password_hash"], user_data["full_name"], user_data.get("role", "backer"), user_data.get("kyc_status", "pending"), json.dumps(user_data.get("alt_emails", [])), user_data.get("created_at", datetime.now().isoformat()), datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

    def get_projects(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects")
        projects = [dict(row) for row in cur.fetchall()]
        
        for p in projects:
            p['creator_verified'] = bool(p['creator_verified'])
            cur.execute("SELECT * FROM milestones WHERE project_id = ? ORDER BY order_index", (p["id"],))
            p["milestones"] = [dict(row) for row in cur.fetchall()]
            
            cur.execute("SELECT * FROM ai_flags WHERE project_id = ?", (p["id"],))
            flag = cur.fetchone()
            if flag:
                f = dict(flag)
                f["is_suspicious"] = bool(f["is_suspicious"])
                f["reasons"] = json.loads(f["reasons"]) if f["reasons"] else []
                # map for frontend
                p["fraudFlag"] = {"score": f["fraud_score"], "reason": f["reasons"][0] if f["reasons"] else "Không phát hiện dấu hiệu bất thường"}
        
        conn.close()
        return projects

    def get_project_by_id(self, project_id: str):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        p = dict(row)
        p['creator_verified'] = bool(p['creator_verified'])
        cur.execute("SELECT * FROM milestones WHERE project_id = ? ORDER BY order_index", (p["id"],))
        p["milestones"] = [dict(row) for row in cur.fetchall()]
        
        cur.execute("SELECT * FROM ai_flags WHERE project_id = ?", (p["id"],))
        flag = cur.fetchone()
        if flag:
            f = dict(flag)
            f["is_suspicious"] = bool(f["is_suspicious"])
            f["reasons"] = json.loads(f["reasons"]) if f["reasons"] else []
            p["fraudFlag"] = {"score": f["fraud_score"], "reason": f["reasons"][0] if f["reasons"] else "Không phát hiện dấu hiệu bất thường"}
            
        conn.close()
        return p

    def create_project(self, project_data: dict):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO projects (id, owner_id, name, category, icon, cover, description, location_name, target_amount, raised_amount, status, lat, lng, creator_name, creator_verified, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project_data["id"], project_data["owner_id"], project_data["name"], project_data["category"], project_data.get("icon", "🌱"), project_data.get("cover", "cover-a"), project_data["description"], project_data["location_name"], project_data["target_amount"], project_data.get("raised_amount", 0), project_data.get("status", "pending_review"), project_data["lat"], project_data["lng"], project_data["creator_name"], project_data.get("creator_verified", False), project_data.get("created_at", datetime.now().isoformat()), datetime.now().isoformat())
        )
        
        for idx, m in enumerate(project_data.get("milestones", [])):
            cur.execute(
                "INSERT INTO milestones (id, project_id, name, target_amount, released_amount, status, description, order_index) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (m["id"], project_data["id"], m["name"], m["target_amount"], 0, m.get("status", "locked"), m.get("desc", ""), idx+1)
            )
            
        conn.commit()
        conn.close()

    def update_project_status(self, project_id: str, new_status: str):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE projects SET status = ?, updated_at = ? WHERE id = ?", (new_status, datetime.now().isoformat(), project_id))
        conn.commit()
        conn.close()

    def update_project_raised_amount(self, project_id: str, added_amount: float):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE projects SET raised_amount = raised_amount + ?, updated_at = ? WHERE id = ?", (added_amount, datetime.now().isoformat(), project_id))
        
        # Check if funded
        cur.execute("SELECT target_amount, raised_amount FROM projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        if row and row['raised_amount'] >= row['target_amount']:
            cur.execute("UPDATE projects SET status = 'funded', updated_at = ? WHERE id = ?", (datetime.now().isoformat(), project_id))
            
        conn.commit()
        conn.close()

    def update_milestone_status(self, milestone_id: str, status: str):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE milestones SET status = ?, released_at = ? WHERE id = ?", (status, datetime.now().isoformat() if status == 'released' else None, milestone_id))
        conn.commit()
        conn.close()
        
    def add_ledger_entry(self, entry: dict):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO ledger (id, project_id, user_name, amount, type, gateway, description, gateway_txn_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (entry["id"], entry["project_id"], entry.get("user_name"), entry["amount"], entry["type"], entry.get("gateway", "momo"), entry.get("description"), entry.get("gateway_txn_id"), entry.get("created_at", datetime.now().isoformat()))
        )
        conn.commit()
        conn.close()
        
    def get_ledger(self):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM ledger")
        entries = [dict(row) for row in cur.fetchall()]
        conn.close()
        return entries
        
    def set_ai_flag(self, flag: dict):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM ai_flags WHERE project_id = ?", (flag["project_id"],))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE ai_flags SET fraud_score = ?, is_suspicious = ?, reasons = ?, status = ? WHERE project_id = ?",
                (flag["fraud_score"], flag.get("is_suspicious", False), json.dumps(flag.get("reasons", [])), flag.get("status", "pending_review"), flag["project_id"])
            )
        else:
            cur.execute(
                "INSERT INTO ai_flags (id, project_id, fraud_score, is_suspicious, reasons, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (flag["id"], flag["project_id"], flag["fraud_score"], flag.get("is_suspicious", False), json.dumps(flag.get("reasons", [])), flag.get("status", "pending_review"), datetime.now().isoformat())
            )
        conn.commit()
        conn.close()

    def create_kyc_doc(self, record: dict):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO kyc_documents (id, user_id, doc_type, doc_number, front_image_url, back_image_url, status, submitted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (record["id"], record["user_id"], record["doc_type"], record.get("doc_number"), record["front_image_url"], record.get("back_image_url"), record.get("status", "pending"), record.get("submitted_at", datetime.now().isoformat()))
        )
        conn.commit()
        conn.close()

store = LocalVestStore()
