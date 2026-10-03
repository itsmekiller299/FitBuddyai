from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import secrets

from .config import get_settings
from .database import get_db
from .schemas import FeedbackRequest, UserInput
from .services import delete_user, get_all_users, get_original_plan, get_user, save_plan, save_user, update_plan
from .gemini_generator import AIServiceError, generate_workout_gemini, plan_to_json
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .updated_plan import update_workout_plan

router = APIRouter()
templates = Jinja2Templates(directory="templates")
settings = get_settings()


def admin_auth(credentials: HTTPBasicCredentials = Depends(HTTPBasic())) -> str:
    valid_user = secrets.compare_digest(credentials.username, settings.admin_username)
    valid_password = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (valid_user and valid_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials", headers={"WWW-Authenticate": "Basic"})
    return credentials.username


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    user_id: str = Form(...),
    name: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user = UserInput(user_id=user_id, name=name, age=age, weight=weight, goal=goal, intensity=intensity)
        workout = generate_workout_gemini(user)
        tip = generate_nutrition_tip_with_flash(user)
        saved_user = save_user(db, user)
        plan = save_plan(db, saved_user, plan_to_json(workout), tip.model_dump_json())
        return templates.TemplateResponse(request=request, name="result.html", context={
            "request": request,
            "user": user,
            "plan": workout,
            "nutrition_tip": tip,
            "plan_id": plan.id,
            "message": None,
            "error": None,
        })
    except (ValueError, AIServiceError) as exc:
        return templates.TemplateResponse(request=request, name="error.html", context={"request": request, "error": str(exc)}, status_code=400)


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        request_data = FeedbackRequest(user_id=user_id, feedback=feedback)
        user_record = get_user(db, request_data.user_id)
        plan_record = get_original_plan(db, request_data.user_id)
        if not user_record or not plan_record:
            raise ValueError("No saved plan was found for that User ID.")
        user = UserInput(user_id=user_record.user_id, name=user_record.name, age=user_record.age, weight=user_record.weight, goal=user_record.goal, intensity=user_record.intensity)
        revised = update_workout_plan(plan_record.original_plan, user, request_data.feedback)
        update_plan(db, plan_record, plan_to_json(revised), request_data.feedback)
        return templates.TemplateResponse(request=request, name="result.html", context={
            "request": request,
            "user": user,
            "plan": revised,
            "nutrition_tip": None,
            "plan_id": plan_record.id,
            "message": "Your plan was updated from the feedback.",
            "error": None,
        })
    except (ValueError, AIServiceError) as exc:
        return templates.TemplateResponse(request=request, name="error.html", context={"request": request, "error": str(exc)}, status_code=400)


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, _: str = Depends(admin_auth), db: Session = Depends(get_db)):
    users = get_all_users(db)
    return templates.TemplateResponse(request=request, name="all_users.html", context={"request": request, "users": users})


@router.post("/admin/delete/{user_id}")
def admin_delete_user(user_id: str, _: str = Depends(admin_auth), db: Session = Depends(get_db)):
    delete_user(db, user_id)
    return RedirectResponse(url="/view-all-users", status_code=303)


@router.get("/api/health")
def health():
    return {"status": "ok", "service": "FitBuddy"}


@router.get("/api/users/{user_id}")
def api_user(user_id: str, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user.user_id,
        "name": user.name,
        "age": user.age,
        "weight": user.weight,
        "goal": user.goal,
        "intensity": user.intensity,
        "plans": [
            {
                "id": p.id,
                "original_plan": p.original_plan,
                "updated_plan": p.updated_plan,
                "feedback": p.feedback,
                "nutrition_tip": p.nutrition_tip,
            }
            for p in user.plans
        ],
    }