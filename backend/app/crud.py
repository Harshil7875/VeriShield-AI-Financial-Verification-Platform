# backend/app/crud.py

from sqlalchemy.orm import Session
from passlib.context import CryptContext

from . import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --------------------
#  User CRUD
# --------------------
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user_in: schemas.UserCreate):
    hashed_pw = pwd_context.hash(user_in.password)
    user = models.User(
        email=user_in.email,
        password_hash=hashed_pw
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_user_verification(db: Session, user_id: int, verified: bool):
    user = get_user(db, user_id)
    if user:
        user.is_verified = verified
        db.commit()
        db.refresh(user)
    return user


# --------------------
#  Business CRUD
# --------------------
def get_business_by_name(db: Session, name: str):
    return db.query(models.Business).filter(models.Business.name == name).first()

def create_business(db: Session, business_in: schemas.BusinessCreate, owner_id: int = None):
    business = models.Business(
        name=business_in.name,
        owner_id=owner_id
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business

def get_business(db: Session, business_id: int):
    return db.query(models.Business).filter(models.Business.id == business_id).first()

def update_business_verification(db: Session, business_id: int, verified: bool):
    business = get_business(db, business_id)
    if business:
        business.is_verified = verified
        db.commit()
        db.refresh(business)
    return business
