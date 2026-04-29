"""
Localized Prompt Builder — injects language instructions into agent prompts.
"""

LANGUAGE_INSTRUCTIONS = {
    "en": "Respond entirely in English. Use clear, simple language.",
    "hi": "पूरी तरह हिंदी में जवाब दें। सरल और स्पष्ट भाषा का प्रयोग करें। तकनीकी शब्द अंग्रेजी में रख सकते हैं।",
    "ta": "முழுவதும் தமிழில் பதிலளிக்கவும். எளிய மற்றும் தெளிவான மொழியைப் பயன்படுத்தவும்.",
    "ml": "പൂർണ്ണമായും മലയാളത്തിൽ മറുപടി നൽകുക. ലളിതവും വ്യക്തവുമായ ഭാഷ ഉപയോഗിക്കുക.",
    "code_mixed_hi": "Respond in Hinglish (Hindi + English mix). Match the user's style. Technical terms can stay in English.",
    "code_mixed_ta": "Respond in Tanglish (Tamil + English mix). Match the user's style.",
    "code_mixed_ml": "Respond in Manglish (Malayalam + English mix). Match the user's style.",
}


def build_localized_prompt(base_prompt: str, language: str, is_code_mixed: bool = False) -> str:
    """Inject language instructions into any agent prompt."""
    lang_key = f"code_mixed_{language}" if is_code_mixed else language
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(lang_key, LANGUAGE_INSTRUCTIONS["en"])

    return f"""{base_prompt}

LANGUAGE INSTRUCTION:
{lang_instruction}

IMPORTANT: Do NOT translate technical terms commonly used in English 
(e.g., GST, plumber, AC, pipe, switch, wire). Keep numbers in Arabic numerals.
Currency should always be shown as ₹."""


def get_language_name(code: str) -> str:
    """Get human-readable language name."""
    names = {"en": "English", "hi": "Hindi", "ta": "Tamil", "ml": "Malayalam", "kn": "Kannada", "te": "Telugu"}
    return names.get(code, "English")
