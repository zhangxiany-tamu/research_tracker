from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
import os

# Use in-memory database for Google App Engine or writable temp directory
if os.getenv('GAE_ENV', '').startswith('standard'):
    # Google App Engine - use /tmp which is writable
    DATABASE_URL = "sqlite:////tmp/research_tracker.db"
else:
    # Local development
    DATABASE_URL = "sqlite:///./research_tracker.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()