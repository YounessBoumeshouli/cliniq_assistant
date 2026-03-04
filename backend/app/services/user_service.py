from app.core.security import hash_password
from app.models.user import Users
from app.schemas.user import UserCreate
from sqlalchemy.orm import Session


def Create_user(db: Session, user: UserCreate):
    try:
        db_User = Users(
            username=user.username,
            email=user.email,
            hashed_password=hash_password(user.password),
            role=user.role,
        )
        db.add(db_User)
        db.commit()
        db.refresh(db_User)
        return db_User
    except Exception as e:
        db.rollback()
        raise e


def get_user_by_id(db: Session, user_id: int):
    return db.query(Users).filter(Users.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(Users).filter(Users.email == email).first()


def get_all_users(db: Session):
    return db.query(Users).all()


def delete_user(db: Session, user_id: int):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        return {"error": "User not found"}
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
