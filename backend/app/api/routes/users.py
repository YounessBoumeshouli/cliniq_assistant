from app.core.database import get_db
from app.core.security import get_current_user
from app.services.user_service import delete_user, get_all_users, get_user_by_id
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
def users_root(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_all_users(db)


@router.get("/{user_id}")
def get_user(user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_by_id(db, user_id)


@router.delete("/{user_id}")
def delete_user_by_id(user_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return delete_user(db, user_id)
