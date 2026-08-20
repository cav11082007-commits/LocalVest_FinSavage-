"""
LocalVest Async AI-Flag Fraud Detection Worker
======================================================================
Chạy nền để quét:
 1. NLP anomaly scan trên mô tả dự án (né tránh bằng khoảng trắng, dấu câu, leetspeak, phủ định...).
 2. Reverse-image / duplicate check bằng Perceptual Hashing (pHash), có xử lý cả ảnh bị lật ngang (mirror).
 3. ONNX Deep Learning Image Classifier: Phân loại ảnh KYC & Ảnh dự án thành 3 nhãn (ai_generated, edited, real).
"""
from __future__ import annotations 

import asyncio
import logging
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime
import os
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
import imagehash
from app.store import store

# ==========================================
# LOGGING
# ==========================================
logger = logging.getLogger("localvest.ai_flag_worker")

# ==========================================
# ONNX IMAGE CLASSIFIER (AI / EDITED / REAL)
# ==========================================
class ONNXImageClassifier:
    """Mô hình Deep Learning ONNX phân loại ảnh (ai_generated, edited, real)"""
    def __init__(self, model_path: str | None = None) -> None:
        if model_path is None:
            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image_fraud_model.onnx")
        self._model_path = model_path
        self._session = None
        self._classes = ['ai_generated', 'edited', 'real']
        if os.path.exists(self._model_path):
            try:
                import onnxruntime as ort
                self._session = ort.InferenceSession(self._model_path)
                logger.info("AI-Flag ONNX: Loaded model '%s' successfully.", self._model_path)
            except Exception:
                logger.exception("AI-Flag ONNX: Error loading ONNX model.")

    def predict(self, image_path: str) -> tuple[str, float] | None:
        if not self._session or not image_path or not os.path.exists(image_path):
            return None
        try:
            with Image.open(image_path) as img:
                img = img.convert('RGB').resize((224, 224))
                arr = np.array(img, dtype=np.float32) / 255.0
                mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
                std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
                arr = (arr - mean) / std
                arr = np.transpose(arr, (2, 0, 1))[np.newaxis, :].astype(np.float32)

                input_name = self._session.get_inputs()[0].name
                outputs = self._session.run(None, {input_name: arr})[0][0]

                exp_out = np.exp(outputs - np.max(outputs))
                probs = exp_out / np.sum(exp_out)
                idx = int(np.argmax(probs))
                return self._classes[idx], float(probs[idx])
        except Exception:
            logger.exception("AI-Flag ONNX: Error predicting image '%s'.", image_path)
            return None

# ==========================================
# CẤU HÌNH NGƯỠNG & TRỌNG SỐ
# ==========================================
PHASH_DUPLICATE_THRESHOLD = 8  # Hamming distance <= 8 -> coi là trùng
BASE_FRAUD_SCORE = 0      # Điểm nền mặc định
MAX_FRAUD_SCORE = 100     
SUSPICIOUS_THRESHOLD = 50      # fraud_score >= 50 -> is_suspicious = True
IMAGE_DUPLICATE_PENALTY = 40   # Nếu hình ảnh trùng trên CSDL thì cộng 40 điểm

RISK_KEYWORDS: dict[str, int] = {
   r"lua\s*dao": 35,
   r"chuyen\s*khoan\s*ca\s*nhan": 25,
   r"xac\s*thuc\s*gia": 30,
   r"crypto": 20,
   r"gap\s*lam": 10,
}

NEGATION_WORDS = {"khong", "khong he", "chua tung", "tuyet doi khong"}
NEGATION_WINDOW = 3
NEGATION_DISCOUNT = 0.25

_LEET_MAP = str.maketrans({
   "0": "o", "1": "i", "3": "e", "4": "a",
   "5": "s", "7": "t", "@": "a", "$": "s",
})

_DJ_MAP = str.maketrans({"đ": "d", "Đ": "D"})

# ==========================================
# DATA CLASSES
# ==========================================
@dataclass
class TextScanResult:
   score: int = 0
   reasons: list[str] = field(default_factory=list)

@dataclass
class ImageScanResult:
   is_duplicate: bool = False
   matched_project_id: Optional[str] = None
   matched_via_mirror: bool = False
   computed_hash: Optional[str] = None

# ==========================================
# 1. TEXT RISK ANALYZER — QUÉT TỪ KHÓA RỦI RO (NLP)
# ==========================================
class TextRiskAnalyzer:
   def __init__(
       self,
       keyword_weights: dict[str, int] | None = None,
       negation_words: set[str] | None = None,
       negation_window: int = NEGATION_WINDOW,
       negation_discount: float = NEGATION_DISCOUNT,
   ) -> None:
       self._keyword_weights = keyword_weights or RISK_KEYWORDS
       self._negation_words = negation_words or NEGATION_WORDS
       self._negation_window = negation_window
       self._negation_discount = negation_discount
       self._compiled_patterns: dict[re.Pattern, int] = {
           re.compile(pattern): weight
           for pattern, weight in self._keyword_weights.items()
       }

   @staticmethod
   def normalize(text: str) -> str:
       if not isinstance(text, str):
           raise TypeError(f"normalize() yêu cầu str, nhận được {type(text).__name__}")
       normalized = text.translate(_DJ_MAP)
       normalized = unicodedata.normalize("NFD", normalized).encode("ascii", "ignore").decode("utf-8")
       normalized = normalized.lower()
       normalized = normalized.translate(_LEET_MAP)
       normalized = re.sub(r"[^\w\s]", "", normalized)
       normalized = re.sub(r"\s+", " ", normalized).strip()
       return normalized

   @staticmethod
   def compress(normalized_text: str) -> str:
       return normalized_text.replace(" ", "")

   def _has_negation_before(self, words: list[str], keyword_word_index: int) -> bool:
       start = max(0, keyword_word_index - self._negation_window)
       window_text = " ".join(words[start:keyword_word_index])
       return any(neg in window_text for neg in self._negation_words)

   def analyze(self, description: str) -> TextScanResult:
       result = TextScanResult()
       if not description:
           return result
       try:
           norm_desc = self.normalize(description)
           words = norm_desc.split(" ") if norm_desc else []
           compressed = self.compress(norm_desc)

           for pattern, weight in self._compiled_patterns.items():
               matched_normal = pattern.search(norm_desc)
               matched_compressed = pattern.search(compressed)

               if matched_normal:
                   applied_weight = self._score_normal_match(
                       pattern, weight, norm_desc, words, matched_normal, result
                   )
               elif matched_compressed:
                   result.score += weight
                   result.reasons.append(
                       f"Phát hiện từ khóa rủi ro bị né tránh bằng cách chèn khoảng trắng/ký tự lạ (Trọng số: +{weight})"
                   )
       except Exception:
           logger.exception("AI-Flag NLP: Lỗi không lường trước khi quét từ khóa rủi ro.")
           return TextScanResult()

       return result

   def _score_normal_match(
       self,
       pattern: re.Pattern,
       weight: int,
       norm_desc: str,
       words: list[str],
       matched: re.Match,
       result: TextScanResult,
   ) -> int:
       match_start_char = matched.start()
       word_idx = len(norm_desc[:match_start_char].split(" ")) - 1

       if self._has_negation_before(words, word_idx):
           applied_weight = round(weight * self._negation_discount)
           result.reasons.append(
               f"Phát hiện từ khóa rủi ro nghi vấn nghi đi sau từ phủ định (+{applied_weight})"
           )
       else:
           applied_weight = weight
           result.reasons.append(f"Phát hiện từ khóa rủi ro nghi vấn (+{applied_weight})")

       result.score += applied_weight
       return applied_weight

# ==========================================
# 2. IMAGE DUPLICATE DETECTOR (pHash)
# ==========================================
class ImageDuplicateDetector:
   def __init__(self, threshold: int = PHASH_DUPLICATE_THRESHOLD) -> None:
       self._threshold = threshold

   def compute_hash(self, image_path: str, mirrored: bool = False):
       try:
           with Image.open(image_path) as img:
               if mirrored:
                   img = ImageOps.mirror(img)
               return imagehash.phash(img)
       except Exception:
           return None

   @staticmethod
   def _to_hash_object(stored_hash):
       if stored_hash is None:
           return None
       if isinstance(stored_hash, str):
           try:
               return imagehash.hex_to_hash(stored_hash)
           except ValueError:
               return None
       return stored_hash

   def find_duplicate(
       self,
       new_hash,
       new_hash_mirrored,
       exclude_project_id: str | None = None,
   ) -> tuple[bool, Optional[str], bool]:
       if new_hash is None or not hasattr(store, "image_hashes"):
           return False, None, False
       try:
           for item in store.image_hashes:
               item_project_id = item.get("project_id")
               if exclude_project_id and item_project_id == exclude_project_id:
                   continue

               stored_hash = self._to_hash_object(item.get("hash"))
               if stored_hash is None:
                   continue

               if new_hash - stored_hash <= self._threshold:
                   return True, item_project_id, False
               if new_hash_mirrored and (new_hash_mirrored - stored_hash <= self._threshold):
                   return True, item_project_id, True
       except Exception:
           return False, None, False

       return False, None, False

   def save_hash(self, project_id: str, image_hash) -> None:
       if image_hash is None or not hasattr(store, "image_hashes"):
           return
       try:
           store.image_hashes.append({
               "project_id": project_id,
               "hash": str(image_hash),
           })
       except Exception:
           pass

   def scan(self, image_path: str, project_id: str) -> ImageScanResult:
       result = ImageScanResult()
       img_hash = self.compute_hash(image_path, mirrored=False)
       img_hash_mirrored = self.compute_hash(image_path, mirrored=True)

       if img_hash is not None:
           result.computed_hash = str(img_hash)

       is_duplicate, matched_project_id, via_mirror = self.find_duplicate(
           img_hash, img_hash_mirrored, exclude_project_id=project_id
       )
       result.is_duplicate = is_duplicate
       result.matched_project_id = matched_project_id
       result.matched_via_mirror = via_mirror

       self.save_hash(project_id, img_hash)
       return result

# ==========================================
# 3. FRAUD FLAG WORKER — ĐIỀU PHỐI TOÀN BỘ LUỒNG
# ==========================================
class FraudFlagWorker:
    def __init__(
        self,
        text_analyzer: TextRiskAnalyzer | None = None,
        image_detector: ImageDuplicateDetector | None = None,
        onnx_classifier: ONNXImageClassifier | None = None,
        base_score: int = BASE_FRAUD_SCORE,
        max_score: int = MAX_FRAUD_SCORE,
        suspicious_threshold: int = SUSPICIOUS_THRESHOLD,
        image_duplicate_penalty: int = IMAGE_DUPLICATE_PENALTY,
    ) -> None:
        self._text_analyzer = text_analyzer or TextRiskAnalyzer()
        self._image_detector = image_detector or ImageDuplicateDetector()
        self._onnx_classifier = onnx_classifier or ONNXImageClassifier()
        self._base_score = base_score
        self._max_score = max_score
        self._suspicious_threshold = suspicious_threshold
        self._image_duplicate_penalty = image_duplicate_penalty

    async def check_project(
        self,
        project_id: str,
        name: str,
        description: str,
        image_path: str | None = None,
        project_image_paths: list[str] | None = None,
        kyc_image_paths: list[str] | None = None,
    ) -> dict:
        await asyncio.sleep(1)
        fraud_score = self._base_score
        reasons: list[str] = []

        # --- 1. Quét NLP từ khóa rủi ro ---
        text_result = self._text_analyzer.analyze(description)
        fraud_score += text_result.score
        for r in text_result.reasons:
            reasons.append(f"[NLP Check] ⚠️ {r}")

        # --- 2. Quét Ảnh KYC bằng ONNX Model ---
        if kyc_image_paths:
            for kyc_p in kyc_image_paths:
                if kyc_p and os.path.exists(kyc_p):
                    pred = self._onnx_classifier.predict(kyc_p)
                    if pred:
                        label, conf = pred
                        conf_pct = int(conf * 100)
                        if label == 'ai_generated':
                            fraud_score += 50
                            reasons.append(f"[KYC Check] ❌ Ảnh CCCD có dấu hiệu được giả mạo bằng AI (Xác suất {conf_pct}%)")
                        elif label == 'edited':
                            fraud_score += 50
                            reasons.append(f"[KYC Check] ❌ Ảnh CCCD nghi vấn bị cắt ghép/chỉnh sửa Photoshop (Xác suất {conf_pct}%)")
                        elif label == 'real':
                            reasons.append(f"[KYC Check] ✅ Tài liệu KYC CCCD hợp lệ")

        # --- 3. Quét Ảnh Dự Án (ONNX Model + pHash Trùng Lặp) ---
        all_proj_imgs = []
        if image_path:
            all_proj_imgs.append(image_path)
        if project_image_paths:
            all_proj_imgs.extend(project_image_paths)

        all_proj_imgs = list(dict.fromkeys(all_proj_imgs))

        for img_p in all_proj_imgs:
            if img_p and os.path.exists(img_p):
                # a) pHash duplicate check
                image_result = self._image_detector.scan(img_p, project_id)
                if image_result.is_duplicate:
                    fraud_score += self._image_duplicate_penalty
                    mirror_note = " (lật ngang)" if image_result.matched_via_mirror else ""
                    reasons.append(
                        f"[Project Image Check] ⚠️ 1 ảnh minh chứng nghi vấn trùng trong cơ sở dữ liệu của dự án '{image_result.matched_project_id}'{mirror_note}"
                    )

                # b) ONNX classification check
                pred = self._onnx_classifier.predict(img_p)
                if pred:
                    label, conf = pred
                    conf_pct = int(conf * 100)
                    if label == 'ai_generated':
                        fraud_score += 40
                        reasons.append(f"[Project Image Check] ⚠️ 1 ảnh minh chứng dự án nghi vấn do AI khởi tạo giả lập (Xác suất {conf_pct}%)")
                    elif label == 'edited':
                        fraud_score += 20
                        reasons.append(f"[Project Image Check] ⚠️ 1 ảnh minh chứng nghi vấn có dấu hiệu bị can thiệp/chỉnh sửa cắt ghép (Xác suất {conf_pct}%)")

        # --- 4. Tổng hợp kết quả ---
        fraud_score = min(fraud_score, self._max_score)
        is_suspicious = (fraud_score >= self._suspicious_threshold)

        if not reasons:
            reasons = ["[AI Audit] Nội dung gốc minh bạch", "[AI Audit] Hình ảnh thực tế hợp lệ"]

        flag = {
            "id": f"flag_{uuid.uuid4().hex[:8]}",
            "project_id": project_id,
            "fraud_score": fraud_score,
            "is_suspicious": is_suspicious,
            "reasons": reasons,
            "checked_at": datetime.now().isoformat(),
        }

        self._persist_flag(flag)
        logger.info(
            "[AI-Flag Worker] Checked Project %s ('%s') | Score: %d%% | Suspicious: %s",
            project_id, name, fraud_score, is_suspicious,
        )
        return flag

    @staticmethod
    def _persist_flag(flag: dict) -> None:
        try:
            store.set_ai_flag(flag)
        except Exception:
            logger.exception("AI-Flag Worker: Lỗi khi ghi flag vào store.")

_default_worker = FraudFlagWorker()

async def async_ai_flag_checker(
    project_id: str,
    name: str,
    description: str,
    image_path: str | None = None,
    project_image_paths: list[str] | None = None,
    kyc_image_paths: list[str] | None = None,
) -> dict:
    return await _default_worker.check_project(
        project_id, name, description, image_path, project_image_paths, kyc_image_paths
    )

if __name__ == "__main__":
    # --- ĐÂY LÀ PHẦN CODE ĐỂ EM TEST (CHỈ CHẠY KHI GÕ LỆNH PYTHON TRỰC TIẾP TỪ FILE NÀY) ---
    print("\n" + "="*50)
    print("🚀 BẮT ĐẦU TEST LUỒNG GỌI TỪ AI_WORKER SANG AUDITOR")
    print("="*50)
    
    # 1. Import hàm evaluate_disbursement từ file disbursement_auditor nằm cùng thư mục
    from disbursement_auditor import evaluate_disbursement
    
    # 2. Giả lập gọi hàm xin giải ngân (truyền ID và 11 thông số dòng tiền)
    project_id = "TEST_INTEGRATION_001"
    fake_features = [0.1, 0.5, 0.8, 0.2, 0.9, 0.4, 0.3, 0.7, 0.6, 0.1, 0.5]
    
    print(f"⌛ Backend đang gọi AI kiểm tra giải ngân cho dự án: {project_id}...")
    json_result = evaluate_disbursement(project_id, fake_features)
    
    # 3. In ra CỤC JSON mà Frontend sẽ nhận được để vẽ giao diện Admin
    print("\n📦 ĐÂY LÀ CỤC JSON MÀ FRONTEND SẼ NHẬN ĐƯỢC ĐỂ VẼ LÊN MÀN HÌNH ADMIN:")
    import json
    parsed_json = json.loads(json_result)
    print(json.dumps(parsed_json, indent=4, ensure_ascii=False))
    print("="*50 + "\n")
