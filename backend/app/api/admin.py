"""
Admin & Moderation Service API Endpoints
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.schemas import AdminApproveSchema, AdminReleaseMilestoneSchema
from app.core.security import get_current_user, require_admin
from app.services.realtime import realtime_manager
from app.core.campaign_state_machine import transition
from app.store import store
from app.database.db import get_db_connection

router = APIRouter(prefix="/admin", tags=["6. Admin/Moderation Service"])

@router.get("/pending-projects")
def get_pending_projects(current_user: dict = Depends(require_admin)):
    projects = store.get_projects()
    pending = [p for p in projects if p["status"] == "pending_review"]
    return {"count": len(pending), "projects": pending}

@router.get("/kyc")
def get_kyc_documents(current_user: dict = Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT k.id, k.user_id, k.doc_type, k.doc_number, k.front_image_url, k.back_image_url, k.status, MAX(k.submitted_at) as submitted_at, u.email 
        FROM kyc_documents k
        JOIN users u ON k.user_id = u.id
        GROUP BY k.user_id
        ORDER BY submitted_at DESC
    """)
    docs = [dict(row) for row in cur.fetchall()]
    conn.close()
    return {"kyc_docs": docs}

@router.post("/kyc/{kyc_id}/status")
def update_kyc_status(kyc_id: str, payload: dict, current_user: dict = Depends(require_admin)):
    status = payload.get("status")
    if status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE kyc_documents SET status = ? WHERE id = ?", (status, kyc_id))
    
    if status == "approved":
        # Also update user kyc_status
        cur.execute("UPDATE users SET kyc_status = 'approved' WHERE id = (SELECT user_id FROM kyc_documents WHERE id = ?)", (kyc_id,))
        # Update projects to verified
        cur.execute("UPDATE projects SET creator_verified = 1 WHERE owner_id = (SELECT user_id FROM kyc_documents WHERE id = ?)", (kyc_id,))
        
    conn.commit()
    conn.close()
    return {"message": f"KYC {status}"}

@router.post("/approve-project")
def admin_approve_project(data: AdminApproveSchema, current_user: dict = Depends(require_admin)):
    p = store.get_project_by_id(data.projectId)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    new_status = "active" if data.approve else "rejected"
    # Wait, transition() updates the dictionary, but we need to save it to DB
    # We can just call store.update_project_status instead of transition, 
    # but transition has logic. We will call store.update_project_status directly.
    store.update_project_status(data.projectId, new_status)
    p["status"] = new_status
    return {"message": f"Dự án đã được {'duyệt active' if data.approve else 'từ chối'}", "project": p}


@router.post("/release-milestone")
async def admin_release_milestone(data: AdminReleaseMilestoneSchema, current_user: dict = Depends(require_admin)):
    p = store.get_project_by_id(data.projectId)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    if p["status"] not in ("active", "funded"):
        raise HTTPException(status_code=400, detail=f"Không thể giải ngân khi dự án đang '{p['status']}'")
    m = next((m_item for m_item in p.get("milestones", []) if m_item["id"] == data.milestoneId), None)
    if not m:
        raise HTTPException(status_code=404, detail="Không tìm thấy mốc giải ngân")
    
    # Tính số dư khả dụng (Raised - Tổng các mốc đã released)
    total_released = sum(ms["target_amount"] for ms in p.get("milestones", []) if ms["status"] == "released")
    available_balance = p.get("raised_amount", 0) - total_released
    
    if available_balance < m["target_amount"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Quỹ không đủ! Khả dụng: {available_balance:,.0f}đ, Cần: {m['target_amount']:,.0f}đ"
        )
    
    store.update_milestone_status(data.milestoneId, "released")
    m["status"] = "released"

    disbursement_entry = {
        "id": f"tx_out_{uuid.uuid4().hex[:8]}",
        "project_id": p["id"],
        "amount": m["target_amount"],
        "type": "milestone_release",
        "description": f"Giải ngân mốc '{m['name']}' (-{m['target_amount']:,.0f}đ)",
        "created_at": datetime.now().isoformat()
    }
    store.add_ledger_entry(disbursement_entry)

    # Realtime Live Feed Broadcast
    await realtime_manager.broadcast("MILESTONE_RELEASED", {
        "projectId": p["id"],
        "projectName": p["name"],
        "milestoneName": m["name"],
        "amount": m["target_amount"]
    })

    return {"message": "Giải ngân thành công!", "milestone": m, "ledger": disbursement_entry}
