"""
ASR (Automatic Speech Recognition) service using Groq's Whisper API.
Transcribes voice messages to text with language detection.
"""
import tempfile
from pathlib import Path
from groq import Groq
from app.config import get_settings
from app.models.schemas import ASRResult
from app.utils.audio import convert_ogg_to_wav
from app.utils.logger import get_logger

log = get_logger("asr")
settings = get_settings()

_groq_client: Groq = None


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.groq_api_key)
        log.info("groq_asr_initialized")
    return _groq_client


async def transcribe_audio(audio_bytes: bytes, content_type: str = "audio/ogg") -> ASRResult:
    """
    Transcribe audio bytes using Groq's Whisper API.
    
    1. Convert OGG→WAV if needed (Groq accepts multiple formats but WAV is safest)
    2. Send to Groq whisper-large-v3-turbo
    3. Return transcript + detected language
    """
    groq = _get_groq()

    # Convert to WAV if OGG/Opus (WhatsApp voice note format)
    if "ogg" in content_type or "opus" in content_type:
        log.info("converting_audio", from_type=content_type)
        audio_bytes = convert_ogg_to_wav(audio_bytes)
        file_ext = ".wav"
    else:
        ext_map = {"audio/mpeg": ".mp3", "audio/mp4": ".m4a", "audio/wav": ".wav"}
        file_ext = ext_map.get(content_type, ".wav")

    # Write to temp file (Groq SDK needs a file-like object)
    with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcription = groq.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=audio_file,
                response_format="verbose_json",
            )

        transcript = transcription.text.strip()
        language = getattr(transcription, "language", None)
        duration = getattr(transcription, "duration", None)

        log.info(
            "transcription_complete",
            language=language,
            duration=duration,
            transcript_length=len(transcript),
            transcript_preview=transcript[:100],
        )

        return ASRResult(
            transcript=transcript,
            language=language,
            duration_seconds=duration,
        )

    finally:
        Path(tmp_path).unlink(missing_ok=True)
