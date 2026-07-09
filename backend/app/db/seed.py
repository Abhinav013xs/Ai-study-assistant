import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models.base import Base
from app.models.user import User, UserRole
from app.models.subject import Subject
from app.core.security import get_password_hash

def seed_db():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Check if test student already exists
        test_email = "student@academy.com"
        existing_user = db.query(User).filter(User.email == test_email).first()
        if existing_user:
            print("Database already seeded. Skipping.")
            return

        print("Seeding database with clean student user and subjects...")

        # 1. Create Student User
        student = User(
            email=test_email,
            hashed_password=get_password_hash("secret123"),
            full_name="Alex Mercer",
            role=UserRole.STUDENT,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        # 2. Create Subjects (Folder categories)
        cs = Subject(name="CS 401: Deep Learning", description="Neural network architectures and optimizer calculations.", color="#4F46E5", user_id=student.id)
        bio = Subject(name="BIO 302: Bioinformatics", description="Sequence alignment algorithms and phylogenetic trees.", color="#10B981", user_id=student.id)
        db.add_all([cs, bio])
        
        db.commit()
        print("Database seeded successfully! Try logging in with student@academy.com / secret123.")

    except Exception as e:
        db.rollback()
        print(f"Failed to seed database: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
