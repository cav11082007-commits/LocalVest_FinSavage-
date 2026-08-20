"""
AI-Flag Service API Endpoints
"""

from fastapi import APIRouter
from app.store import store

router = APIRouter(prefix="/ai-flag", tags=["5. AI-Flag Service"])

@router.get("/{project_id}")
def get_ai_flag_result(project_id: str):
    flag = store.get_ai_flag(project_id)
    return {"flag": flag or {"fraud_score": 0, "is_suspicious": False, "reasons": ["Chưa ghi nhận rủi ro"]}}
