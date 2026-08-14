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

router = APIRouter(prefix="/admin", tags=["6. Admin/Moderation Service"])

@router.get("/pending-projects")
def get_pending_projects(current_user: dict = Depends(require_admin)):
    pending = [p for p in store.projects if p["status"] == "pending_review"]
    return {"count": len(pending), "projects": pending}

@router.post("/approve-project")
def admin_approve_project(data: AdminApproveSchema, current_user: dict = Depends(require_admin)):
    p = next((proj for proj in store.projects if proj["id"] == data.projectId), None)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    new_status = "active" if data.approve else "rejected"
    transition(p, new_status, actor=f"admin:{current_user['sub']}")
    return {"message": f"Dự án đã được {'duyệt active' if data.approve else 'từ chối'}", "project": p}


@router.post("/release-milestone")
async def admin_release_milestone(data: AdminReleaseMilestoneSchema, current_user: dict = Depends(require_admin)):
    p = next((proj for proj in store.projects if proj["id"] == data.projectId), None)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    if p["status"] not in ("active", "funded"):
        raise HTTPException(status_code=400, detail=f"Không thể giải ngân khi dự án đang '{p['status']}'")
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
