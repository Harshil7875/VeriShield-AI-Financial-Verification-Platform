# backend/app/crud.py

from sqlalchemy.orm import Session
from passlib.context import CryptContext

from . import models, schemas
from .kafka_producer import publish_event  # <-- New import for Phase 3

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --------------------
#  User CRUD
# --------------------
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user_in: schemas.UserCreate):
    """
    Creates a new user in the DB, then publishes a 'user_created' event to Kafka.
    """
    hashed_pw = pwd_context.hash(user_in.password)
    user = models.User(
        email=user_in.email,
        password_hash=hashed_pw
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Publish Kafka event
    event_data = {
        "action": "UserCreated",
        "user_id": user.id,
        "email": user.email
    }
    publish_event(topic="user_created", data=event_data)

    return user


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def update_user_verification(db: Session, user_id: int, verified: bool):
    """
    Updates a user's is_verified status, then publishes a 'user_verified' (or 'user_unverified') event.
    """
    user = get_user(db, user_id)
    if user:
        user.is_verified = verified
        db.commit()
        db.refresh(user)

        # Publish event indicating verification status
        event_name = "UserVerified" if verified else "UserUnverified"
        event_data = {
            "action": event_name,
            "user_id": user.id,
            "email": user.email,
            "is_verified": user.is_verified
        }
        publish_event(topic="user_verified", data=event_data)

    return user


# --------------------
#  Business CRUD
# --------------------
def get_business_by_name(db: Session, name: str):
    return db.query(models.Business).filter(models.Business.name == name).first()


def create_business(db: Session, business_in: schemas.BusinessCreate, owner_id: int = None):
    """
    Creates a new business in the DB, then publishes a 'business_created' event to Kafka.
    """
    business = models.Business(
        name=business_in.name,
        owner_id=owner_id
    )
    db.add(business)
    db.commit()
    db.refresh(business)

    # Publish Kafka event
    event_data = {
        "action": "BusinessCreated",
        "business_id": business.id,
        "name": business.name,
        "owner_id": business.owner_id
    }
    publish_event(topic="business_created", data=event_data)

    return business


def get_business(db: Session, business_id: int):
    return db.query(models.Business).filter(models.Business.id == business_id).first()


def update_business_verification(db: Session, business_id: int, verified: bool):
    """
    Updates a business's is_verified status, then publishes a 'business_verified' event.
    """
    business = get_business(db, business_id)
    if business:
        business.is_verified = verified
        db.commit()
        db.refresh(business)

        # Publish event indicating business verification
        event_name = "BusinessVerified" if verified else "BusinessUnverified"
        event_data = {
            "action": event_name,
            "business_id": business.id,
            "name": business.name,
            "is_verified": business.is_verified
        }
        publish_event(topic="business_verified", data=event_data)

    return business
