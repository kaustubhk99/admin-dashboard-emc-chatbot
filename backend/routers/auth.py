from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import AdminUser
from schemas import AdminLoginRequestSchema, AdminLoginResponseSchema
from auth.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login", response_model=AdminLoginResponseSchema)
def admin_login(
    data: AdminLoginRequestSchema,
    db: Session = Depends(get_db)
):
    admin = db.query(AdminUser).filter(AdminUser.email == data.email).first()
    if not admin or not verify_password(data.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
    "sub": str(admin.id),
    "email": admin.email,
    "role": "admin"
    })

    return {"access_token": token}
