from datetime import datetime
from fastapi import HTTPException

ALLOWED_TRANSITIONS = {
    "pending_review": ["active", "rejected"],
    "flagged":         ["active", "rejected"],
    "active":          ["funded", "cancelled"],
    "funded":          ["completed"],
    "rejected":        [],
    "cancelled":       [],
    "completed":       [],
}

def transition(campaign: dict, new_state: str, actor: str, reason: str = None) -> dict:
    current_state = campaign.get("status")
    allowed_next = ALLOWED_TRANSITIONS.get(current_state, [])
    if new_state not in allowed_next:
        raise HTTPException(
            status_code=400,
            detail=f"Không thể chuyển trạng thái từ '{current_state}' sang '{new_state}'"
        )
    old_state = campaign["status"]
    campaign["status"] = new_state
    campaign.setdefault("status_history", []).append({
        "from": old_state, "to": new_state, "actor": actor,
        "reason": reason, "at": datetime.now().isoformat()
    })
    return campaign