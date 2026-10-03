from typing import Literal

from pydantic import BaseModel, Field, field_validator

Goal = Literal["weight loss", "muscle gain", "general wellness", "flexibility"]
Intensity = Literal["low", "medium", "high"]


class UserInput(BaseModel):
    user_id: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=120)
    age: int = Field(ge=13, le=120)
    weight: float = Field(gt=20, lt=500)
    goal: Goal
    intensity: Intensity

    @field_validator("user_id", "name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value

    @field_validator("goal")
    @classmethod
    def minor_goal_guard(cls, value: str, info):
        age = info.data.get("age")
        if age is not None and age < 18 and value == "weight loss":
            return "general wellness"
        return value


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2, max_length=64)
    feedback: str = Field(min_length=3, max_length=1000)


class Exercise(BaseModel):
    name: str
    sets_or_duration: str
    reps_or_time: str
    rest: str


class WorkoutDay(BaseModel):
    day: str
    focus: str
    warmup: str
    exercises: list[Exercise] = Field(min_length=1, max_length=8)
    cooldown: str


class WorkoutPlan(BaseModel):
    title: str
    safety_note: str
    days: list[WorkoutDay] = Field(min_length=7, max_length=7)


class NutritionTip(BaseModel):
    tip: str
    recovery_note: str
