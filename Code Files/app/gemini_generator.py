import json
from typing import Any

from google import genai
from google.genai import types

from .config import get_settings
from .schemas import WorkoutPlan


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


def generate_workout_gemini(user: Any) -> WorkoutPlan:
    settings = get_settings()
    if getattr(settings, "demo_mode", False):
        from .ai import demo_workout
        return demo_workout(user)

    prompt = f"""
You are FitBuddy, a conservative wellness planning assistant.
Create a practical 7-day fitness plan for this profile:
Name: {user.name}
Age: {user.age}
Weight: {user.weight} kg
Goal: {user.goal}
Preferred intensity: {user.intensity}

Requirements:
- Return exactly 7 days.
- Each day needs a focus, warm-up, exercises, and cooldown/recovery guidance.
- Use accessible bodyweight or common-gym exercises.
- Include rest/recovery days where appropriate.
- Do not prescribe extreme exercise, crash diets, unsafe dehydration, supplements, or medical treatment.
- Do not diagnose injuries or illnesses.
- For anyone under 18, do not use weight as a target and do not provide weight-loss instructions; keep the plan focused on general fitness, movement skills, recovery, and enjoyment.
- Keep exercise descriptions concise and easy to follow.
"""
    return _generate_structured(settings.gemini_workout_model, prompt, WorkoutPlan)


def plan_to_json(plan: WorkoutPlan) -> str:
    return json.dumps(plan.model_dump(), indent=2, ensure_ascii=False)