import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- МАГИЯ ПУТЕЙ ---
# Получаем путь к корню проекта (выходим из папки app назад)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Формируем путь к папке data
DATA_DIR = os.path.join(BASE_DIR, "data")
# Гарантируем, что папка существует
os.makedirs(DATA_DIR, exist_ok=True)

# Указываем полный путь к файлу базы
DB_PATH = os.path.join(DATA_DIR, "neuro_ligand.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Создаем движок
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Создаем сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Главная функция (называется get_db, без единичек!)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
