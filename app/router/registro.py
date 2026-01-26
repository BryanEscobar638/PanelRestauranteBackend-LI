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
    
@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    summary="Obtener estudiantes (máx. 15)",
    description="Devuelve hasta 15 registros de la tabla estudiantes ordenado por los mas recientes"
)
def listar_estudiantes(db: Session = Depends(get_db)):
    try:
        registros = get_all_registers_all(db)
        return {
            "total": len(registros),
            "data": registros
        }
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los estudiantes"
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


@router.get("/filtrar",status_code=status.HTTP_200_OK,
    summary="Buscador con filtros",
    description="Permite buscar por fecha, por codigo de estudiante, o por ambos al mismo tiempo")
def listar_registros_filtrados(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    codigo_estudiante: Optional[str] = Query(None, description="Código del estudiante"),
    db: Session = Depends(get_db)
):
    """
    Filtra registros por rango de fechas, código de estudiante o ambos.
    """
    print("🔥 RUTA /filtrar EJECUTADA 🔥")
    registros = get_registers_filtered(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        codigo_estudiante=codigo_estudiante
    )

    return {
        "total": len(registros),
        "data": registros
    }


@router.get("/excel",status_code=status.HTTP_200_OK,
    summary="Descargar con filtros en un excel",
    description="Permite descargar por fecha, por codigo de estudiante, o por ambos al mismo tiempo")
def descargar_excel(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    codigo_estudiante: Optional[str] = Query(None, description="Código del estudiante"),
    db: Session = Depends(get_db)
):
    """
    Genera un Excel con los registros filtrados opcionalmente por fechas y/o código.
    """
    data = get_registers_filtered(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        codigo_estudiante=codigo_estudiante
    )

    if not data:
        raise HTTPException(
            status_code=404,
            detail="No hay registros para los filtros indicados"
        )

    # Crear Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Registros"

    headers = [
        "ID",
        "Código Estudiante",
        "Nombre",
        "Grado",
        "Tipo Alimentación",
        "Fecha Hora",
        "Plan",
        "Estado"
    ]
    ws.append(headers)

    for row in data:
        ws.append([
            row["id"],
            row["codigo_estudiante"],
            row["nombre"],
            row.get("grado", ""),
            row["tipo_alimentacion"],
            row["fecha_hora"],
            row["plan"],
            row["estado"]
        ])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # Nombre dinámico del archivo
    nombre_codigo = codigo_estudiante or "todos"
    nombre_fecha_inicio = fecha_inicio or "inicio"
    nombre_fecha_fin = fecha_fin or "fin"

    filename = f"registros_{nombre_codigo}_{nombre_fecha_inicio}_a_{nombre_fecha_fin}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get(
    "/excel/all",
    status_code=status.HTTP_200_OK,
    summary="Descargar todos los registros en Excel",
    description="Genera un Excel con TODOS los registros sin aplicar filtros"
)
def descargar_excel_all(
    db: Session = Depends(get_db)
):
    data = get_all_registers_all(db)

    if not data:
        raise HTTPException(
            status_code=404,
            detail="No hay registros para exportar"
        )

    # Crear Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Registros"

    headers = [
        "ID",
        "Código Estudiante",
        "Nombre",
        "Grado",
        "Tipo Alimentación",
        "Fecha Hora",
        "Plan",
        "Estado"
    ]
    ws.append(headers)

    for row in data:
        ws.append([
            row["id"],
            row["codigo_estudiante"],
            row["nombre"],
            row.get("grado", ""),
            row["tipo_alimentacion"],
            row["fecha_hora"],
            row["plan"],
            row["estado"]
        ])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = "registros_completos.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

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
    summary="Obtiene todos los estudiantes que han registrado ese dia alimentacion",
    description="Obtiene todos los estudiantes que han registrado ese dia alimentacion")
def obtener_total_estudiantes_hoy(db: Session = Depends(get_db)):
    try:
        total = count_students_today(db)
        return {"total_estudiantes_hoy": total}
    except Exception:
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