from pydantic import BaseModel, EmailStr


class User2(BaseModel):
    id: str
    name: str = "rachid"
    email: EmailStr
