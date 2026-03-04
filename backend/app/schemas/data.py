from pydantic import BaseModel, ConfigDict, EmailStr

class User2(BaseModel):
    id : str
    name : str = "rachid"
    email : EmailStr

    