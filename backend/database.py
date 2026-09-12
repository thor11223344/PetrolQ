import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Read the database URL from environment, default to a local Postgres instance
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:YOUR_PASSWORD_HERE@localhost:5432/petrolq_nwis"
).strip()


# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models
Base = declarative_base()

# Dependency function to yield database sessions for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
