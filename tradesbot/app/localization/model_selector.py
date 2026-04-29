"""
Model Selector — chooses the best LLM based on language and task.
Since we use Groq exclusively, this selects between available Groq models.
"""
from app.utils.logger import get_logger

log = get_logger("model_selector")

# Groq available models
MODELS = {
    "fast": "llama-3.1-8b-instant",          # Fast, good for English/Hinglish
    "versatile": "llama-3.3-70b-versatile",   # Best quality, all languages
    "vision": "llama-3.2-90b-vision-preview", # Vision tasks (OCR)
}


def select_model(language: str, is_code_mixed: bool, task: str) -> str:
    """
    Select the best Groq model for the given context.
    
    Strategy:
    - English/simple tasks → fast 8B model
    - Indic languages / complex tasks → versatile 70B model
    - Vision tasks → vision model
    """
    # Vision tasks always use vision model
    if task == "ocr":
        return MODELS["vision"]

    # Pure English + simple tasks can use faster model
    if language == "en" and not is_code_mixed and task in ("general", "schedule"):
        return MODELS["fast"]

    # Everything else uses the versatile model for best quality
    return MODELS["versatile"]
