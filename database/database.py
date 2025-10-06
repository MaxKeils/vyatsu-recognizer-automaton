"""Конфигурация базы данных и сессий."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import get_settings
import json

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=30,
    max_overflow=20,  
    echo=settings.debug,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False)
)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


def get_db():
    """
    Dependency для получения сессии БД.
    
    Используется в FastAPI endpoints через Depends.
    Автоматически закрывает сессию после использования.
    
    Yields:
        Session: Сессия базы данных
        
    Example:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Инициализирует базу данных.
    
    Создаёт все таблицы, определённые в моделях.
    Вызывается при запуске приложения.
    """
    # Import models to register them with Base
    from database.models import Configuration, Task, User, Submission
    Base.metadata.create_all(bind=engine)
