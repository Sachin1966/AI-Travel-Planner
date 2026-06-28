import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./travel_planner.db")

# For SQLite, we add connect_args={"check_same_thread": False} to allow multi-threaded access (FastAPI request lifecycle)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    Dependency generator yielding a database session, ensuring it is closed properly.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initializes database tables.
    """
    # Import models here to ensure they register on Base metadata before creation
    import database.models
    Base.metadata.create_all(bind=engine)
