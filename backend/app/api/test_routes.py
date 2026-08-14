from fastapi import APIRouter, HTTPException
from app.config import settings
from app.core.campaign_state_machine import transition
from app.store import store

router = APIRouter(prefix="/test", tags=["TEST-ONLY"])

@router.post("/mock-payment-success")
def mock_payment_success(project_id: str, amount: float):
    if settings.ENV == "prod":
        raise HTTPException(status_code=404, detail="Not found")
    p = next((proj for proj in store.projects if proj["id"] == project_id), None)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
    p["raised_amount"] = p.get("raised_amount", 0) + amount
    if p["raised_amount"] >= p["target_amount"] and p["status"] == "active":
        transition(p, "funded", actor="system:mock_payment")
    return {"message": "Mock payment thành công", "project": p}