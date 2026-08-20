from fastapi import APIRouter, HTTPException
from app.config import settings
from app.core.campaign_state_machine import transition
from app.store import store

router = APIRouter(prefix="/test", tags=["TEST-ONLY"])

@router.post("/mock-payment-success")
def mock_payment_success(project_id: str, amount: float):
    if settings.ENV == "prod":
        raise HTTPException(status_code=404, detail="Not found")
    p = store.get_project_by_id(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    store.update_project_raised_amount(project_id, amount)
    # Reload project to get updated state
    p = store.get_project_by_id(project_id)
    return {"message": "Mock payment thành công", "project": p}