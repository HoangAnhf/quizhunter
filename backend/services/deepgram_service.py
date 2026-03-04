from deepgram import DeepgramClient

from config import (
    DEEPGRAM_API_KEY,
    DEEPGRAM_MODEL,
    DEEPGRAM_LANGUAGE,
    DEEPGRAM_SMART_FORMAT,
    DEEPGRAM_PUNCTUATE,
)


class DeepgramService:
    """Wrapper cho Deepgram Speech-to-Text API (SDK v6)."""

    def __init__(self):
        self._client = DeepgramClient(api_key=DEEPGRAM_API_KEY)

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Chuyển audio thành text.

        Args:
            audio_bytes: Raw audio bytes (wav, mp3, webm, etc.)

        Returns:
            Transcript text hoặc chuỗi rỗng nếu lỗi.
        """
        result = self.transcribe_with_details(audio_bytes)
        return result.get("transcript", "")

    def transcribe_with_details(self, audio_bytes: bytes) -> dict:
        """Chuyển audio thành text với thông tin chi tiết.

        Returns:
            dict với keys: transcript, confidence, language, duration
        """
        try:
            response = self._client.listen.v1.media.transcribe_file(
                request=audio_bytes,
                model=DEEPGRAM_MODEL,
                smart_format=DEEPGRAM_SMART_FORMAT,
                punctuate=DEEPGRAM_PUNCTUATE,
                detect_language=True,
            )

            channel = response.results.channels[0]
            alternative = channel.alternatives[0]

            return {
                "transcript": alternative.transcript,
                "confidence": alternative.confidence,
                "language": getattr(channel, "detected_language", DEEPGRAM_LANGUAGE) or DEEPGRAM_LANGUAGE,
                "duration": getattr(response.metadata, "duration", 0) or 0,
            }

        except Exception as e:
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": "",
                "duration": 0,
                "error": str(e),
            }

    def is_available(self) -> bool:
        """Kiểm tra API key có hợp lệ không."""
        return bool(DEEPGRAM_API_KEY and len(DEEPGRAM_API_KEY) > 10)
