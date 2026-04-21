from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database - Valores por defecto (se sobreescriben con el .env)
    DB_HOST: str = "localhost"
    DB_PORT: str = "8432"  # Cambiado a str para facilitar la concatenación
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "postgres"

    # Esta variable se construirá automáticamente
    DATABASE_URL: Optional[str] = None

    # En core/config.py, cambia la línea de DATABASE_URL así:

    def model_post_init(self, __context) -> None:
        self.DATABASE_URL = (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?sslmode=disable"
        )

    class Config:
        env_file = ".env"
        # Esto permite que si en el .env ya viene una DATABASE_URL completa, la use
        extra = "ignore" 

settings = Settings()