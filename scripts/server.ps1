Write-Host "Iniciando Backend Panel Admin Restaurante..."
cd "D:\Cafeteria\Documents\PanelAdminRestaurante"

.\.venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000
