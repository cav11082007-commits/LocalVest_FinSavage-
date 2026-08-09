"""
Campaign Service API Endpoints (CRUD & State Machine)
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from app.schemas.schemas import CreateProjectSchema
from app.core.security import get_current_user
from app.services.ai_worker import async_ai_flag_checker
from app.store import store

router = APIRouter(prefix="/campaigns", tags=["2. Campaign Service"])

@router.get("")
def get_campaigns():
    return {"projects": store.projects}

@router.get("/{project_id}")
def get_campaign_detail(project_id: str):
    p = next((proj for proj in store.projects if proj["id"] == project_id), None)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    return {"project": p}

@router.post("")
def create_campaign(data: CreateProjectSchema, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    project_id = f"proj_{uuid.uuid4().hex[:8]}"

    milestones_list = []
    for idx, m in enumerate(data.milestones):
        milestones_list.append({
            "id": f"m_{idx+1}_{uuid.uuid4().hex[:4]}",
            "name": m.name,
            "target_amount": m.target_amount,
            "status": "locked",
            "desc": m.description or "Chờ giải ngân"
        })

    new_project = {
        "id": project_id,
        "owner_id": current_user["sub"],
        "name": data.name,
        "category": data.category,
        "icon": "🌱",
        "cover": "cover-a",
        "description": data.description,
        "location_name": data.location_name,
        "target_amount": data.target_amount,
        "raised_amount": 0.0,
        "status": "pending_review",
        "lat": data.lat,
        "lng": data.lng,
        "creator_name": current_user["email"],
        "milestones": milestones_list,
        "created_at": datetime.now().isoformat()
    }
    store.projects.append(new_project)

    background_tasks.add_task(async_ai_flag_checker, project_id, data.name, data.description)

    return {
        "message": "Tạo dự án thành công. Trạng thái: pending_review (Đang chờ AI & Admin).",
        "project": new_project
    }
