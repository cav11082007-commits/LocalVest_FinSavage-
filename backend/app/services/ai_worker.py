"""
LocalVest Async AI-Flag Fraud Detection Worker
Runs background non-blocking pHash / NLP text anomaly scan.
"""
import asyncio
import uuid
import re
import unicodedata
from datetime import datetime
from PIL import Image
import imagehash
from app.store import store

# ==========================================
# CẤU HÌNH NGƯỠNG & TRỌNG SỐ (CÓ THỂ TINH CHỈNH THÊM)
# ==========================================
PHASH_DUPLICATE_THRESHOLD = 8

# Trọng số từ khóa: Từ khóa nguy hiểm hơn sẽ cộng nhiều điểm hơn
RISK_KEYWORDS = {
    r"lua\s*dao": 35,
    r"chuyen\s*khoan\s*ca\s*nhan": 25,
    r"xac\s*thuc\s*gia": 30,
    r"crypto": 20,
    r"gap\s*lam": 10,
    # Bạn có thể bổ sung thêm từ log thực tế ở đây
}


# ==========================================
# HÀM HỖ TRỢ (UTILITIES)
# ==========================================
def normalize_text(text: str) -> str:
    """Loại bỏ dấu tiếng Việt và các ký tự đặc biệt để chống lách luật (VD: l.ừ.a đ.ả.o -> lua dao)"""
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s]', '', text)
    return text.lower()


def compute_phash(image_path: str):
    """Tính toán mã băm pHash của hình ảnh"""
    try:
        return imagehash.phash(Image.open(image_path))
    except Exception as e:
        print(f"[AI-Flag Worker] Lỗi đọc ảnh {image_path}: {e}")
        return None


def _to_hash_object(stored_hash):
    """
    Chuyển stored_hash về đúng kiểu imagehash.ImageHash để so sánh được,
    dù store lưu dưới dạng string (khi ghi xuống DB thật) hay object (khi còn trong RAM).
    """
    if stored_hash is None:
        return None
    if isinstance(stored_hash, str):
        try:
            return imagehash.hex_to_hash(stored_hash)
        except ValueError:
            return None
    return stored_hash  # đã là ImageHash object rồi


def check_image_duplicate(new_hash, exclude_project_id: str = None) -> tuple[bool, str | None]:
    """
    So sánh Hamming distance với danh sách ảnh trong hệ thống.
    Trả về (is_duplicate, matched_project_id) để log rõ trùng với project nào.
    """
    if not new_hash:
        return False, None

    if hasattr(store, 'image_hashes'):
        for item in store.image_hashes:
            item_project_id = item.get('project_id')
            # không so sánh ảnh với chính project đang xét (VD khi user edit lại project của mình)
            if exclude_project_id and item_project_id == exclude_project_id:
                continue

            stored_hash = _to_hash_object(item.get('hash'))
            if stored_hash and (new_hash - stored_hash <= PHASH_DUPLICATE_THRESHOLD):
                return True, item_project_id

    return False, None


# ==========================================
# LUỒNG XỬ LÝ CHÍNH
# ==========================================
async def async_ai_flag_checker(project_id: str, name: str, description: str, image_path: str = None):
    """Thực hiện xử lý NLP & Reverse-image fraud check"""
    await asyncio.sleep(1)  # Non-blocking async sleep
    fraud_score = 5
    reasons = []

    # 1. Quét NLP Từ Khóa Rủi Ro
    norm_desc = normalize_text(description)
    for pattern, weight in RISK_KEYWORDS.items():
        if re.search(pattern, norm_desc):
            fraud_score += weight
            reasons.append(f"Phát hiện từ khóa rủi ro bị ẩn giấu (Trọng số: +{weight})")

    # 2. Quét Trùng Lặp Ảnh bằng pHash
    if image_path:
        img_hash = compute_phash(image_path)
        is_duplicate, matched_project_id = check_image_duplicate(img_hash, exclude_project_id=project_id)

        if is_duplicate:
            fraud_score += 40
            reasons.append(
                f"Cảnh báo: Ảnh minh chứng trùng lặp với project '{matched_project_id}' "
                f"(Khả năng giả mạo cao)"
            )

        # QUAN TRỌNG: lưu hash lại vào store để các project sau so khớp được.
        # Thiếu bước này thì check_image_duplicate() sẽ luôn trả về False
        # vì không có dữ liệu nào để so sánh.
        if img_hash and hasattr(store, 'image_hashes'):
            store.image_hashes.append({
                "project_id": project_id,
                "hash": str(img_hash),  # lưu dạng string để tương thích khi ghi xuống DB thật
            })

    # 3. Tổng hợp kết quả (Giới hạn Fraud Score tối đa 100)
    fraud_score = min(fraud_score, 100)
    is_suspicious = fraud_score > 50

    if not reasons:
        reasons = ["Nội dung gốc minh bạch", "Hình ảnh thực tế hợp lệ"]

    flag = {
        "id": f"flag_{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "fraud_score": fraud_score,
        "is_suspicious": is_suspicious,
        "reasons": reasons,
        "checked_at": datetime.now().isoformat()
    }
    store.ai_flags.append(flag)
    print(f"[AI-Flag Worker] Checked Project {project_id} | Score: {fraud_score}%")
