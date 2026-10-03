import json
from typing import Any

from google import genai
from google.genai import types

from .config import get_settings
from .schemas import NutritionTip


class AIServiceError(RuntimeError):
    pass


def _client() -> genai.Client:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise AIServiceError("GEMINI_API_KEY is not configured. Set it in .env or enable DEMO_MODE=true.")
    return genai.Client(api_key=settings.gemini_api_key)


def _generate_structured(model: str, prompt: str, schema: type[Any]) -> Any:
    try:
        response = _client().models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.6,
            ),
        )
        if getattr(response, "parsed", None) is not None:
            return response.parsed
        if not response.text:
            raise AIServiceError("Gemini returned an empty response.")
        return schema.model_validate_json(response.text)
    except AIServiceError:
        raise
    except Exception as exc:
        raise AIServiceError(f"Gemini request failed: {exc}") from exc


def generate_nutrition_tip_with_flash(user: Any) -> NutritionTip:
    settings = get_settings()
    if getattr(settings, "demo_mode", False):
        from .ai import demo_tip
        return demo_tip(user)

    goal = "general wellness" if user.age < 18 else user.goal
    prompt = f"""
Create one concise nutrition/recovery tip for a FitBuddy user.
Age: {user.age}
Goal: {goal}
Intensity: {user.intensity}

Keep it general and practical. Encourage balanced meals, hydration, sleep, and recovery.
Do not prescribe calorie restriction, fasting, supplements, or medical treatment.
If under 18, avoid weight-loss advice and focus on regular balanced meals and healthy habits.
Return only the requested structured fields.
"""
    return _generate_structured(settings.gemini_tip_model, prompt, NutritionTip)