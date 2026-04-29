"""
System Message Translations — all user-facing messages in 4 languages.
"""

SYSTEM_MESSAGES = {
    "welcome": {
        "en": "👋 Welcome! I'm your AI business assistant. How can I help you today?\n\nI can help with:\n📋 Quotes — \"Give me a quote for...\"\n📅 Scheduling — \"Book a job for...\"\n🧾 Invoices — \"Generate invoice for...\"\n🎨 Marketing — \"Make a promo for...\"",
        "hi": "👋 नमस्ते! मैं आपका AI बिजनेस असिस्टेंट हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?\n\nमैं इनमें मदद कर सकता हूँ:\n📋 कोटेशन — \"... के लिए कोटेशन दो\"\n📅 शेड्यूल — \"... के लिए जॉब बुक करो\"\n🧾 इनवॉइस — \"... का बिल बनाओ\"\n🎨 मार्केटिंग — \"... का प्रोमो बनाओ\"",
        "ta": "👋 வணக்கம்! நான் உங்கள் AI வணிக உதவியாளர். இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?\n\nநான் இவற்றில் உதவ முடியும்:\n📋 மேற்கோள் — \"...க்கு மேற்கோள் கொடு\"\n📅 திட்டமிடல் — \"...க்கு வேலை பதிவு செய்\"\n🧾 விலைப்பட்டியல் — \"...க்கு பில் உருவாக்கு\"",
        "ml": "👋 നമസ്കാരം! ഞാൻ നിങ്ങളുടെ AI ബിസിനസ് അസിസ്റ്റന്റ് ആണ്. ഇന്ന് ഞാൻ എങ്ങനെ സഹായിക്കാം?\n\nഞാൻ ഇവയിൽ സഹായിക്കാം:\n📋 ക്വോട്ടേഷൻ — \"...ന് ക്വോട്ടേഷൻ തരൂ\"\n📅 ഷെഡ്യൂൾ — \"...ന് ജോലി ബുക്ക് ചെയ്യൂ\"\n🧾 ഇൻവോയ്‌സ് — \"...ന്റെ ബിൽ ഉണ്ടാക്കൂ\"",
    },
    "quote_ready": {
        "en": "📋 Your quote is ready!",
        "hi": "📋 आपका कोटेशन तैयार है!",
        "ta": "📋 உங்கள் மேற்கோள் தயார்!",
        "ml": "📋 നിങ്ങളുടെ ക്വോട്ടേഷൻ തയ്യാറാണ്!",
    },
    "job_booked": {
        "en": "✅ Job booked successfully!",
        "hi": "✅ जॉब सफलतापूर्वक बुक हो गई!",
        "ta": "✅ வேலை வெற்றிகரமாக பதிவு செய்யப்பட்டது!",
        "ml": "✅ ജോലി വിജയകരമായി ബുക്ക് ചെയ്തു!",
    },
    "language_select": {
        "en": "🌐 Please select your preferred language:\n1️⃣ English\n2️⃣ हिंदी (Hindi)\n3️⃣ தமிழ் (Tamil)\n4️⃣ മലയാളം (Malayalam)\n\nReply with the number.",
    },
    "language_set": {
        "en": "✅ Language set to English!",
        "hi": "✅ भाषा हिंदी में सेट की गई!",
        "ta": "✅ மொழி தமிழாக அமைக்கப்பட்டது!",
        "ml": "✅ ഭാഷ മലയാളത്തിലേക്ക് മാറ്റി!",
    },
    "error_fallback": {
        "en": "⚠️ Sorry, I didn't understand. Could you rephrase?",
        "hi": "⚠️ क्षमा करें, मुझे समझ नहीं आया। क्या आप दोबारा बता सकते हैं?",
        "ta": "⚠️ மன்னிக்கவும், புரியவில்லை. மீண்டும் சொல்ல முடியுமா?",
        "ml": "⚠️ ക്ഷമിക്കണം, എനിക്ക് മനസ്സിലായില്ല. വീണ്ടും പറയാമോ?",
    },
    "processing": {
        "en": "⏳ Processing your request...",
        "hi": "⏳ आपका अनुरोध प्रोसेस हो रहा है...",
        "ta": "⏳ உங்கள் கோரிக்கை செயலாக்கப்படுகிறது...",
        "ml": "⏳ നിങ്ങളുടെ അഭ്യർത്ഥന പ്രോസസ്സ് ചെയ്യുന്നു...",
    },
    "image_analyzing": {
        "en": "📷 Image received! Analyzing... ⏳",
        "hi": "📷 इमेज मिल गई! विश्लेषण हो रहा है... ⏳",
        "ta": "📷 படம் பெறப்பட்டது! பகுப்பாய்வு செய்யப்படுகிறது... ⏳",
        "ml": "📷 ചിത്രം ലഭിച്ചു! വിശകലനം ചെയ്യുന്നു... ⏳",
    },
    "voice_heard": {
        "en": "🎤 I heard: \"{transcript}\"\n\n⏳ Processing...",
        "hi": "🎤 मैंने सुना: \"{transcript}\"\n\n⏳ प्रोसेस हो रहा है...",
        "ta": "🎤 நான் கேட்டேன்: \"{transcript}\"\n\n⏳ செயலாக்கப்படுகிறது...",
        "ml": "🎤 ഞാൻ കേട്ടു: \"{transcript}\"\n\n⏳ പ്രോസസ്സ് ചെയ്യുന്നു...",
    },
}


def get_message(key: str, language: str, **kwargs) -> str:
    """Get a localized system message with optional string formatting."""
    msgs = SYSTEM_MESSAGES.get(key, {})
    msg = msgs.get(language, msgs.get("en", ""))
    if kwargs:
        try:
            return msg.format(**kwargs)
        except (KeyError, IndexError):
            return msg
    return msg
