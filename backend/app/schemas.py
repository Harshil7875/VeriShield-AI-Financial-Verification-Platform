# backend/app/schemas.py

from pydantic import BaseModel, EmailStr

# ---------------------
#  User Schemas
# ---------------------
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    is_verified: bool

    class Config:
        orm_mode = True


# ---------------------
#  Business Schemas
# ---------------------
class BusinessBase(BaseModel):
    name: str

class BusinessCreate(BusinessBase):
    pass  # You could add more fields if needed

class BusinessRead(BusinessBase):
    id: int
    is_verified: bool

    class Config:
        orm_mode = True
