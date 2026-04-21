from datetime import date
from io import BytesIO
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DBAPIError

# Tus funciones ya migradas a Supabase
from app.searchs.registro import (
    buscar_estudiantes, 
    consumo_mes_actual, 
    count_all_students, 
    count_students_today, 
    get_all_registers_all, 
    get_estudiantes_con_plan, 
    total_planalimenticio, 
    get_all_registers, 
    get_registers_filtered, 
    get_registers_today
)
from core.database import get_db

# Configuración de logger para ver errores de Supabase en consola
logger = logging.getLogger(__name__)

router = APIRouter()

# ------------------------------------------------------------------
# Endpoint: Obtener los últimos 15 registros
# ------------------------------------------------------------------
@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Obtener estudiantes (máx. 15)",
    description="Devuelve hasta 15 registros recientes de la tabla registros_validacion desde Supabase"
)
def listar_estudiantes(db: Session = Depends(get_db)):
    try:
        # get_all_registers ya tiene el SELECT con 'public.registros_validacion'
        registros = get_all_registers(db)
        
        return {
            "status": "success",
            "total": len(registros),
            "data": registros
        }
        
    except (SQLAlchemyError, DBAPIError) as e:
        # Logueamos el error real para debuguear (ej: error de SSL o puerto 8432)
        logger.error(f"Error de conexión o consulta en Supabase: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al conectar con el servidor de base de datos de Supabase"
        )
    
# endpoint para conseguir los todos los estudiantes
@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    summary="Obtener estudiantes paginados",
    description="Devuelve una lista paginada de todos los estudiantes registrados desde Supabase."
)
def listar_estudiantes_paginados(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Número de página"), 
    size: int = Query(50, ge=1, le=100, description="Registros por página")
):
    """
    Nota: He añadido 'Query' para que FastAPI valide que la página no sea 
    menor a 1 y el tamaño no sea exagerado (máx 100).
    """
    try:
        # La función get_all_registers_all ya usa el esquema 'public' y el puerto 8432
        resultado = get_all_registers_all(db, page=page, size=size)
        
        return resultado

    except SQLAlchemyError as e:
        # Logueamos el error específico para identificar fallos en el túnel de Supabase
        logger.error(f"Error de base de datos en /all: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los registros paginados del servidor"
        )
    except Exception as e:
        logger.error(f"Error inesperado en /all: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al procesar la solicitud"
        )

@router.get(
    "/hoy",
    status_code=status.HTTP_200_OK,
    summary="Obtener estudiantes registrados en el día actual",
    description="Devuelve todos los registros de validación del día de hoy desde Supabase."
)
def listar_registros_hoy(
    db: Session = Depends(get_db),
    codigo_estudiante: Optional[str] = Query(None, description="Filtrar por código de estudiante")
):
    """
    Obtiene los registros del día. 
    Nota: La función 'get_registers_today' ya está configurada para usar CURRENT_DATE de Postgres.
    """
    try:
        # Llamamos a la función que ya migramos con la sintaxis de PostgreSQL
        registros = get_registers_today(db, codigo_estudiante=codigo_estudiante)
        
        return {
            "status": "success",
            "filtros": {
                "codigo_estudiante": codigo_estudiante if codigo_estudiante else "todos",
                "fecha_consulta": date.today().isoformat() # Formato estándar YYYY-MM-DD
            },
            "total": len(registros),
            "data": registros
        }

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos en /hoy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al conectar con Supabase para obtener los datos de hoy"
        )
    except Exception as e:
        logger.error(f"Error inesperado en /hoy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/filtrar", 
    status_code=status.HTTP_200_OK,
    summary="Buscador con filtros avanzados y paginación",
    description="Permite filtrar por rango de fechas, código, nombre, grado, plan y estado, devolviendo resultados paginados desde Supabase."
)
def listar_registros_filtrados(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    codigo_estudiante: Optional[str] = Query(None, description="Código del estudiante"),
    nombre: Optional[str] = Query(None, description="Nombre del estudiante (búsqueda aproximada)"),
    grado: Optional[str] = Query(None, description="Grado del estudiante (ej: 1, 5, 11)"),
    plan: Optional[str] = Query(None, description="Tipo de plan: REFRIGERIO, ALMUERZO o TODOS"),
    estado: Optional[str] = Query(None, description="Estado del registro: VALIDADO, NO REGISTRADO o TODOS"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(50, ge=1, le=100, description="Registros por página"),
    db: Session = Depends(get_db)
):
    """
    Endpoint que integra filtros y paginación. 
    Nota: Se apoya en 'get_registers_filtered' que ya usa ILIKE para Postgres.
    """
    try:
        # Log de auditoría interna
        logger.info(
            f"🔍 Consulta Supabase: Inicio={fecha_inicio}, Fin={fecha_fin}, "
            f"Estudiante={codigo_estudiante}, Nombre={nombre}, Plan={plan}, Estado={estado}"
        )
        
        # Llamamos al controlador que ya configuramos con la sintaxis de PostgreSQL
        resultado = get_registers_filtered(
            db=db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            codigo_estudiante=codigo_estudiante,
            nombre=nombre,
            grado=grado,
            plan=plan,
            estado=estado,
            page=page,
            size=size
        )

        return resultado

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos en /filtrar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar los filtros en el servidor de base de datos"
        )
    except Exception as e:
        logger.error(f"Error inesperado en /filtrar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al aplicar los filtros"
        )


@router.get(
    "/excel", 
    status_code=status.HTTP_200_OK,
    summary="Descargar con filtros en un excel",
    description="Genera un archivo Excel con un nombre dinámico basado en los filtros aplicados sobre los datos en Supabase."
)
def descargar_excel(
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    codigo_estudiante: Optional[str] = Query(None, description="Código del estudiante"),
    nombre: Optional[str] = Query(None, description="Nombre del estudiante"),
    grado: Optional[str] = Query(None, description="Grado del estudiante"),
    plan: Optional[str] = Query(None, description="Tipo de plan (REFRIGERIO/ALMUERZO)"),
    estado: Optional[str] = Query(None, description="Estado del registro (VALIDADO/NO REGISTRADO)"),
    db: Session = Depends(get_db)
):
    try:
        # 1. Obtener datos (get_registers_filtered ya usa la sintaxis de Supabase)
        resultado = get_registers_filtered(
            db=db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            codigo_estudiante=codigo_estudiante,
            nombre=nombre,
            grado=grado,
            plan=plan,
            estado=estado,
            page=1,
            size=1000000 # Límite alto para exportación total
        )

        registros = resultado.get("data", [])
        if not registros:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="No hay registros para los filtros indicados en Supabase"
            )

        # 2. Crear Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Registros Filtrados"
        
        # Encabezados
        ws.append(["ID", "Código Estudiante", "Nombre", "Grado", "Tipo Alimentación", "Fecha Hora", "Plan", "Estado"])

        for row in registros:
            # Manejo robusto de fechas para PostgreSQL
            fecha_hora = row.get("fecha_hora")
            if hasattr(fecha_hora, "strftime"):
                # Si viene de Supabase con zona horaria, esto lo maneja correctamente
                fecha_str = fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
            else:
                fecha_str = str(fecha_hora)

            ws.append([
                row.get("id"), 
                row.get("codigo_estudiante"), 
                row.get("nombre"), 
                row.get("grado", ""), 
                row.get("tipo_alimentacion"), 
                fecha_str, 
                row.get("plan"), 
                row.get("estado")
            ])

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        # 3. LÓGICA DE NOMBRE DINÁMICO
        partes_nombre = ["Reporte"]
        
        if nombre:
            partes_nombre.append(nombre.replace(" ", "_").strip())
        elif codigo_estudiante:
            partes_nombre.append(str(codigo_estudiante))
        
        if grado:
            partes_nombre.append(f"G{grado}")
        
        if plan and plan.upper() != "TODOS":
            partes_nombre.append(plan.capitalize())
            
        if estado and estado.upper() != "TODOS":
            partes_nombre.append(estado.capitalize())

        if fecha_inicio and fecha_fin:
            if fecha_inicio == fecha_fin:
                partes_nombre.append(str(fecha_inicio))
            else:
                partes_nombre.append(f"{fecha_inicio}_al_{fecha_fin}")
        else:
            partes_nombre.append("Historico")

        filename_final = "_".join(partes_nombre) + ".xlsx"

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename_final}"}
        )

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos al exportar Excel: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al extraer datos de Supabase para el reporte")
    except Exception as e:
        logger.error(f"Error inesperado al generar Excel: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al generar el archivo Excel")

@router.get(
    "/excel/all",
    status_code=status.HTTP_200_OK,
    summary="Descargar todos los registros en Excel",
    description="Genera un Excel con todos los registros históricos almacenados en Supabase sin filtros."
)
def descargar_excel_all(
    db: Session = Depends(get_db)
):
    """
    Exportación masiva de datos desde Supabase a Excel.
    """
    try:
        # Usamos la función que ya migramos para Supabase con un límite alto.
        # get_all_registers_all ya usa el esquema 'public' y el puerto 8432.
        resultado = get_all_registers_all(db, page=1, size=1000000)
        registros = resultado.get("data", [])

        if not registros:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron registros en Supabase para exportar"
            )

        # 1. Crear el libro de Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Histórico Completo"

        # 2. Definir y añadir encabezados
        headers = [
            "ID", "Código Estudiante", "Nombre", "Grado", 
            "Tipo Alimentación", "Fecha Hora", "Plan", "Estado"
        ]
        ws.append(headers)

        # 3. Iterar sobre los registros de Supabase
        for row in registros:
            # Manejo de fecha: Postgres devuelve objetos datetime. 
            # Verificamos si tiene el método strftime para evitar errores.
            fecha_hora = row.get("fecha_hora")
            if hasattr(fecha_hora, "strftime"):
                fecha_str = fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
            else:
                fecha_str = str(fecha_hora) if fecha_hora else ""
            
            # Usamos row.get() para evitar KeyErrors si alguna columna es NULL en la BD
            ws.append([
                row.get("id"),
                row.get("codigo_estudiante"),
                row.get("nombre"),
                row.get("grado", ""),
                row.get("tipo_alimentacion"),
                fecha_str,
                row.get("plan"),
                row.get("estado")
            ])

        # 4. Preparar el buffer de memoria
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        # Nombre del archivo con la fecha de hoy
        filename = f"reporte_historico_cafeteria_{date.today()}.xlsx"

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos en Excel ALL (Supabase): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error de conexión con el servidor de base de datos"
        )
    except Exception as e:
        logger.error(f"Error inesperado al generar Excel histórico: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error interno al procesar el archivo Excel"
        )

@router.get(
    "/total-estudiantes-hoy", 
    status_code=status.HTTP_200_OK,
    summary="Obtiene el desglose de consumos por nivel educativo",
    description="Retorna el conteo de SNACK y LUNCH segmentado por Elementary (1-5) y High School (6-12) desde Supabase."
)
def obtener_total_estudiantes_hoy(db: Session = Depends(get_db)):
    """
    Este endpoint consume la lógica de agregación de PostgreSQL.
    Ideal para mostrar en los indicadores (cards) principales del dashboard.
    """
    try:
        # La función count_students_today ya maneja el esquema 'public' 
        # y la conversión de grados (::INTEGER) para Postgres.
        conteo = count_students_today(db)
        
        # Estructuramos la respuesta asegurando tipos enteros
        return {
            "status": "success",
            "total_estudiantes_hoy": int(conteo.get("total_estudiantes_hoy", 0)),
            "desglose": {
                "snack": {
                    "elementary": int(conteo["snack"].get("elementary", 0)),
                    "highschool": int(conteo["snack"].get("highschool", 0)),
                    "total": int(conteo["snack"].get("total", 0))
                },
                "lunch": {
                    "elementary": int(conteo["lunch"].get("elementary", 0)),
                    "highschool": int(conteo["lunch"].get("highschool", 0)),
                    "total": int(conteo["lunch"].get("total", 0))
                }
            }
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos en totales hoy (Supabase): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al conectar con el servidor de datos para obtener consumos"
        )
    except Exception as e:
        logger.error(f"Error inesperado en totales hoy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar las estadísticas de hoy"
        )

@router.get(
    "/total-planes", 
    status_code=status.HTTP_200_OK,
    summary="Obtiene los totales globales del plan alimenticio",
    description="Retorna el total de estudiantes inscritos, cuántos han consumido hoy y el desglose por tipo de plan (SNACK, LUNCH, etc.) desde Supabase."
)
def obtener_totales_planes(db: Session = Depends(get_db)):
    """
    Este endpoint es el corazón del Dashboard principal.
    Consume 'total_planalimenticio' que ya fue migrado al esquema 'public'.
    """
    try:
        # La función total_planalimenticio ya está optimizada para 
        # manejar los conteos y grupos en PostgreSQL.
        totales = total_planalimenticio(db)
        
        # Estructuramos la respuesta para asegurar que sea JSON puro
        return {
            "status": "success",
            "data": {
                "total_estudiantes": int(totales.get("total_estudiantes", 0)),
                "total_consumieron_hoy": int(totales.get("total_consumieron_hoy", 0)),
                "total_por_tipo": totales.get("total_por_tipo", [])
            }
        }

    except SQLAlchemyError as e:
        # Logueamos el error técnico para soporte interno
        logger.error(f"Error de base de datos en dashboard (Supabase): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al conectar con el servidor de Supabase para obtener estadísticas"
        )
    except Exception as e:
        logger.error(f"Error inesperado en totales dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al procesar los totales"
        )
    
@router.get(
    "/dashboard/consumo-mes", 
    status_code=status.HTTP_200_OK,
    summary="Obtiene el total de estudiantes que han consumido este mes",
    description="Calcula el conteo de estudiantes únicos que tienen registros en el mes y año actuales desde Supabase."
)
def obtener_consumo_mes(db: Session = Depends(get_db)):
    """
    Endpoint para KPIs mensuales. 
    Usa la lógica de PostgreSQL para filtrar por el mes en curso.
    """
    try:
        hoy = date.today()
        # La función consumo_mes_actual ya maneja los esquemas 'public' 
        # y la sintaxis EXTRACT de Postgres.
        total_mes = consumo_mes_actual(db)
        
        return {
            "status": "success",
            "periodo": {
                "mes": hoy.month,
                "anio": hoy.year,
                "nombre_mes": hoy.strftime("%B") # Opcional: devuelve el nombre del mes
            },
            "total_consumo": int(total_mes)
        }

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos en consumo-mes (Supabase): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al conectar con Supabase para obtener estadísticas mensuales"
        )
    except Exception as e:
        logger.error(f"Error inesperado en consumo-mes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al calcular el consumo del mes"
        )
    
@router.get(
    "/estudiantes-con-plan",
    status_code=status.HTTP_200_OK,
    summary="Estudiantes con plan alimenticio",
    description="Lista a todos los estudiantes registrados en Supabase cuyo tipo de alimentación es distinto a 'NINGUNO'."
)
def listar_estudiantes_con_plan(db: Session = Depends(get_db)):
    """
    Este endpoint es útil para obtener la lista base de beneficiarios.
    La función 'get_estudiantes_con_plan' ya utiliza el esquema 'public' y ordena por nombre.
    """
    try:
        # Llamamos a la función del controlador que ya migramos
        data = get_estudiantes_con_plan(db)

        return {
            "status": "success",
            "total": len(data),
            "data": data
        }

    except SQLAlchemyError as e:
        # Registramos el error de base de datos (Postgres/Supabase)
        logger.error(f"Error de base de datos en estudiantes-con-plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al conectar con Supabase para obtener los estudiantes"
        )
    except Exception as e:
        # Error genérico de Python
        logger.error(f"Error inesperado en estudiantes-con-plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al procesar la lista de estudiantes"
        )
    
@router.get(
    "/buscar-estudiantes",
    status_code=status.HTTP_200_OK,
    summary="Buscador de estudiantes",
    description="Permite buscar estudiantes en Supabase por nombre, código, grado o combinación de ellos."
)
def buscar_estudiantes_endpoint(
    codigo_estudiante: Optional[str] = Query(None, description="Código del estudiante"),
    nombre: Optional[str] = Query(None, description="Nombre del estudiante"),
    grado: Optional[str] = Query(None, description="Grado / grupo"),
    db: Session = Depends(get_db)
):
    """
    Endpoint de búsqueda flexible.
    Nota: La función 'buscar_estudiantes' ya utiliza ILIKE para que no importe 
    si escribes en mayúsculas o minúsculas en Supabase.
    """
    # Validamos que no intenten buscar en blanco
    if not any([codigo_estudiante, nombre, grado]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar al menos un criterio de búsqueda (código, nombre o grado)"
        )

    try:
        # Llamamos al controlador que ya configuramos con la sintaxis de PostgreSQL
        data = buscar_estudiantes(
            db=db,
            codigo_estudiante=codigo_estudiante,
            nombre=nombre,
            grado=grado
        )

        return {
            "status": "success",
            "filtros_aplicados": {
                "codigo": codigo_estudiante,
                "nombre": nombre,
                "grado": grado
            },
            "total": len(data),
            "data": data
        }

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos en buscar-estudiantes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al conectar con el motor de búsqueda de Supabase"
        )
    except Exception as e:
        logger.error(f"Error inesperado en buscar-estudiantes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al realizar la búsqueda"
        )