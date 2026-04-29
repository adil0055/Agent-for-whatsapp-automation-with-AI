"""
Media service — download media files from Twilio and upload to MinIO (S3).
"""
import httpx
from minio import Minio
from io import BytesIO
from datetime import datetime
from app.config import get_settings
from app.utils.logger import get_logger

log = get_logger("media")
settings = get_settings()

_minio_client: Minio = None


def _get_minio() -> Minio:
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        log.info("minio_connected", endpoint=settings.minio_endpoint)
    return _minio_client


async def download_twilio_media(media_url: str) -> tuple[bytes, str]:
    """
    Download a media file from Twilio's servers.
    Returns (file_bytes, content_type).
    Twilio media URLs require basic auth with account SID + auth token.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            media_url,
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            follow_redirects=True,
        )
        response.raise_for_status()

    content_type = response.headers.get("content-type", "application/octet-stream")
    log.info("media_downloaded", url=media_url, size=len(response.content), content_type=content_type)
    return response.content, content_type


def upload_to_storage(
    file_bytes: bytes,
    filename: str,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Upload a file to MinIO and return the stored URL.
    Files are organized by date: YYYY/MM/DD/filename
    """
    minio = _get_minio()
    bucket = settings.minio_bucket

    # Ensure bucket exists
    if not minio.bucket_exists(bucket):
        minio.make_bucket(bucket)
        log.info("bucket_created", bucket=bucket)

    # Build object path with date prefix
    now = datetime.utcnow()
    object_name = f"{now:%Y/%m/%d}/{filename}"

    minio.put_object(
        bucket,
        object_name,
        BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )

    # Build the access URL using the public webhook URL so Twilio can fetch it
    base_url = settings.webhook_base_url.rstrip('/')
    url = f"{base_url}/api/media/{object_name}"
    log.info("media_uploaded", object_name=object_name, size=len(file_bytes), url=url)
    return url


def get_extension_for_content_type(content_type: str) -> str:
    """Map MIME types to file extensions."""
    mapping = {
        "audio/ogg": ".ogg",
        "audio/opus": ".ogg",
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
        "video/mp4": ".mp4",
    }
    return mapping.get(content_type, ".bin")
