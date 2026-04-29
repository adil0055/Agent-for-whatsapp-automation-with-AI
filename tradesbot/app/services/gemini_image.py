"""
Local Image Generation Service.
Delegates requests to the local SDXL Turbo API worker running in Docker.
"""
import httpx
from app.utils.logger import get_logger

log = get_logger("local_image")

async def generate_image(prompt: str) -> bytes | None:
    """
    Generate an image using the local SDXL Turbo worker.
    """
    url = "http://image-worker:8001/generate"
    payload = {"prompt": prompt}
    
    try:
        # Remove timeout because local generation can take a few seconds and the first-time model download takes several minutes
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                log.info("local_image_generated", size_kb=len(resp.content) // 1024)
                return resp.content
            else:
                log.error("local_image_error", status=resp.status_code, body=resp.text)
                return None
    except httpx.TimeoutException:
        log.error("local_image_timeout")
        return None
    except Exception as e:
        log.error("local_image_connection_failed", error=str(e))
        return None

async def generate_marketing_image(
    trade_type: str,
    business_name: str,
    description: str,
    contact: str = "",
) -> bytes | None:
    """
    Generate a professional marketing image for a tradesperson.
    """
    # SDXL Turbo responds better to highly descriptive, concise prompts
    prompt = (
        f"Professional advertisement poster for an Indian {trade_type}. "
        f"Business name '{business_name}'. Promoting: {description}. "
        f"High quality, 4k, professional photography, studio lighting, highly detailed. "
        f"No watermark."
    )
    return await generate_image(prompt)
