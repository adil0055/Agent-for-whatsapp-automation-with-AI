"""
Media API — serves media files from MinIO storage.
Allows external services (Twilio) to access stored images/PDFs via public URL.
"""
from io import BytesIO
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.services.media import _get_minio
from app.config import get_settings
from app.utils.logger import get_logger

log = get_logger("api_media")
settings = get_settings()
router = APIRouter(prefix="/api")


@router.get("/media/{path:path}")
async def serve_media(path: str):
    """
    Proxy media files from MinIO storage.
    Twilio requires publicly accessible URLs for media messages —
    this endpoint makes MinIO files accessible through the app's public URL.
    """
    minio = _get_minio()
    bucket = settings.minio_bucket

    try:
        response = minio.get_object(bucket, path)
        data = response.read()
        response.close()
        response.release_conn()

        # Determine content type from extension
        ct_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
            ".mp3": "audio/mpeg",
            ".ogg": "audio/ogg",
            ".mp4": "video/mp4",
        }
        ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""
        content_type = ct_map.get(ext, "application/octet-stream")

        log.info("media_served", path=path, size=len(data))
        return StreamingResponse(
            BytesIO(data),
            media_type=content_type,
            headers={"Content-Disposition": f"inline; filename={path.split('/')[-1]}"},
        )
    except Exception as e:
        log.error("media_not_found", path=path, error=str(e))
        raise HTTPException(status_code=404, detail="Media not found")
