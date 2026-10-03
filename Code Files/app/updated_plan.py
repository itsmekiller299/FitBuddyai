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


def update_workout_plan(original_plan: str, user: Any, feedback: str) -> WorkoutPlan:
    settings = get_settings()
    if getattr(settings, "demo_mode", False):
        from .ai import demo_workout
        plan = demo_workout(user)
        plan.title = "Updated FitBuddy 7-Day Plan"
        plan.safety_note = f"Updated using feedback: {feedback[:180]}"
        return plan

    prompt = f"""
You are updating a FitBuddy 7-day wellness plan.
User profile: age={user.age}, goal={user.goal}, intensity={user.intensity}.
Original plan JSON:
{original_plan}

User feedback:
{feedback}

Create a revised 7-day plan. Apply reasonable changes requested by the feedback while
preserving safe progression, recovery, and the user's general goal. Do not introduce
extreme exercise, crash dieting, dehydration, medical treatment, or injury diagnosis.
For users under 18, avoid weight-loss instructions and keep the plan centered on healthy movement and recovery.
Return exactly 7 days in the required schema.
"""
    return _generate_structured(settings.gemini_workout_model, prompt, WorkoutPlan)