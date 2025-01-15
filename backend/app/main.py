# backend/app/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import SessionLocal, engine, Base
from . import crud, schemas, models

app = FastAPI(title="VeriShield Phase 2")

# Create tables on startup (Dev only!). In production, use migrations (Alembic).
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "OK"}

# ----------------------------
#       User Endpoints
# ----------------------------
@app.post("/users", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = crud.create_user(db, user_in)
    return user

@app.get("/users/{user_id}", response_model=schemas.UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

@app.patch("/users/{user_id}/verify", response_model=schemas.UserRead)
def verify_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.update_user_verification(db, user_id, True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

# ----------------------------
#     Business Endpoints
# ----------------------------
@app.post("/businesses", response_model=schemas.BusinessRead, status_code=status.HTTP_201_CREATED)
def create_business(business_in: schemas.BusinessCreate, owner_id: int = None, db: Session = Depends(get_db)):
    existing = crud.get_business_by_name(db, business_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="Business name already taken.")
    business = crud.create_business(db, business_in, owner_id)
    return business

@app.get("/businesses/{business_id}", response_model=schemas.BusinessRead)
def get_business(business_id: int, db: Session = Depends(get_db)):
    biz = crud.get_business(db, business_id)
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found.")
    return biz

@app.patch("/businesses/{business_id}/verify", response_model=schemas.BusinessRead)
def verify_business(business_id: int, db: Session = Depends(get_db)):
    biz = crud.update_business_verification(db, business_id, True)
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found.")
    return biz
