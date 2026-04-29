import asyncio
from app.services.gemini_image import generate_marketing_image
from app.services.media import upload_to_storage
import uuid

async def test_generation():
    print("Testing local LCM Dreamshaper image generation...")
    image_bytes = await generate_marketing_image(
        trade_type="plumber",
        business_name="Super Pipes",
        description="Discounted winter pipe repair",
    )
    
    if image_bytes:
        print(f"✅ Generated image size: {len(image_bytes)} bytes")
        image_filename = f"marketing/test_{uuid.uuid4().hex}.png"
        url = upload_to_storage(image_bytes, image_filename, "image/png")
        print(f"✅ Image uploaded to MinIO: {url}")
        
        # In the context of our API, the external URL is webhook_base_url/api/media/...
        # But locally we can just print the MinIO internal one
    else:
        print("❌ Image generation failed")

if __name__ == "__main__":
    asyncio.run(test_generation())
