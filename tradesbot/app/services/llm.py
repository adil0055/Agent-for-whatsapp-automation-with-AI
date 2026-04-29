"""
LLM service — Groq-hosted Llama 3 via LangChain.
Provides a shared LLM instance and conversation memory.
"""
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.config import get_settings
from app.utils.logger import get_logger

log = get_logger("llm")
settings = get_settings()

_llm: ChatGroq = None


def get_llm() -> ChatGroq:
    """Get a shared Groq LLM instance (Llama 3 70B)."""
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=1024,
        )
        log.info("groq_llm_initialized", model="llama-3.3-70b-versatile")
    return _llm


async def chat(system_prompt: str, user_message: str, chat_history: list = None) -> str:
    """
    Send a message to the LLM with system prompt and optional history.
    Returns the assistant's response text.
    """
    llm = get_llm()
    messages = [SystemMessage(content=system_prompt)]

    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    response = await llm.ainvoke(messages)
    return response.content


async def chat_json(system_prompt: str, user_message: str) -> dict:
    """
    Send a message and parse the response as JSON.
    Falls back to raw text wrapped in a dict if JSON parsing fails.
    """
    raw = await chat(system_prompt, user_message)

    # Try to extract JSON from the response
    try:
        # Handle responses wrapped in ```json ... ```
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw.strip()

        return json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        log.warning("json_parse_failed", raw_preview=raw[:200])
        return {"raw_response": raw}
