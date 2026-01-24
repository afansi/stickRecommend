from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from database import get_session
from models.tables import User
from auth.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=User)
def register(user_details: User, session: Session = Depends(get_session)):
    # Check existing
    existing = session.exec(select(User).where(User.username == user_details.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password (User Pydantic model has hashed_password field, but we receive raw via 'hashed_password' alias or separate DTO. 
    # For MVP simplicity, we assume the client sends 'hashed_password' as the raw password text in the JSON body, which we then hash.
    # A proper DTO (UserCreate) would be better but keeping it simple.)
    raw_password = user_details.hashed_password 
    user_details.hashed_password = get_password_hash(raw_password)
    
    session.add(user_details)
    session.commit()
    session.refresh(user_details)
    return user_details

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
