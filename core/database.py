from typing import Generator
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

from core.config import settings

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Engine configuration
# ------------------------------------------------------------------
# Supabase/Postgres tips:
# 1. pool_pre_ping: Re-conecta automáticamente si el servidor cerró la conexión.
# 2. pool_recycle: Evita "Stale connections" (conexiones viejas).
# 3. sslmode: 'require' es fundamental para la seguridad en la nube.

# En core/database.py
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,             
    pool_pre_ping=True,
    # Asegúrate de que NO haya un connect_args pidiendo sslmode require aquí
)

# ------------------------------------------------------------------
# Session & Base
# ------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False, # ✅ Evita errores al acceder a objetos después de un commit
    future=True
)

Base = declarative_base()

# ------------------------------------------------------------------
# Dependency (FastAPI)
# ------------------------------------------------------------------
def get_db() -> Generator:
    """
    Inyecta la sesión de DB. El uso de context manager asegura el cierre.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"❌ SQLAlchemy Error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado en DB: {str(e)}")
        raise
    finally:
        db.close()

# ------------------------------------------------------------------
# Utilidades de Diagnóstico
# ------------------------------------------------------------------
def check_database_connection() -> bool:
    """
    Prueba rápida de latencia y conexión.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            # No es estrictamente necesario el commit para un SELECT 1, 
            # pero asegura que la transacción cierre limpia.
            connection.rollback() 
        return True
    except Exception as e:
        logger.error(f"❌ Error crítico de conexión: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"--- Diagnóstico de Conexión ---")
    print(f"Host: {settings.DB_HOST}")
    print(f"Puerto: {settings.DB_PORT}")
    
    if check_database_connection():
        print("✅ Resultado: Conexión Exitosa.")
    else:
        print("❌ Resultado: Error de Conexión. Revisa SSL y Credenciales.")