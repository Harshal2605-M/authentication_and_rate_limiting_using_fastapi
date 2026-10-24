from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request 
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models, schemas
from app.security import hash_password
from app.routers.auth import router as auth_router
from app.dependencies import get_current_user
from app.rate_limit import is_rate_limited


@asynccontextmanager
async def lifespan(app:FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Authentication and Rate Limiting API",
    version="1.0.0",
    lifespan=lifespan,
)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):

    excluded_paths = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/docs/oauth2-redirect",
    }

    if request.url.path in excluded_paths:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"

    limited, retry_after = is_rate_limited(client_ip)

    if limited:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."},
            headers={"Retry-After": str(retry_after)},
        )

    return await call_next(request)


app.include_router(auth_router)

@app.get("/health")
def health_check():
    return {"status" : "healthy"}

@app.post(
    "/auth/register",
    response_model=schemas.UserResponse,
    status_code=201,
    )
def register_user(
    user_data : schemas.UserRegister,
    db : Session = Depends(get_db),
):
    email = str(user_data.email).lower()

    existing_user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if existing_user :
        raise HTTPException(
            status_code=409, 
            detail = "Email already registered",
        )

    user = models.User(
        email = email,
        hashed_password = hash_password(user_data.password),
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    return user

    
@app.get("/users/me")
def read_current_user(
    user: models.User = Depends(get_current_user),
):
    return {
        "id": user.id,
        "email": user.email,
    }

