from typing import Generator
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
from sqlalchemy.pool import QueuePool

from core.config import settings

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Engine
# ------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,             # 🔴 Cambia a True solo en desarrollo
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    poolclass=QueuePool,
    future=True             # ✅ Recomendado SQLAlchemy 2.x
)

# ------------------------------------------------------------------
# Session
# ------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True
)

# ------------------------------------------------------------------
# Base ORM
# ------------------------------------------------------------------
Base = declarative_base()

# ------------------------------------------------------------------
# Dependency
# ------------------------------------------------------------------
def get_db() -> Generator:
    """
    Dependencia para obtener una sesión de base de datos en FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Error de base de datos", exc_info=e)
        raise
    finally:
        db.close()

# ------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------
def check_database_connection() -> bool:
    """
    Verifica la conexión a la base de datos.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except (OperationalError, DisconnectionError) as e:
        logger.error("Error de conexión a la base de datos", exc_info=e)
        return False


# ------------------------------------------------------------------
# Standalone test
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("¿Conexión exitosa?:", check_database_connection())