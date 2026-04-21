from datetime import datetime
import os
import logging
from typing import Generator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text

# Importaciones locales
from app.router import registro, auth
from core.database import SessionLocal

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ------------------------------------------------------------------
# Estáticos y Manuales
# ------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return {"message": "ok", "autor": "TECNOLOGIA LICEO INGLES"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/download/manual")
def descargar_manual():
    file_path = os.path.join(BASE_DIR, "download", "MANUAL_PANEL_RESTURANTE.pdf")
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename="MANUAL_PANEL_RESTURANTE.pdf"
    )

# ------------------------------------------------------------------
# Routers y Middleware
# ------------------------------------------------------------------
app.include_router(registro.router, prefix="/registro", tags=["registros"])
app.include_router(auth.router, prefix="/access", tags=["servicios de loggin"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Scheduler - Lógica para Supabase (PostgreSQL)
# ------------------------------------------------------------------
colombia_tz = timezone('America/Bogota')
scheduler = BackgroundScheduler(timezone=colombia_tz)

def ejecutar_registro_snack():
    # Usamos NOW() AT TIME ZONE 'America/Bogota' para que coincida con tu hora local
    print(f"--- INICIANDO INSERCIÓN AUTOMÁTICA SNACK: {datetime.now(colombia_tz)} ---")
    db = SessionLocal()
    try:
        query = text("""
            INSERT INTO public.registros_validacion (
                codigo_estudiante, nombre, tipo_alimentacion, plan, estado, fecha_hora, fecha
            )
            SELECT 
                e.codigo_estudiante, 
                e.nombre, 
                e.tipo_alimentacion, 
                'SNACK', 
                'NO RECLAMO', 
                (NOW() AT TIME ZONE 'America/Bogota'),
                CURRENT_DATE
            FROM public.estudiantes e
            LEFT JOIN public.registros_validacion r ON e.codigo_estudiante = r.codigo_estudiante 
                                            AND r.fecha = CURRENT_DATE
                                            AND r.plan = 'SNACK'
            WHERE r.codigo_estudiante IS NULL 
                AND e.tipo_alimentacion NOT IN ('NINGUNO', 'ALMUERZO', 'SOLO ALMUERZO')
                AND e.grado NOT IN ('K2', 'K3', 'K4', 'K5', '1', '2');
        """)
        db.execute(query)
        db.commit()
        print("✅ Inserción de SNACK completada exitosamente.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error en el scheduler (SNACK): {e}")
    finally:
        db.close()

def ejecutar_registro_lunch():
    print(f"--- INICIANDO INSERCIÓN AUTOMÁTICA LUNCH: {datetime.now(colombia_tz)} ---")
    db = SessionLocal()
    try:
        query = text("""
            INSERT INTO public.registros_validacion (
                codigo_estudiante, nombre, tipo_alimentacion, plan, estado, fecha_hora, fecha
            )
            SELECT 
                e.codigo_estudiante, 
                e.nombre, 
                e.tipo_alimentacion, 
                'LUNCH', 
                'NO RECLAMO', 
                (NOW() AT TIME ZONE 'America/Bogota'),
                CURRENT_DATE
            FROM public.estudiantes e
            LEFT JOIN public.registros_validacion r ON e.codigo_estudiante = r.codigo_estudiante 
                                            AND r.fecha = CURRENT_DATE
                                            AND r.plan = 'LUNCH'
            WHERE r.codigo_estudiante IS NULL 
                AND e.tipo_alimentacion NOT IN ('NINGUNO', 'REFRIGERIO', 'SOLO REFRIGERIO')
                AND e.grado NOT IN ('K2', 'K3', 'K4', 'K5', '1', '2');
        """)
        db.execute(query)
        db.commit()
        print("✅ Inserción de LUNCH completada exitosamente.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error en el scheduler (LUNCH): {e}")
    finally:
        db.close()

# ------------------------------------------------------------------
# Tareas Programadas
# ------------------------------------------------------------------
# scheduler.add_job(ejecutar_registro_snack, 'cron', hour=11, minute=30)
# scheduler.add_job(ejecutar_registro_lunch, 'cron', hour=14, minute=15)

# ------------------------------------------------------------------
# Eventos de Ciclo de Vida
# ------------------------------------------------------------------
# @app.on_event("startup")
# def startup_event():
#     if not scheduler.running:
#         scheduler.start()
#         logger.info("🚀 SCHEDULER INICIADO: Buscando faltantes en Supabase.")

# @app.on_event("shutdown")
# def shutdown_event():
#     scheduler.shutdown()
#     logger.info("🛑 SCHEDULER APAGADO.")