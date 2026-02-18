"""Create test users kevin and ron"""
import sys
sys.path.insert(0, '/root/welldoc-demos/solution-1-fda-automation/backend')

from app.core.database import engine, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create users table
from app.core.database import Base
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Check if users already exist
kevin = db.query(User).filter(User.username == "kevin").first()
ron = db.query(User).filter(User.username == "ron").first()

if not kevin:
    kevin = User(
        username="kevin",
        email="kevin@welldoc.com",
        hashed_password=get_password_hash("WellDoc2026!"),
        full_name="Kevin (Administrator)",
        role="admin",
        is_active=True
    )
    db.add(kevin)
    print("Created user: kevin")
else:
    print("User kevin already exists")

if not ron:
    ron = User(
        username="ron",
        email="ron@welldoc.com",
        hashed_password=get_password_hash("WellDoc2026!"),
        full_name="Ron (Reviewer)",
        role="user",
        is_active=True
    )
    db.add(ron)
    print("Created user: ron")
else:
    print("User ron already exists")

db.commit()
db.close()

print("\nUsers created successfully!")
print("Username: kevin | Password: WellDoc2026! | Role: admin")
print("Username: ron | Password: WellDoc2026! | Role: user")
