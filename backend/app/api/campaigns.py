"""
Campaign Service API Endpoints (CRUD & State Machine)
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, File, UploadFile, Form
import json
import os
import shutil
from app.schemas.schemas import CreateProjectSchema, CampaignListResponse, CampaignDetailResponse
from app.core.security import get_current_user, get_current_user_optional
from app.services.ai_worker import async_ai_flag_checker
from app.store import store

router = APIRouter(prefix="/campaigns", tags=["2. Campaign Service"])

@router.get("", response_model=CampaignListResponse)
def get_campaigns(current_user: dict = Depends(get_current_user_optional)):
    all_projects = store.get_projects()
    if current_user and current_user.get("role") == "admin":
        return {"projects": all_projects}
    
    # Non-admin users only see approved projects
    filtered = [p for p in all_projects if p.get("status") in ("active", "funded", "completed")]
    return {"projects": filtered}

@router.get("/{project_id}", response_model=CampaignDetailResponse)
def get_campaign_detail(project_id: str):
    p = store.get_project_by_id(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    return {"project": p}

@router.get("/{project_id}/ledger")
def get_campaign_ledger(project_id: str):
    ledger = store.get_ledger()
    # Filter for this project
    project_ledger = [e for e in ledger if e["project_id"] == project_id]
    
    # Map to frontend format
    formatted = []
    for e in project_ledger:
        formatted.append({
            "time": e["created_at"],
            "amount": e["amount"],
            "type": "in" if e["type"] == "escrow_deposit" else "out",
            "desc": e["description"]
        })
    return {"ledger": formatted}

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "backend", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
def create_campaign(
    background_tasks: BackgroundTasks,
    payload: str = Form(...),
    project_images: list[UploadFile] = File([]),
    kyc_front: UploadFile = File(None),
    kyc_back: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in payload")

    # Xử lý lưu ảnh dự án
    cover_path = "cover-a" # Default
    images_paths = []
    
    projects_dir = os.path.join(UPLOAD_DIR, "projects", project_id)
    os.makedirs(projects_dir, exist_ok=True)
    
    for idx, img in enumerate(project_images):
        if img:
            filename = f"img_{idx}_{img.filename}"
            with open(os.path.join(projects_dir, filename), "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            images_paths.append(f"/uploads/projects/{project_id}/{filename}")
            
    if images_paths:
        cover_path = images_paths[0]

    user = store.get_user_by_id(current_user["sub"])
    is_verified = bool(user and user.get("kyc_status") == "approved")

    # Xử lý lưu ảnh KYC
    if not is_verified and (kyc_front or kyc_back):
        front_url, back_url = "", ""
        kyc_dir = os.path.join(UPLOAD_DIR, "kyc", project_id)
        os.makedirs(kyc_dir, exist_ok=True)
        
        if kyc_front:
            front_filename = f"kyc_front_{kyc_front.filename}"
            with open(os.path.join(kyc_dir, front_filename), "wb") as buffer:
                shutil.copyfileobj(kyc_front.file, buffer)
            front_url = f"/uploads/kyc/{project_id}/{front_filename}"
        if kyc_back:
            back_filename = f"kyc_back_{kyc_back.filename}"
            with open(os.path.join(kyc_dir, back_filename), "wb") as buffer:
                shutil.copyfileobj(kyc_back.file, buffer)
            back_url = f"/uploads/kyc/{project_id}/{back_filename}"
            
        kyc_record = {
            "id": f"kyc_{uuid.uuid4().hex[:8]}",
            "user_id": current_user["sub"],
            "doc_type": "cccd",
            "doc_number": "N/A",  # MVP doesn't extract ID yet
            "front_image_url": front_url,
            "back_image_url": back_url,
            "status": "pending",
            "submitted_at": datetime.now().isoformat()
        }
        store.create_kyc_doc(kyc_record)

    milestones_list = []
    for idx, m in enumerate(data.get("milestones", [])):
        milestones_list.append({
            "id": f"m_{idx+1}_{uuid.uuid4().hex[:4]}",
            "name": m.get("name"),
            "target_amount": m.get("target_amount"),
            "status": "locked",
            "desc": m.get("description", "Chờ giải ngân")
        })

    new_project = {
        "id": project_id,
        "owner_id": current_user["sub"],
        "name": data.get("name"),
        "category": data.get("category"),
        "icon": "🌱",
        "cover": cover_path,
        "images": images_paths,
        "description": data.get("description"),
        "location_name": data.get("location_name"),
        "target_amount": data.get("target_amount"),
        "raised_amount": 0.0,
        "status": "pending_review",
        "lat": data.get("lat"),
        "lng": data.get("lng"),
        "creator_name": current_user["email"],
        "creator_verified": is_verified,
        "milestones": milestones_list,
        "created_at": datetime.now().isoformat()
    }
    store.create_project(new_project)

    background_tasks.add_task(async_ai_flag_checker, project_id, new_project["name"], new_project["description"])

    return {
        "message": "Tạo dự án thành công. Trạng thái: pending_review (Đang chờ AI & Admin).",
        "project": new_project
    }
