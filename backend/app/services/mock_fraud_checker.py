import random

FRAUD_THRESHOLD = 50  

def mock_check_fraud(project_id: str, name: str, description: str) -> dict:
    if "TEST_HIGH_RISK" in name:
        score = 85
    elif "TEST_LOW_RISK" in name:
        score = 5
    else:
        score = random.randint(0, 30)

    return {
        "project_id": project_id,
        "fraud_score": score,
        "is_suspicious": score > FRAUD_THRESHOLD,
        "reasons": ["[MOCK] Dữ liệu giả lập, chưa qua AI thật"]
    }