from fastapi import APIRouter
from pydantic import BaseModel
from deep_translator import GoogleTranslator

router = APIRouter()

SUPPORTED = {
    "en": "English", "hi": "Hindi", "kn": "Kannada",
    "sa": "Sanskrit", "ta": "Tamil", "te": "Telugu",
    "ml": "Malayalam", "mr": "Marathi", "bn": "Bengali",
    "gu": "Gujarati", "pa": "Punjabi", "fr": "French",
    "de": "German", "es": "Spanish", "ja": "Japanese",
    "zh-CN": "Chinese (Simplified)",
}

# deep-translator uses different code for some langs
_CODE_MAP = {
    "sa": "auto",   # Sanskrit → translate from auto-detected source
    "zh-CN": "zh-CN",
}

class TranslateRequest(BaseModel):
    text: str
    target: str   # language code e.g. "hi", "kn", "en"

@router.post("/api/translate")
def translate(req: TranslateRequest):
    if req.target not in SUPPORTED:
        return {"error": f"Unsupported target language: {req.target}"}
    if not req.text.strip():
        return {"translated": ""}
    try:
        target_code = _CODE_MAP.get(req.target, req.target)
        translator = GoogleTranslator(source="auto", target=target_code)
        # deep-translator has a 5000 char limit per call — chunk if needed
        text = req.text
        if len(text) <= 4500:
            result = translator.translate(text)
        else:
            # Split on double newline (paragraph boundaries), translate each
            parts = text.split("\n\n")
            translated_parts = []
            for part in parts:
                if part.strip():
                    translated_parts.append(translator.translate(part))
                else:
                    translated_parts.append("")
            result = "\n\n".join(translated_parts)
        return {"translated": result, "target": req.target}
    except Exception as e:
        return {"error": str(e)}
