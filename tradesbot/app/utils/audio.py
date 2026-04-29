"""
Audio conversion utilities using ffmpeg (via pydub).
"""
import tempfile
import subprocess
from pathlib import Path
from app.utils.logger import get_logger

log = get_logger("audio")


def convert_ogg_to_wav(ogg_bytes: bytes) -> bytes:
    """
    Convert OGG/Opus audio (WhatsApp voice note format) to WAV (16kHz mono).
    Uses ffmpeg directly for reliability.
    """
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_file:
        ogg_file.write(ogg_bytes)
        ogg_path = ogg_file.name

    wav_path = ogg_path.replace(".ogg", ".wav")

    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", ogg_path,
                "-ar", "16000",      # 16kHz sample rate
                "-ac", "1",          # mono
                "-f", "wav",
                wav_path,
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            log.error("ffmpeg_failed", stderr=result.stderr.decode())
            raise RuntimeError(f"ffmpeg conversion failed: {result.stderr.decode()}")

        with open(wav_path, "rb") as f:
            wav_bytes = f.read()

        log.info("audio_converted", input_size=len(ogg_bytes), output_size=len(wav_bytes))
        return wav_bytes

    finally:
        # Clean up temp files
        Path(ogg_path).unlink(missing_ok=True)
        Path(wav_path).unlink(missing_ok=True)
