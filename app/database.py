import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Getting the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Formating the path to the SQLite database
DATA_DIR = os.path.join(BASE_DIR, "data")
# Garanteeing that the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Full path to the SQLite database file
DB_PATH = os.path.join(DATA_DIR, "neuro_ligand.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Creating the SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Creating session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Main function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
