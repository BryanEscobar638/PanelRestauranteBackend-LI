from datetime import date
from io import BytesIO
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, logger, status
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.searchs.registro import buscar_estudiantes, consumo_mes_actual, count_all_students, count_students_today, get_all_registers_all, get_estudiantes_con_plan, total_planalimenticio, get_all_registers, get_registers_filtered, get_registers_today
from core.database import get_db

router = APIRouter()

# endpoint para conseguir los ultimos 15 estudiantes
@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Obtener estudiantes (máx. 15)",
    description="Devuelve hasta 15 registros de la tabla estudiantes ordenado por los mas recientes"
)
def listar_estudiantes(db: Session = Depends(get_db)):
    try:
        registros = get_all_registers(db)
        return {
            "total": len(registros),
            "data": registros
        }
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los estudiantes"
        )
    
# endpoint para conseguir los todos los estudiantes
@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    summary="Obtener estudiantes paginados",
    description="Devuelve una lista paginada de todos los estudiantes registrados."
)
def listar_estudiantes(
    db: Session = Depends(get_db),
    page: int = 1, # Página por defecto
    size: int = 50 # Registros por página por defecto
):
    try:
        # Pasamos los parámetros de paginación a la función del controlador
        resultado = get_all_registers_all(db, page=page, size=size)
        
        # 'resultado' ya es un diccionario que contiene:
        # {"total": X, "page": Y, "size": Z, "data": [...]}
        return resultado

    except SQLAlchemyError as e:
        logger.error(f"Error en endpoint /all: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los estudiantes de la base de datos"
        )

@router.get("/hoy",status_code=status.HTTP_200_OK,
    summary="Obtener estudiantes registrados en el dia actual",
    description="Devuelve todos los estudiantes registrados en el dia actual por el mas reciente")
def listar_registros_hoy(
    db: Session = Depends(get_db),
    codigo_estudiante: Optional[str] = None
):
    """
    Devuelve los registros del día de hoy.
    Si se pasa 'codigo_estudiante', filtra por ese estudiante.
    """
    try:
        registros = get_registers_today(db, codigo_estudiante=codigo_estudiante)
        return {
            "codigo_estudiante": codigo_estudiante or "todos",
            "fecha": date.today(),
            "total": len(registros),
            "data": registros
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener los registros del día: {e}"
        )


@router.get("/filtrar", status_code=status.HTTP_200_OK,
    summary="Buscador con filtros avanzados y paginación",
    description="Permite filtrar por rango de fechas, código, nombre y plan, devolviendo resultados paginados.")
def listar_registros_filtrados(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    codigo_estudiante: Optional[str] = Query(None, description="Código del estudiante"),
    nombre: Optional[str] = Query(None, description="Nombre del estudiante (búsqueda aproximada)"),
    plan: Optional[str] = Query(None, description="Tipo de plan: REFRIGERIO, ALMUERZO o TODOS"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(50, ge=1, le=100, description="Registros por página"),
    db: Session = Depends(get_db)
):
    """
    Endpoint que integra filtros y paginación para optimizar el rendimiento del Dashboard.
    """
    print(f"🔍 Filtrando Paginado: Inicio={fecha_inicio}, Fin={fecha_fin}, Codigo={codigo_estudiante}, Nombre={nombre}, Plan={plan}, Pagina={page}")
    
    # Llamamos al controlador pasando los nuevos parámetros de paginación
    resultado = get_registers_filtered(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        codigo_estudiante=codigo_estudiante,
        nombre=nombre,
        plan=plan,
        page=page,
        size=size
    )

    # 'resultado' ya contiene { "total": X, "page": Y, "size": Z, "data": [...] }
    return resultado


@router.get("/excel", status_code=status.HTTP_200_OK,
    summary="Descargar con filtros en un excel",
    description="Permite descargar registros filtrando por fecha, código, nombre o tipo de plan.")
def descargar_excel(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    codigo_estudiante: Optional[str] = Query(None, description="Código del estudiante"),
    nombre: Optional[str] = Query(None, description="Nombre del estudiante"),
    plan: Optional[str] = Query(None, description="Tipo de plan (REFRIGERIO/ALMUERZO)"),
    db: Session = Depends(get_db)
):
    """
    Genera un Excel con los registros filtrados aplicando la misma lógica del buscador,
    pero ignorando el límite de paginación para traer todos los resultados.
    """
    
    # 1. Llamamos a la función filtrada con un size gigante para el Excel
    resultado = get_registers_filtered(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        codigo_estudiante=codigo_estudiante,
        nombre=nombre,
        plan=plan,
        page=1,
        size=1000000  # Forzamos a que traiga todos los registros para el reporte
    )

    # Extraemos la lista de la llave 'data'
    registros = resultado.get("data", [])

    if not registros:
        raise HTTPException(
            status_code=404,
            detail="No hay registros para los filtros indicados"
        )

    # 2. Crear Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Registros Filtrados"

    headers = [
        "ID", "Código Estudiante", "Nombre", "Grado", 
        "Tipo Alimentación", "Fecha Hora", "Plan", "Estado"
    ]
    ws.append(headers)

    for row in registros:
        # Formateo de fecha para que sea legible en Excel
        fecha_str = row["fecha_hora"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(row["fecha_hora"], "strftime") else str(row["fecha_hora"])
        
        ws.append([
            row["id"],
            row["codigo_estudiante"],
            row["nombre"],
            row.get("grado", ""),
            row["tipo_alimentacion"],
            fecha_str,
            row["plan"],
            row["estado"]
        ])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # 3. Nombre dinámico del archivo
    nombre_busqueda = (nombre or codigo_estudiante or "reporte").replace(" ", "_")
    filename = f"reporte_{nombre_busqueda}_{date.today()}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get(
    "/excel/all",
    status_code=status.HTTP_200_OK,
    summary="Descargar todos los registros en Excel",
    description="Genera un Excel con TODOS los registros sin aplicar filtros ni paginación"
)
def descargar_excel_all(
    db: Session = Depends(get_db)
):
    # IMPORTANTE: Llamamos a la función pero extrayendo solo la lista 'data'
    # Como queremos TODOS los registros para el Excel, pasamos un tamaño muy grande
    # o mejor aún, modificamos la llamada para que ignore el límite.
    
    try:
        # Opción 1: Si tu función get_all_registers_all permite omitir el límite, úsalo.
        # Opción 2: Pasamos un tamaño gigante (ej. 1000000) para asegurar que traiga todo.
        resultado = get_all_registers_all(db, page=1, size=1000000)
        registros = resultado["data"] # Extraemos la lista de filas

        if not registros:
            raise HTTPException(
                status_code=404,
                detail="No hay registros para exportar"
            )

        # Crear Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Registros"

        headers = [
            "ID", "Código Estudiante", "Nombre", "Grado", 
            "Tipo Alimentación", "Fecha Hora", "Plan", "Estado"
        ]
        ws.append(headers)

        for row in registros:
            # Aseguramos el formato de la fecha para el Excel
            fecha_str = row["fecha_hora"].strftime("%Y-%m-%d %H:%M:%S") if hasattr(row["fecha_hora"], 'strftime') else str(row["fecha_hora"])
            
            ws.append([
                row["id"],
                row["codigo_estudiante"],
                row["nombre"],
                row.get("grado", ""),
                row["tipo_alimentacion"],
                fecha_str,
                row["plan"],
                row["estado"]
            ])

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        filename = f"registros_completos_{date.today()}.xlsx"

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error generando Excel: {e}")
        raise HTTPException(status_code=500, detail="Error al generar el archivo Excel")

@router.get("/total-estudiantes", status_code=status.HTTP_200_OK,
    summary="Obtener todos los estudiantes",
    description="Obtiene todos los estudiantes en la DB")
def obtener_total_estudiantes(db: Session = Depends(get_db)):
    try:
        total = count_all_students(db)
        return {"total_estudiantes": total}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la cantidad total de estudiantes"
        )

@router.get("/total-estudiantes-hoy", status_code=status.HTTP_200_OK,
    summary="Obtiene el desglose de consumos por nivel educativo",
    description="Retorna el conteo de SNACK y LUNCH segmentado por Elementary (1-5) y High School (6-12).")
def obtener_total_estudiantes_hoy(db: Session = Depends(get_db)):
    try:
        # 'conteo' ahora es: 
        # {
        #   "snack": {"elementary": X, "highschool": Y, "total": Z}, 
        #   "lunch": {"elementary": A, "highschool": B, "total": C}, 
        #   "total_estudiantes_hoy": N
        # }
        conteo = count_students_today(db)
        
        return {
            "total_estudiantes_hoy": conteo["total_estudiantes_hoy"],
            "desglose": {
                "snack": conteo["snack"],
                "lunch": conteo["lunch"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error en endpoint total-estudiantes-hoy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la cantidad de estudiantes que consumieron hoy"
        )

@router.get("/total-planes", status_code=status.HTTP_200_OK,
    summary="Obtiene todos los estudiantes con plan alimenticio activo",
    description="Obtiene todos los estudiantes con plan alimenticio activo")
def obtener_totales_planes(db: Session = Depends(get_db)):
    try:
        totales = total_planalimenticio(db)
        return totales
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los totales del dashboard"
        )
    
@router.get("/dashboard/consumo-mes", status_code=200,
    summary="Obtiene todos los estudiantes que han consumido ese mes",
    description="Obtiene todos los estudiantes que han consumido ese mes")
def obtener_consumo_mes(db: Session = Depends(get_db)):
    try:
        total_mes = consumo_mes_actual(db)
        return {"mes": date.today().month, "anio": date.today().year, "total_consumo": total_mes}
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al obtener el consumo del mes actual"
        )
    
@router.get(
    "/estudiantes-con-plan",
    status_code=status.HTTP_200_OK,
    summary="Estudiantes con plan alimenticio",
    description="Lista estudiantes cuyo tipo de alimentación es distinto a NINGUNO"
)
def listar_estudiantes_con_plan(db: Session = Depends(get_db)):
    try:
        data = get_estudiantes_con_plan(db)

        return {
            "total": len(data),
            "data": data
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estudiantes con plan alimenticio"
        )
    
@router.get(
    "/buscar-estudiantes",
    status_code=status.HTTP_200_OK,
    summary="Buscador de estudiantes",
    description="Permite buscar por nombre, código, grado o combinación de ellos"
)
def buscar_estudiantes_endpoint(
    codigo_estudiante: str = Query(None, description="Código del estudiante"),
    nombre: str = Query(None, description="Nombre del estudiante"),
    grado: str = Query(None, description="Grado / grupo"),
    db: Session = Depends(get_db)
):
    if not codigo_estudiante and not nombre and not grado:
        raise HTTPException(
            status_code=400,
            detail="Debe enviar al menos un criterio de búsqueda"
        )

    data = buscar_estudiantes(
        db=db,
        codigo_estudiante=codigo_estudiante,
        nombre=nombre,
        grado=grado
    )

    return {
        "total": len(data),
        "data": data
    }