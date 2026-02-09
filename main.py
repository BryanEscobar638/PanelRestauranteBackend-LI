from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text
from app.router import registro
from app.router import auth
from fastapi.responses import FileResponse
import os
from fastapi.staticfiles import StaticFiles

from core.database import SessionLocal

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()
    

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
@app.get("/download/manual")
def descargar_manual():
    file_path = os.path.join(BASE_DIR, "download", "MANUAL_PANEL_RESTURANTE.pdf")
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename="MANUAL_PANEL_RESTURANTE.pdf"
    )

# Incluir en el objeto app los routers
app.include_router(registro.router, prefix="/registro", tags=["registros"])
app.include_router(auth.router, prefix="/access", tags=["servicios de loggin"])

# Configuración de CORS para permitir todas las solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir solicitudes desde cualquier origen
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Permitir estos métodos HTTP
    allow_headers=["*"],  # Permitir cualquier encabezado en las solicitudes
)

@app.get("/")
def read_root():
    return {
                "message": "ok",
                "autor": "TECNOLOGIA LICEO INGLES"
            }

# EVENTOS
# 1. Configuración del Scheduler (Fuera de las funciones)
colombia_tz = timezone('America/Bogota')
scheduler = BackgroundScheduler(timezone=colombia_tz)

# 2. La función que hace el trabajo
def ejecutar_registro_snack():
    print(f"--- INICIANDO INSERCIÓN AUTOMÁTICA: {datetime.now(colombia_tz)} ---")
    db = SessionLocal()
    try:
        query = text("""
            INSERT INTO registros_validacion (
                codigo_estudiante, nombre, tipo_alimentacion, plan, estado, fecha_hora
            )
            SELECT 
                e.codigo_estudiante, e.nombre, e.tipo_alimentacion, 'SNACK', 'NO RECLAMO', NOW() 
            FROM estudiantes e
            LEFT JOIN registros_validacion r ON e.codigo_estudiante = r.codigo_estudiante 
                                            AND r.fecha = CURRENT_DATE
                                            AND r.plan = 'SNACK'
            WHERE r.codigo_estudiante IS NULL 
                AND e.tipo_alimentacion != 'NINGUNO'
                AND e.tipo_alimentacion != 'ALMUERZO'
                AND e.tipo_alimentacion != 'SOLO ALMUERZO'
                AND e.grado NOT IN ('K2', 'K3', 'K4', 'K5', '1', '2');
        """)
        db.execute(query)
        db.commit()
        print("✅ Inserción de SNACK completada exitosamente.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error en el scheduler: {e}")
    finally:
        db.close()

def ejecutar_registro_lunch():
    print(f"--- INICIANDO INSERCIÓN AUTOMÁTICA: {datetime.now(colombia_tz)} ---")
    db = SessionLocal()
    try:
        query = text("""
            INSERT INTO registros_validacion (
                codigo_estudiante, nombre, tipo_alimentacion, plan, estado, fecha_hora
            )
            SELECT 
                e.codigo_estudiante, e.nombre, e.tipo_alimentacion, 'LUNCH', 'NO RECLAMO', NOW() 
            FROM estudiantes e
            LEFT JOIN registros_validacion r ON e.codigo_estudiante = r.codigo_estudiante 
                                            AND r.fecha = CURRENT_DATE
                                            AND r.plan = 'LUNCH'
            WHERE r.codigo_estudiante IS NULL 
                AND e.tipo_alimentacion != 'NINGUNO'
                AND e.tipo_alimentacion != 'REFRIGERIO'
                AND e.tipo_alimentacion != 'SOLO REFRIGERIO'
                AND e.grado NOT IN ('K2', 'K3', 'K4', 'K5', '1', '2');
        """)
        db.execute(query)
        db.commit()
        print("✅ Inserción de LUNCH completada exitosamente.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error en el scheduler: {e}")
    finally:
        db.close()

# 3. Programar la tarea (Ajusta la hora a un par de minutos a futuro)
scheduler.add_job(ejecutar_registro_snack, 'cron', hour=11, minute=30)
scheduler.add_job(ejecutar_registro_lunch, 'cron', hour=14, minute=15)

# 4. Eventos de ciclo de vida de FastAPI
@app.on_event("startup")
def startup_event():
    if not scheduler.running:
        scheduler.start()
        print("🚀 SCHEDULER INICIADO: El sistema buscará faltantes a la hora programada.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    print("🛑 SCHEDULER APAGADO.")
