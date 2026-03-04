from typing import List

from deep_translator import GoogleTranslator


# Ký tự phân cách Unicode hiếm dùng, Google Translate sẽ giữ nguyên
_SEPARATOR = "\n⸻⸻⸻\n"


class TranslatorService:
    """Dịch text sang tiếng Việt bằng Google Translate (miễn phí).

    Tối ưu: gộp nhiều text thành 1 request duy nhất để giảm thời gian.
    """

    def __init__(self, target: str = "vi"):
        self._translator = GoogleTranslator(source="en", target=target)

    def translate(self, text: str) -> str:
        """Dịch 1 đoạn text."""
        if not text or not text.strip():
            return text
        try:
            return self._translator.translate(text)
        except Exception:
            return text

    def translate_batch(self, texts: List[str]) -> List[str]:
        """Dịch nhiều text - gộp thành chunks lớn để giảm API calls."""
        if not texts:
            return []

        try:
            # Google Translate giới hạn ~5000 ký tự/request
            # Gộp texts thành chunks dưới 4500 chars
            max_chunk_chars = 4500
            chunks = []
            current_chunk: List[str] = []
            current_len = 0

            for t in texts:
                added_len = len(t) + len(_SEPARATOR)
                if current_len + added_len > max_chunk_chars and current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = [t]
                    current_len = len(t)
                else:
                    current_chunk.append(t)
                    current_len += added_len

            if current_chunk:
                chunks.append(current_chunk)

            # Dịch từng chunk (1 API call mỗi chunk)
            results = []
            for chunk in chunks:
                joined = _SEPARATOR.join(chunk)
                translated = self._translator.translate(joined)
                if translated:
                    parts = translated.split("⸻⸻⸻")
                    # Clean up whitespace
                    parts = [p.strip() for p in parts]
                    # Nếu split ra đúng số lượng
                    if len(parts) == len(chunk):
                        results.extend(parts)
                    else:
                        # Fallback: gán lại best-effort
                        results.extend(parts[:len(chunk)])
                        # Pad nếu thiếu
                        while len(results) < len(results) + (len(chunk) - len(parts)):
                            break
                        if len(parts) < len(chunk):
                            results.extend(chunk[len(parts):])
                else:
                    results.extend(chunk)

            # Đảm bảo trả về đúng số lượng
            if len(results) < len(texts):
                results.extend(texts[len(results):])

            return results[:len(texts)]

        except Exception:
            return texts
