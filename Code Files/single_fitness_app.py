import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

app = FastAPI(title="FitBuddy AI Fitness Plan Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserProfile(BaseModel):
    age: int = Field(..., ge=13, le=100, description="User age in years")
    gender: str = Field(..., description="User gender (male/female/other)")
    weight: float = Field(..., gt=0, description="Weight in kg")
    height: float = Field(..., gt=0, description="Height in cm")
    activity_level: str = Field(
        ..., 
        description="Activity level (sedentary/light/moderate/active/very_active)"
    )
    goals: List[str] = Field(
        default=["general fitness"],
        description="Fitness goals"
    )
    restrictions: List[str] = Field(
        default=[],
        description="Exercise restrictions"
    )

class Exercise(BaseModel):
    name: str
    sets: int = Field(ge=1, le=10, description="Number of sets")
    reps: int = Field(ge=1, le=50, description="Repetitions per set")
    rest_seconds: int = Field(
        ge=0, le=300, 
        description="Rest time between sets in seconds"
    )
    difficulty: str = Field(
        default="moderate",
        description=" difficulty level (beginner/intermediate/advanced)"
    )

class FitnessPlan(BaseModel):
    user_profile: UserProfile
    warmup: List[Exercise]
    main_workout: List[Exercise]
    cooldown: List[Exercise]
    duration_minutes: int
    plan_name: str
    created_at: datetime.datetime

@app.get("/")
async def root():
    return {"message": "FitBuddy AI Fitness Plan Generator API", "version": "1.0.0"}

@app.post("/generate-plan", response_model=FitnessPlan)
async def generate_plan(profile: UserProfile):
    age = profile.age
    gender = profile.gender
    weight = profile.weight
    height = profile.height
    activity = profile.activity_level
    goals = profile.goals or ["general fitness"]
    restrictions = profile.restrictions or []

    bmi = weight / (height/100)**2

    if activity == "sedentary":
        base_calories = 2000
    elif activity == "light":
        base_calories = 2200
    elif activity == "moderate":
        base_calories = 2500
    elif activity == "active":
        base_calories = 2800
    else:
        base_calories = 3200

    if "weight loss" in goals:
        calorie_target = base_calories - 500
    elif "muscle gain" in goals:
        calorie_target = base_calories + 300
    else:
        calorie_target = base_calories

    age_factor = max(0.8, 1.0 - (age - 25) * 0.01)

    warmup = [
        Exercise(name="Dynamic stretching", sets=2, reps=10, rest_seconds=30, difficulty="beginner"),
        Exercise(name="Jumping jacks", sets=2, reps=15, rest_seconds=30, difficulty="beginner"),
        Exercise(name="Arm circles", sets=2, reps=12, rest_seconds=30, difficulty="beginner"),
    ]

    if age > 40 and "beginner" not in str(restrictions).lower():
        main_workout = [
            Exercise(name="Push-ups", sets=3, reps=8, rest_seconds=60, difficulty="intermediate"),
            Exercise(name="Bodyweight squats", sets=3, reps=12, rest_seconds=60, difficulty="intermediate"),
            Exercise(name="Lunges", sets=3, reps=10, rest_seconds=60, difficulty="intermediate"),
            Exercise(name="Plank", sets=3, reps=30, rest_seconds=60, difficulty="intermediate"),
        ]
    else:
        main_workout = [
            Exercise(name="Push-ups", sets=3, reps=10, rest_seconds=45, difficulty="beginner"),
            Exercise(name="Bodyweight squats", sets=3, reps=15, rest_seconds=45, difficulty="beginner"),
            Exercise(name="Lunges", sets=3, reps=12, rest_seconds=45, difficulty="beginner"),
            Exercise(name="Plank", sets=3, reps=30, rest_seconds=45, difficulty="beginner"),
        ]

    cooldown = [
        Exercise(name="Static stretching", sets=1, reps=30, rest_seconds=0, difficulty="beginner"),
        Exercise(name="Hamstring stretch", sets=1, reps=30, rest_seconds=0, difficulty="beginner"),
        Exercise(name="Quad stretch", sets=1, reps=30, rest_seconds=0, difficulty="beginner"),
    ]

    duration = 45 if activity in ["sedentary", "light"] else 60

    plan_name = f"FitBuddy Plan - {datetime.date.today().strftime('%B %d, %Y')}"

    plan = FitnessPlan(
        user_profile=profile,
        warmup=warmup,
        main_workout=main_workout,
        cooldown=cooldown,
        duration_minutes=duration,
        plan_name=plan_name,
        created_at=datetime.datetime.now()
    )

    return plan

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.now()}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)