from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
import os

# Use PostgreSQL for production, SQLite for local development
if os.getenv('GAE_ENV', '').startswith('standard'):
    # Google App Engine - use Cloud SQL PostgreSQL
    connection_name = "research-tracker-466018:us-central1:research-tracker-db"
    DATABASE_URL = f"postgresql+psycopg2://postgres:research_tracker_secure_2025@/research_tracker?host=/cloudsql/{connection_name}"
else:
    # Local development - use SQLite
    DATABASE_URL = "sqlite:///./research_tracker.db"

if DATABASE_URL.startswith('postgresql'):
    # PostgreSQL specific configuration
    engine = create_engine(DATABASE_URL, echo=False)
else:
    # SQLite specific configuration
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