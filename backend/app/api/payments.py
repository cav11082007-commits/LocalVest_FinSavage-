"""
Payment & Escrow Service API Endpoints (MoMo Webhook & Ledger)
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.schemas.schemas import MoMoWebhookSchema
from app.services.realtime import realtime_manager
from app.store import store

router = APIRouter(prefix="/payments", tags=["3. Payment & Escrow Service"])

@router.post("/momo-webhook")
async def momo_webhook(data: MoMoWebhookSchema):
    project = next((p for p in store.projects if p["id"] == data.projectId), None)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại")

    project["raised_amount"] += data.amount
    if project["raised_amount"] >= project["target_amount"] and project["status"] == "active":
        project["status"] = "funded"

    ledger_entry = {
        "id": f"tx_{uuid.uuid4().hex[:8]}",
        "project_id": data.projectId,
        "user_name": data.backerName or "Nhà tài trợ ẩn danh",
        "amount": data.amount,
        "type": "escrow_deposit",
        "gateway": "momo",
        "gateway_txn_id": data.gatewayTxnId or f"MOMO_{int(datetime.now().timestamp())}",
        "description": f"+{data.amount:,.0f}đ từ {data.backerName} (Ký quỹ Escrow)",
        "created_at": datetime.now().isoformat()
    }
    store.ledger.append(ledger_entry)

    # Push to Realtime Live Feed WebSocket
    await realtime_manager.broadcast("NEW_TRANSACTION", {
        "projectId": project["id"],
        "projectName": project["name"],
        "backerName": ledger_entry["user_name"],
        "amount": data.amount,
        "raisedTotal": project["raised_amount"],
        "targetTotal": project["target_amount"]
    })

    return {"status": "success", "message": "Ghi nhận đóng góp Escrow thành công", "ledger": ledger_entry}
