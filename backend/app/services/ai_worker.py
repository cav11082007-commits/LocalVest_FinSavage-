"""
LocalVest Async AI-Flag Fraud Detection Worker
======================================================================
Chạy nền để quét:
 1. NLP anomaly scan trên mô tả dự án (né tránh bằng khoảng trắng,
    dấu câu, leetspeak, phủ định...).
 2. Reverse-image / duplicate check bằng Perceptual Hashing (pHash),
    có xử lý cả ảnh bị lật ngang (mirror).
 
Thiết kế:
 - `TextRiskAnalyzer`  : chịu trách nhiệm chuẩn hóa + chấm điểm rủi ro văn bản.
 - `ImageDuplicateDetector`: chịu trách nhiệm tính pHash + so khớp trùng lặp.
 - `FraudFlagWorker`   : điều phối (orchestrator) toàn bộ luồng, tổng hợp
   điểm số cuối cùng và ghi kết quả vào store.
 
Toàn bộ các hàm/method đều có try-except riêng biệt ở đúng lớp nghiệp vụ
của nó, để một lỗi cục bộ (VD: ảnh hỏng, path sai) không bao giờ làm
crash worker chạy nền — tệ nhất chỉ làm giảm chất lượng của MỘT lần quét,
không làm mất toàn bộ hàng đợi (queue) đang xử lý phía sau.
"""
from __future__ import annotations 
 
import asyncio
import logging
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from PIL import Image, ImageOps, UnidentifiedImageError
import imagehash
from app.store import store
# ==========================================
# LOGGING
# ==========================================
# Dùng logger riêng theo tên module để khi trace log production, ta lọc
# được đúng luồng của AI-Flag Worker mà không lẫn với log của các service
# khác. Việc cấu hình handler/level cụ thể (file, format, level) nên do
# entrypoint của ứng dụng (main.py / uvicorn config) quyết định; ở đây
# module chỉ tạo logger và giả định nó đã được cấu hình từ bên ngoài.
logger = logging.getLogger("localvest.ai_flag_worker")
 
 
# ==========================================
# CẤU HÌNH NGƯỠNG & TRỌNG SỐ (CÓ THỂ TINH CHỈNH THÊM)
# ==========================================
PHASH_DUPLICATE_THRESHOLD = 8  # Hamming distance <= ngưỡng này -> coi là trùng
BASE_FRAUD_SCORE = 0      # Điểm nền mặc định cho mọi project
MAX_FRAUD_SCORE = 100
SUSPICIOUS_THRESHOLD = 50      # fraud_score > ngưỡng này -> is_suspicious = True
IMAGE_DUPLICATE_PENALTY = 40
 
# Trọng số từ khóa: Từ khóa nguy hiểm hơn sẽ cộng nhiều điểm hơn.
# Có thể bổ sung thêm từ log thực tế (false-negative bị lọt) tại đây.
RISK_KEYWORDS: dict[str, int] = {
   r"lua\s*dao": 35,
   r"chuyen\s*khoan\s*ca\s*nhan": 25,
   r"xac\s*thuc\s*gia": 30,
   r"crypto": 20,
   r"gap\s*lam": 10,
}
 
# Các từ phủ định đứng trước keyword trong bán kính NEGATION_WINDOW từ sẽ
# làm giảm trọng số cộng điểm (giảm false-positive khi user viết "cam kết
# không lừa đảo", "minh bạch không gấp lắm"...).
NEGATION_WORDS = {"khong", "khong he", "chua tung", "tuyet doi khong"}
NEGATION_WINDOW = 3        # số từ tối đa tính từ phủ định đến keyword
NEGATION_DISCOUNT = 0.25   # giữ lại 25% trọng số thay vì bỏ hẳn (vẫn đáng ngờ nhẹ)
 
# Bảng thay thế leetspeak phổ biến (VD: crypt0 -> crypto, l0a d4o -> loa dao)
_LEET_MAP = str.maketrans({
   "0": "o", "1": "i", "3": "e", "4": "a",
   "5": "s", "7": "t", "@": "a", "$": "s",
})
 
# QUAN TRỌNG: 'đ'/'Đ' (U+0111) là chữ cái ĐỘC LẬP trong Unicode, không có
# canonical decomposition như các nguyên âm có dấu thanh (ả, ừ...). Vì vậy
# unicodedata.normalize('NFD', ...) KHÔNG tách được 'đ' -> 'd' + dấu, và
# bước encode('ascii', 'ignore') phía sau sẽ XÓA MẤT chữ 'đ' thay vì giữ
# lại 'd'. Bug này khiến "lừa đảo" bị chuẩn hóa sai thành "lua ao" (mất
# chữ d) và regex "lua\s*dao" KHÔNG BAO GIỜ khớp, kể cả câu viết bình
# thường không hề né tránh gì. Phải map thủ công đ/Đ -> d/D TRƯỚC khi
# decompose NFD.
_DJ_MAP = str.maketrans({"đ": "d", "Đ": "D"})
 
 
# ==========================================
# KIỂU DỮ LIỆU KẾT QUẢ (DATA CLASSES)
# ==========================================
@dataclass
class TextScanResult:
   """Kết quả quét rủi ro trên văn bản mô tả dự án.
 
   Attributes:
       score: Tổng điểm rủi ro cộng dồn từ các từ khóa khớp được.
       reasons: Danh sách lý do (human-readable) để hiển thị cho
           reviewer/admin biết vì sao bị cộng điểm.
   """
   score: int = 0
   reasons: list[str] = field(default_factory=list)
 
 
@dataclass
class ImageScanResult:
   """Kết quả quét trùng lặp ảnh minh chứng bằng pHash.
 
   Attributes:
       is_duplicate: Có phát hiện trùng với ảnh của project khác không.
       matched_project_id: ID project bị trùng (nếu có).
       matched_via_mirror: True nếu chỉ khớp sau khi ảnh mới bị lật ngang
           để so sánh (dấu hiệu cố ý né duplicate-check).
       computed_hash: pHash (dạng hex string) của ảnh vừa quét, để log/lưu.
   """
   is_duplicate: bool = False
   matched_project_id: Optional[str] = None
   matched_via_mirror: bool = False
   computed_hash: Optional[str] = None
 
 
# ==========================================
# 1. TEXT RISK ANALYZER — QUÉT TỪ KHÓA RỦI RO (NLP)
# ==========================================
class TextRiskAnalyzer:
   """Chuẩn hóa và chấm điểm rủi ro cho văn bản mô tả dự án.
 
   Kỹ thuật chống né tránh (evasion) được xử lý:
     1. Dấu câu chèn giữa ký tự:      "l.ừ.a đ.ả.o"
     2. Khoảng trắng chèn giữa ký tự: "l ừ a đ ả o"
     3. Leetspeak cơ bản:             "l0a d4o", "crypt0"
     4. Giảm false-positive khi keyword đi sau từ phủ định:
        "cam kết không lừa đảo"
 
   Toàn bộ logic không phụ thuộc I/O (không đọc file, không gọi network)
   nên không cần try-except ở tầng regex/string — lỗi duy nhất có thể
   xảy ra là input không phải string, được chặn tường minh ngay đầu vào.
   """
 
   def __init__(
       self,
       keyword_weights: dict[str, int] | None = None,
       negation_words: set[str] | None = None,
       negation_window: int = NEGATION_WINDOW,
       negation_discount: float = NEGATION_DISCOUNT,
   ) -> None:
       """Khởi tạo analyzer với bộ từ khóa/cấu hình có thể tùy biến.
 
       Cho phép inject cấu hình khác nhau (VD: test unit, hoặc mỗi
       category dự án có bộ từ khóa riêng) thay vì hard-code toàn cục.
 
       Args:
           keyword_weights: Map regex-pattern -> trọng số điểm rủi ro.
           negation_words: Tập từ phủ định tiếng Việt đã chuẩn hóa.
           negation_window: Số từ tối đa tính từ phủ định đến keyword.
           negation_discount: Tỷ lệ trọng số còn giữ lại khi có phủ định
               (0.25 nghĩa là giữ lại 25%, không loại bỏ hoàn toàn vì vẫn
               đáng ngờ nhẹ).
       """
       self._keyword_weights = keyword_weights or RISK_KEYWORDS
       self._negation_words = negation_words or NEGATION_WORDS
       self._negation_window = negation_window
       self._negation_discount = negation_discount
       # Pre-compile regex 1 lần khi khởi tạo để tránh compile lại mỗi
       # request — quan trọng vì worker này chạy cho MỌI project được tạo.
       self._compiled_patterns: dict[re.Pattern, int] = {
           re.compile(pattern): weight
           for pattern, weight in self._keyword_weights.items()
       }
 
   @staticmethod
   def normalize(text: str) -> str:
       """Chuẩn hóa văn bản để chống lách luật.
 
       Pipeline: đ/Đ -> d/D  =>  bỏ dấu tiếng Việt (NFD)  =>  lowercase
       =>  giải leetspeak  =>  bỏ ký tự đặc biệt  =>  gộp khoảng trắng.
 
       Args:
           text: Văn bản gốc (có thể chứa dấu tiếng Việt, ký tự đặc biệt).
 
       Returns:
           Văn bản đã chuẩn hóa, chỉ gồm chữ thường a-z0-9 và khoảng trắng.
 
       Raises:
           TypeError: Nếu `text` không phải kiểu str (lỗi lập trình gọi
               sai, cố tình không nuốt để phát hiện sớm ở tầng gọi).
       """
       if not isinstance(text, str):
           raise TypeError(f"normalize() yêu cầu str, nhận được {type(text).__name__}")
 
       normalized = text.translate(_DJ_MAP)  # xử lý đ/Đ trước vì NFD không tách được
       normalized = unicodedata.normalize("NFD", normalized).encode("ascii", "ignore").decode("utf-8")
       normalized = normalized.lower()
       normalized = normalized.translate(_LEET_MAP)
       normalized = re.sub(r"[^\w\s]", "", normalized)
       normalized = re.sub(r"\s+", " ", normalized).strip()
       return normalized
 
   @staticmethod
   def compress(normalized_text: str) -> str:
       """Xóa toàn bộ khoảng trắng để bắt kiểu né tránh chèn khoảng trắng
       giữa từng ký tự (VD: 'l u a d a o' -> 'luadao').
 
       Args:
           normalized_text: Văn bản đã qua `normalize()`.
 
       Returns:
           Chuỗi không còn khoảng trắng.
       """
       return normalized_text.replace(" ", "")
 
   def _has_negation_before(self, words: list[str], keyword_word_index: int) -> bool:
       """Kiểm tra có từ phủ định trong cửa sổ N từ ngay trước keyword không.
 
       Args:
           words: Danh sách từ của văn bản đã chuẩn hóa.
           keyword_word_index: Vị trí (index) của từ chứa keyword khớp được.
 
       Returns:
           True nếu có ít nhất một từ phủ định trong cửa sổ trước đó.
       """
       start = max(0, keyword_word_index - self._negation_window)
       window_text = " ".join(words[start:keyword_word_index])
       return any(neg in window_text for neg in self._negation_words)
 
   def analyze(self, description: str) -> TextScanResult:
       """Quét toàn bộ từ khóa rủi ro trên mô tả dự án.
 
       Quét trên cả bản chuẩn hóa (giữ khoảng trắng, để check phủ định
       theo từ) và bản nén (không khoảng trắng, để bắt né tránh kiểu
       chèn khoảng trắng/ký tự lạ giữa từng chữ cái).
 
       Args:
           description: Mô tả dự án do người dùng nhập.
 
       Returns:
           TextScanResult chứa tổng điểm và danh sách lý do.
           Nếu description rỗng/None hoặc có lỗi không lường trước,
           trả về TextScanResult rỗng (score=0) thay vì raise, để
           KHÔNG làm crash worker — lỗi được log lại đầy đủ để điều tra.
       """
       result = TextScanResult()
 
       if not description:
           logger.debug("TextRiskAnalyzer: description rỗng, bỏ qua bước quét NLP.")
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
                   logger.info(
                       "AI-Flag NLP: từ khóa '%s' khớp trực tiếp (+%d điểm).",
                       pattern.pattern, applied_weight,
                   )
               elif matched_compressed:
                   result.score += weight
                   result.reasons.append(
                       f"Phát hiện từ khóa rủi ro bị né tránh bằng cách chèn "
                       f"khoảng trắng/ký tự lạ (Trọng số: +{weight})"
                   )
                   logger.warning(
                       "AI-Flag NLP: từ khóa '%s' chỉ khớp ở bản NÉN (nghi né "
                       "tránh bằng khoảng trắng/ký tự lạ), +%d điểm.",
                       pattern.pattern, weight,
                   )
 
       except Exception:
           # Bắt mọi lỗi không lường trước (regex lỗi lạ, encode lỗi...)
           # để một mô tả dự án "dị" không bao giờ làm chết worker nền.
           logger.exception(
               "AI-Flag NLP: lỗi không lường trước khi quét từ khóa rủi ro. "
               "Bỏ qua điểm NLP cho lần quét này."
           )
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
       """Tính điểm cho 1 match khớp trên bản chuẩn hóa (có khoảng trắng),
       có áp dụng giảm trọng số nếu phía trước là từ phủ định.
 
       Args:
           pattern: Regex pattern đã compile đang xét.
           weight: Trọng số gốc của keyword.
           norm_desc: Văn bản đã chuẩn hóa (dùng để định vị từ).
           words: Danh sách từ của `norm_desc`.
           matched: Đối tượng re.Match đã tìm được.
           result: TextScanResult đang được tích lũy — hàm này append
               trực tiếp vào `result.reasons` và cộng vào `result.score`.
 
       Returns:
           Trọng số thực tế đã được cộng vào điểm (để phục vụ logging).
       """
       match_start_char = matched.start()
       word_idx = len(norm_desc[:match_start_char].split(" ")) - 1
 
       if self._has_negation_before(words, word_idx):
           applied_weight = round(weight * self._negation_discount)
           result.reasons.append(
               f"Phát hiện từ khóa rủi ro nhưng đi sau phủ định, giảm trọng số (+{applied_weight})"
           )
       else:
           applied_weight = weight
           result.reasons.append(f"Phát hiện từ khóa rủi ro bị ẩn giấu (Trọng số: +{applied_weight})")
 
       result.score += applied_weight
       return applied_weight
 
 
# ==========================================
# 2. IMAGE DUPLICATE DETECTOR — QUÉT TRÙNG LẶP ẢNH (pHash)
# ==========================================
class ImageDuplicateDetector:
   """Tính pHash và so khớp trùng lặp ảnh minh chứng dự án.
 
   Bắt cả 2 chiều so sánh:
     - Ảnh mới  <->  ảnh đã lưu (bình thường)
     - Ảnh mới đã LẬT NGANG (mirror)  <->  ảnh đã lưu
       (vì pHash gốc không bất biến với phép lật — đây là cách né
       duplicate-check phổ biến: kẻ gian lật ngang ảnh cũ rồi đăng lại).
 
   Mọi thao tác đọc file ảnh đều được bọc try-except riêng để 1 file ảnh
   hỏng/không đọc được không làm crash toàn bộ worker.
   """
 
   def __init__(self, threshold: int = PHASH_DUPLICATE_THRESHOLD) -> None:
       """Khởi tạo detector.
 
       Args:
           threshold: Ngưỡng Hamming distance để coi là trùng lặp. Giá
               trị càng nhỏ càng "khắt khe" (ít false-positive nhưng dễ
               bỏ lọt ảnh chỉnh sửa nhẹ); giá trị càng lớn càng "nhạy"
               nhưng dễ báo nhầm ảnh khác nhau là trùng.
       """
       self._threshold = threshold
 
   def compute_hash(self, image_path: str, mirrored: bool = False):
       """Tính pHash của một ảnh, tùy chọn lật ngang trước khi tính.
 
       Args:
           image_path: Đường dẫn tới file ảnh trên đĩa.
           mirrored: Nếu True, lật ngang ảnh trước khi tính hash — dùng
               để so khớp trường hợp ảnh gian lận bị lật để né trùng lặp.
 
       Returns:
           Đối tượng `imagehash.ImageHash`, hoặc None nếu đọc/tính lỗi
           (file không tồn tại, không phải ảnh hợp lệ, ảnh hỏng...).
           Trả None thay vì raise để tầng gọi có thể tiếp tục xử lý các
           bước còn lại (VD: vẫn chấm điểm NLP) thay vì mất toàn bộ flag.
       """
       try:
           with Image.open(image_path) as img:
               if mirrored:
                   img = ImageOps.mirror(img)
               return imagehash.phash(img)
       except FileNotFoundError:
           logger.error("AI-Flag pHash: không tìm thấy file ảnh '%s'.", image_path)
       except UnidentifiedImageError:
           logger.error("AI-Flag pHash: file '%s' không phải ảnh hợp lệ hoặc bị hỏng.", image_path)
       except Exception:
           logger.exception("AI-Flag pHash: lỗi không lường trước khi đọc ảnh '%s'.", image_path)
       return None
 
   @staticmethod
   def _to_hash_object(stored_hash):
       """Chuyển stored_hash về đúng kiểu `imagehash.ImageHash` để so sánh
       được, dù store lưu dưới dạng string (khi ghi xuống DB thật) hay
       object (khi còn trong RAM).
 
       Args:
           stored_hash: Giá trị hash lấy từ store — có thể là str (hex)
               hoặc đã là `imagehash.ImageHash`.
 
       Returns:
           `imagehash.ImageHash` hợp lệ, hoặc None nếu không parse được
           (dữ liệu store bị hỏng/format lạ — không nên làm crash cả
           worker chỉ vì 1 bản ghi cũ bị lỗi).
       """
       if stored_hash is None:
           return None
       if isinstance(stored_hash, str):
           try:
               return imagehash.hex_to_hash(stored_hash)
           except ValueError:
               logger.warning("AI-Flag pHash: không parse được stored_hash='%s' từ store.", stored_hash)
               return None
       return stored_hash  # đã là ImageHash object rồi
 
   def find_duplicate(
       self,
       new_hash,
       new_hash_mirrored,
       exclude_project_id: str | None = None,
   ) -> tuple[bool, Optional[str], bool]:
       """So sánh Hamming distance với danh sách ảnh đã lưu trong hệ thống.
 
       Args:
           new_hash: pHash của ảnh mới (chiều thuận).
           new_hash_mirrored: pHash của ảnh mới sau khi lật ngang.
           exclude_project_id: ID project hiện tại — không so sánh ảnh
               với chính project đang xét (VD khi user edit lại project
               của mình thì không tự báo trùng với chính mình).
 
       Returns:
           Tuple (is_duplicate, matched_project_id, matched_via_mirror).
       """
       # Dùng "is None" thay vì "not new_hash": imagehash.ImageHash định
       # nghĩa __len__ = số bit '1' trong hash (không định nghĩa __bool__),
       # nên 1 hash hợp lệ nhưng toàn bit 0 sẽ bị Python coi là falsy và
       # bỏ qua nhầm nếu dùng "not".
       if new_hash is None:
           return False, None, False
 
       if not hasattr(store, "image_hashes"):
           logger.debug("AI-Flag pHash: store chưa có thuộc tính 'image_hashes', bỏ qua so khớp.")
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
           logger.exception("AI-Flag pHash: lỗi không lường trước khi so khớp trùng lặp ảnh.")
           return False, None, False
 
       return False, None, False
 
   def save_hash(self, project_id: str, image_hash) -> None:
       """Lưu pHash của ảnh vừa quét vào store để các project sau so khớp.
 
       QUAN TRỌNG: thiếu bước này thì `find_duplicate()` sẽ luôn trả về
       False vì không có dữ liệu nào để so sánh.
 
       Args:
           project_id: ID project sở hữu ảnh.
           image_hash: Đối tượng `imagehash.ImageHash` vừa tính được.
       """
       if image_hash is None or not hasattr(store, "image_hashes"):
           return
       try:
           store.image_hashes.append({
               "project_id": project_id,
               "hash": str(image_hash),  # lưu dạng string để tương thích khi ghi xuống DB thật
           })
       except Exception:
           logger.exception(
               "AI-Flag pHash: lỗi khi lưu hash ảnh của project '%s' vào store.", project_id
           )
 
   def scan(self, image_path: str, project_id: str) -> ImageScanResult:
       """Quét đầy đủ 1 ảnh: tính hash (thuận + lật), tìm trùng lặp, rồi
       lưu hash lại vào store cho các lần quét sau.
 
       Args:
           image_path: Đường dẫn ảnh minh chứng cần quét.
           project_id: ID project đang được quét (để loại trừ tự-so-sánh
               và để gắn nhãn khi lưu hash).
 
       Returns:
           ImageScanResult mô tả kết quả trùng lặp (nếu có).
       """
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
 
       if is_duplicate:
           logger.warning(
               "AI-Flag pHash: project '%s' có ảnh TRÙNG LẶP với project '%s' "
               "(mirror=%s, hash=%s).",
               project_id, matched_project_id, via_mirror, result.computed_hash,
           )
 
       self.save_hash(project_id, img_hash)
       return result
 
 
# ==========================================
# 3. FRAUD FLAG WORKER — ĐIỀU PHỐI TOÀN BỘ LUỒNG
# ==========================================
class FraudFlagWorker:
   """Điều phối luồng chấm điểm gian lận (fraud scoring) cho một project:
   kết hợp kết quả từ `TextRiskAnalyzer` và `ImageDuplicateDetector`,
   tổng hợp thành 1 flag hoàn chỉnh và ghi vào `store.ai_flags`.
 
   Tách orchestrator riêng khỏi 2 analyzer ở trên giúp:
     - Dễ unit-test độc lập từng phần (text-only, image-only).
     - Dễ thay đổi công thức tổng hợp điểm (VD: đổi trọng số ảnh/text)
       mà không đụng vào logic quét bên trong từng analyzer.
   """
 
   def __init__(
       self,
       text_analyzer: TextRiskAnalyzer | None = None,
       image_detector: ImageDuplicateDetector | None = None,
       base_score: int = BASE_FRAUD_SCORE,
       max_score: int = MAX_FRAUD_SCORE,
       suspicious_threshold: int = SUSPICIOUS_THRESHOLD,
       image_duplicate_penalty: int = IMAGE_DUPLICATE_PENALTY,
   ) -> None:
       """Khởi tạo worker, cho phép inject các thành phần con để dễ test
       (VD: mock ImageDuplicateDetector trong unit test không cần đọc
       file ảnh thật).
 
       Args:
           text_analyzer: Analyzer chấm điểm văn bản (mặc định tạo mới).
           image_detector: Detector so khớp ảnh (mặc định tạo mới).
           base_score: Điểm nền cộng cho mọi project.
           max_score: Trần điểm fraud_score tối đa.
           suspicious_threshold: Ngưỡng điểm để đánh dấu is_suspicious.
           image_duplicate_penalty: Điểm cộng thêm khi phát hiện ảnh trùng.
       """
       self._text_analyzer = text_analyzer or TextRiskAnalyzer()
       self._image_detector = image_detector or ImageDuplicateDetector()
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
   ) -> dict:
       """Chạy toàn bộ pipeline chấm điểm gian lận cho 1 project và ghi
       kết quả vào `store.ai_flags`.
 
       Đây là entrypoint tương đương hàm `async_ai_flag_checker` cũ, giữ
       nguyên chữ ký/hành vi (side-effect ghi vào store) để không phải
       sửa code gọi nó ở nơi khác.
 
       Args:
           project_id: ID project cần quét.
           name: Tên project (hiện dùng để log; có thể mở rộng đưa vào
               phần quét text sau này nếu cần).
           description: Mô tả project cần quét NLP.
           image_path: Đường dẫn ảnh minh chứng (tùy chọn).
 
       Returns:
           Dict flag đã được append vào `store.ai_flags`, gồm các khóa:
           id, project_id, fraud_score, is_suspicious, reasons, checked_at.
       """
       # Giả lập độ trễ xử lý nền (non-blocking) như bản gốc — trong thực
       # tế đây là chỗ để mô phỏng/đợi các tác vụ I/O bound khác nếu cần.
       await asyncio.sleep(1)
 
       fraud_score = self._base_score
       reasons: list[str] = []
 
       # --- 1. Quét NLP từ khóa rủi ro ---
       text_result = self._text_analyzer.analyze(description)
       fraud_score += text_result.score
       reasons.extend(text_result.reasons)
 
       # --- 2. Quét trùng lặp ảnh (nếu có ảnh minh chứng) ---
       if image_path:
           image_result = self._image_detector.scan(image_path, project_id)
           if image_result.is_duplicate:
               fraud_score += self._image_duplicate_penalty
               mirror_note = (
                   " (ảnh đã bị LẬT NGANG để né trùng lặp)"
                   if image_result.matched_via_mirror else ""
               )
               reasons.append(
                   f"Cảnh báo: Ảnh minh chứng trùng lặp với project "
                   f"'{image_result.matched_project_id}'{mirror_note} "
                   f"(Khả năng giả mạo cao)"
               )
 
       # --- 3. Tổng hợp kết quả ---
       fraud_score = min(fraud_score, self._max_score)
       is_suspicious = fraud_score > self._suspicious_threshold
 
       if not reasons:
           reasons = ["Nội dung gốc minh bạch", "Hình ảnh thực tế hợp lệ"]
 
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
       """Ghi flag vào `store.ai_flags`, cô lập lỗi ghi store khỏi phần
       tính toán phía trên (nếu store lỗi, ta vẫn đã log được kết quả
       tính toán để không mất dấu vết điều tra).
 
       Args:
           flag: Dict kết quả đã tổng hợp, sẵn sàng để lưu.
       """
       try:
           store.set_ai_flag(flag)
       except Exception:
           logger.exception(
               "AI-Flag Worker: lỗi khi ghi flag '%s' (project '%s') vào store.",
               flag.get("id"), flag.get("project_id"),
           )
 
 
# ==========================================
# ENTRYPOINT TƯƠNG THÍCH NGƯỢC (BACKWARD-COMPATIBLE)
# ==========================================
# Giữ nguyên 1 module-level singleton + hàm async cùng tên/chữ ký với bản
# gốc, để các nơi khác trong codebase (route xử lý tạo project, queue
# consumer...) đang gọi `async_ai_flag_checker(...)` không cần sửa gì cả.
_default_worker = FraudFlagWorker()
 
 
async def async_ai_flag_checker(
   project_id: str,
   name: str,
   description: str,
   image_path: str | None = None,
) -> dict:
   """Wrapper tương thích ngược cho `FraudFlagWorker.check_project`.
 
   Xem chi tiết tham số/kết quả tại `FraudFlagWorker.check_project`.
   """
   return await _default_worker.check_project(project_id, name, description, image_path)
