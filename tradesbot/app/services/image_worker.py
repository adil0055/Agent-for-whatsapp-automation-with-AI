"""
Local Image Generation Worker
Runs a FastAPI service inside a separate container to generate images using SDXL Turbo.
Requires an NVIDIA GPU.
"""
import io
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from diffusers import AutoPipelineForText2Image

app = FastAPI(title="Local Image Gen API")

pipe = None

def load_model():
    global pipe
    if pipe is not None:
        return
    print("Loading LCM Dreamshaper model onto GPU to save RAM...")
    try:
        pipe = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sd-turbo",
            torch_dtype=torch.float16,
            variant="fp16"
        )
        pipe.to("cuda")
        print("✅ LCM Dreamshaper loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        raise e

class ImageRequest(BaseModel):
    prompt: str

@app.post("/generate")
def generate_image(req: ImageRequest):
    if pipe is None:
        load_model()
    
    try:
        # sd-turbo generates great images in 1-2 steps
        image = pipe(
            prompt=req.prompt, 
            num_inference_steps=2, 
            guidance_scale=0.0
        ).images[0]
        
        # Convert to PNG bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        
        return Response(content=img_byte_arr.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
