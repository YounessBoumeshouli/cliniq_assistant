from datetime import datetime

from app.core.database import Base
from sqlalchemy import Column, DateTime, Integer, String


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)
    hashed_password = Column(String)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
