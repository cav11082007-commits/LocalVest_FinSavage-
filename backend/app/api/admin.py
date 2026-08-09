"""
Admin & Moderation Service API Endpoints
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.schemas import AdminApproveSchema, AdminReleaseMilestoneSchema
from app.core.security import get_current_user
from app.services.realtime import realtime_manager
from app.store import store

router = APIRouter(prefix="/admin", tags=["6. Admin/Moderation Service"])

@router.get("/pending-projects")
def get_pending_projects(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền truy cập")
    pending = [p for p in store.projects if p["status"] == "pending_review"]
    return {"count": len(pending), "projects": pending}

@router.post("/approve-project")
def admin_approve_project(data: AdminApproveSchema, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền truy cập")
    p = next((proj for proj in store.projects if proj["id"] == data.projectId), None)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")

    p["status"] = "active" if data.approve else "closed"
    return {"message": f"Dự án đã được {'duyệt active' if data.approve else 'từ chối closed'}", "project": p}

@router.post("/release-milestone")
async def admin_release_milestone(data: AdminReleaseMilestoneSchema, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền truy cập")
    p = next((proj for proj in store.projects if proj["id"] == data.projectId), None)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")

    m = next((m_item for m_item in p.get("milestones", []) if m_item["id"] == data.milestoneId), None)
    if not m:
        raise HTTPException(status_code=404, detail="Không tìm thấy mốc giải ngân")

    m["status"] = "released"

    disbursement_entry = {
        "id": f"tx_out_{uuid.uuid4().hex[:8]}",
        "project_id": p["id"],
        "amount": m["target_amount"],
        "type": "milestone_release",
        "description": f"Giải ngân mốc '{m['name']}' (-{m['target_amount']:,.0f}đ)",
        "created_at": datetime.now().isoformat()
    }
    store.ledger.append(disbursement_entry)

    # Realtime Live Feed Broadcast
    await realtime_manager.broadcast("MILESTONE_RELEASED", {
        "projectId": p["id"],
        "projectName": p["name"],
        "milestoneName": m["name"],
        "amount": m["target_amount"]
    })

    return {"message": "Giải ngân thành công!", "milestone": m, "ledger": disbursement_entry}
