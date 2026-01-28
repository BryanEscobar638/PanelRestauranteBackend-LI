from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.router import registro
from app.router import auth
from fastapi.responses import FileResponse
import os
from fastapi.staticfiles import StaticFiles

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
