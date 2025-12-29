from database import SessionLocal
from models import AdminUser
from auth.security import hash_password

def create_admin(email: str, password: str):
    db = SessionLocal()

    existing = db.query(AdminUser).filter(AdminUser.email == email).first()
    if existing:
        print("❌ Admin already exists")
        return

    admin = AdminUser(
        email=email,
        hashed_password=hash_password(password)
    )

    db.add(admin)
    db.commit()
    db.close()

    print("✅ Admin created successfully")


if __name__ == "__main__":
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    create_admin(email, password)
