from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .models import Plan, User
from .schemas import UserInput


def save_user(db: Session, data: UserInput) -> User:
    user = db.scalar(select(User).where(User.user_id == data.user_id))
    if user is None:
        user = User(user_id=data.user_id)
        db.add(user)
    user.name = data.name
    user.age = data.age
    user.weight = data.weight
    user.goal = data.goal
    user.intensity = data.intensity
    db.commit()
    db.refresh(user)
    return user


def save_plan(db: Session, user: User, original_plan: str, nutrition_tip: str) -> Plan:
    plan = Plan(user_id=user.id, original_plan=original_plan, nutrition_tip=nutrition_tip)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(db: Session, plan: Plan, updated_plan: str, feedback: str) -> Plan:
    plan.updated_plan = updated_plan
    plan.feedback = feedback
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)
    return plan


def get_user(db: Session, user_id: str) -> User | None:
    return db.scalar(select(User).where(User.user_id == user_id))


def get_original_plan(db: Session, user_id: str) -> Plan | None:
    user = get_user(db, user_id)
    if not user:
        return None
    return db.scalar(select(Plan).where(Plan.user_id == user.id).order_by(Plan.id.desc()))


def get_all_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).options(joinedload(User.plans)).order_by(User.created_at.desc()).unique()).all())


def delete_user(db: Session, user_id: str) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
