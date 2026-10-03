import json
from typing import Any

from google import genai
from google.genai import types

from .config import get_settings
from .schemas import NutritionTip, UserInput, WorkoutPlan

settings = get_settings()


class AIServiceError(RuntimeError):
    pass


def _client() -> genai.Client:
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


def generate_workout_gemini(user: UserInput) -> WorkoutPlan:
    if settings.demo_mode:
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


def generate_nutrition_tip_with_flash(user: UserInput) -> NutritionTip:
    if settings.demo_mode:
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


def update_workout_plan(original_plan: str, user: UserInput, feedback: str) -> WorkoutPlan:
    if settings.demo_mode:
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


def demo_workout(user: UserInput) -> WorkoutPlan:
    focuses = [
        "Full body foundation", "Cardio and mobility", "Upper body", "Recovery and flexibility",
        "Lower body", "Core and light cardio", "Active recovery"
    ]
    exercise_bank = [
        ("Bodyweight squat", "3 sets", "8–12 reps", "60 sec"),
        ("Incline push-up", "3 sets", "6–12 reps", "60 sec"),
        ("Glute bridge", "3 sets", "10–15 reps", "45 sec"),
        ("Bird dog", "2 sets", "8–10/side", "30 sec"),
    ]
    days = []
    for index, focus in enumerate(focuses, start=1):
        exercises = [ExerciseProxy(*item) for item in exercise_bank[:3 if index != 4 and index != 7 else 2]]
        days.append({
            "day": f"Day {index}",
            "focus": focus,
            "warmup": "5–10 minutes of easy movement and dynamic mobility.",
            "exercises": [e.__dict__ for e in exercises],
            "cooldown": "5 minutes of easy movement and comfortable stretching; stop if pain occurs.",
        })
    return WorkoutPlan.model_validate({
        "title": f"FitBuddy 7-Day Plan for {user.name}",
        "safety_note": "Demo mode: this is sample content. Adjust activity to your comfort and seek qualified advice for injuries or medical restrictions.",
        "days": days,
    })


class ExerciseProxy:
    def __init__(self, name: str, sets_or_duration: str, reps_or_time: str, rest: str):
        self.name = name
        self.sets_or_duration = sets_or_duration
        self.reps_or_time = reps_or_time
        self.rest = rest


def demo_tip(user: UserInput) -> NutritionTip:
    if user.age < 18:
        return NutritionTip(tip="Choose regular balanced meals with protein, grains or other carbohydrates, fruits or vegetables, and enough fluids.", recovery_note="Aim for consistent sleep and easy recovery days between harder activities.")
    return NutritionTip(tip="Include a balanced source of protein and carbohydrate around your normal meals, and drink fluids regularly.", recovery_note="Prioritize sleep and recovery; increase training gradually rather than all at once.")


def plan_to_json(plan: WorkoutPlan) -> str:
    return json.dumps(plan.model_dump(), indent=2, ensure_ascii=False)
