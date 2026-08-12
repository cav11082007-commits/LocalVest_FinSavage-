"""
Payment & Escrow Service API Endpoints (MoMo Webhook & Ledger)
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.schemas.schemas import MoMoWebhookSchema
from app.services.realtime import realtime_manager
from app.services.notifications import notify
from app.store import store

router = APIRouter(prefix="/payments", tags=["3. Payment & Escrow Service"])

@router.get("/ledger/{project_id}")
def get_ledger(project_id: str):
    """Đọc sổ cái escrow của một dự án — cần cho dashboard nạp trạng thái ban đầu
    trước khi lắng nghe cập nhật tiếp theo qua WebSocket /ws/live-feed."""
    entries = [e for e in store.ledger if e["project_id"] == project_id]
    total_in = sum(e["amount"] for e in entries if e["type"] == "escrow_deposit")
    total_out = sum(e["amount"] for e in entries if e["type"] == "milestone_release")
    return {
        "projectId": project_id,
        "ledger": entries,
        "totalIn": total_in,
        "totalOut": total_out,
        "balance": total_in - total_out,
    }

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
    await notify(
        user_id=project.get("owner_id"),
        title="Có khoản đóng góp mới",
        message=f'{ledger_entry["user_name"]} vừa đóng góp {data.amount:,.0f}đ cho dự án "{project["name"]}".',
        n_type="donation",
    )

    return {"status": "success", "message": "Ghi nhận đóng góp Escrow thành công", "ledger": ledger_entry}
