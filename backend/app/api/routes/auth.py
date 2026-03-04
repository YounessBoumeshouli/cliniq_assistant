import re

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.security import get_current_user
from app.schemas.user import LoginRequest, Token, UserCreate
from app.services.auth_service import authenticate_user
from app.services.user_service import Create_user, get_user_by_email, get_user_by_id
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])


def validate_password(password):
    if len(password) < 8:
        raise AppException("Le mot de passe doit contenir au moins 8 caractères")
    if not re.search(r"[A-Z]", password):
        raise AppException("Le mot de passe doit contenir une majuscule")
    if not re.search(r"[a-z]", password):
        raise AppException("Le mot de passe doit contenir une minuscule")
    if not re.search(r"[0-9]", password):
        raise AppException("Le mot de passe doit contenir un chiffre")


@router.post("/register", response_model=Token)
def register(request: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, request.email)
    if existing_user:
        raise AppException("Utilisateur déjà existant")
    validate_password(request.password)
    Create_user(db, request)
    token = authenticate_user(db, request.email, request.password)
    return token


@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    token = authenticate_user(db, request.email, request.password)
    if not token:
        raise AppException("Email ou mot de passe incorrect")
    return token


@router.get("/me")
def read_users_me(current_user: dict = Depends(get_current_user),db: Session = Depends(get_db)):
    user = get_user_by_id(db, current_user["id"])
    if not user:
        raise AppException("Utilisateur non trouvé")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": str(user.created_at),
    }
