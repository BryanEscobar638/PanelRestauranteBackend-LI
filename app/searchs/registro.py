from datetime import date, datetime
from fastapi import FastAPI
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from pytz import timezone

from core.database import SessionLocal

logger = logging.getLogger(__name__)

app = FastAPI()

# 1️⃣ Todos los registros recientes (LIMIT 15)
def get_all_registers(db: Session):
    try:
        query = text("""
            SELECT
                rv.id,
                rv.codigo_estudiante,
                e.nombre,
                e.grado,
                e.tipo_alimentacion,
                rv.fecha_hora,
                rv.plan,
                rv.estado
            FROM cafeteria.registros_validacion rv
            INNER JOIN cafeteria.estudiantes e
                ON rv.codigo_estudiante = e.codigo_estudiante
            ORDER BY rv.fecha_hora DESC
            LIMIT 15;
        """)
        return db.execute(query).mappings().all()
    except SQLAlchemyError as e:
        logger.error(f"Error al obtener registros de estudiantes: {e}")
        raise

def get_all_registers_all(db: Session, page: int = 1, size: int = 50):
    try:
        # 1. Calcular el salto (offset)
        skip = (page - 1) * size

        # 2. Consulta para contar el total de registros (sin paginar)
        count_query = text("""
            SELECT COUNT(*) 
            FROM cafeteria.registros_validacion rv
            INNER JOIN cafeteria.estudiantes e 
                ON rv.codigo_estudiante = e.codigo_estudiante
        """)
        total_registros = db.execute(count_query).scalar()

        # 3. Consulta principal con LIMIT y OFFSET
        query = text("""
            SELECT
                rv.id,
                rv.codigo_estudiante,
                e.nombre,
                e.grado,
                e.tipo_alimentacion,
                rv.fecha_hora,
                rv.plan,
                rv.estado
            FROM cafeteria.registros_validacion rv
            INNER JOIN cafeteria.estudiantes e
                ON rv.codigo_estudiante = e.codigo_estudiante
            ORDER BY rv.fecha_hora DESC
            LIMIT :limit OFFSET :offset
        """)

        result = db.execute(query, {"limit": size, "offset": skip}).mappings().all()

        # 4. Retornar estructura completa
        return {
            "total": total_registros,
            "page": page,
            "size": size,
            "data": result
        }

    except SQLAlchemyError as e:
        logger.error(f"Error al obtener registros de estudiantes: {e}")
        raise

# 2️⃣ Filtrar por fechas, código o ambos
def get_registers_filtered(
    db: Session,
    fecha_inicio: date = None,
    fecha_fin: date = None,
    codigo_estudiante: str = None,
    nombre: str = None,
    grado: str = None,
    plan: str = None,
    estado: str = None,  # Nuevo parámetro añadido
    page: int = 1,
    size: int = 50
):
    try:
        skip = (page - 1) * size

        base_query = """
            FROM cafeteria.registros_validacion rv
            INNER JOIN cafeteria.estudiantes e
                ON rv.codigo_estudiante = e.codigo_estudiante
        """

        conditions = []
        params = {}

        # 1. Filtrar por fecha
        if fecha_inicio and fecha_fin:
            conditions.append("DATE(rv.fecha_hora) BETWEEN :fecha_inicio AND :fecha_fin")
            params["fecha_inicio"] = fecha_inicio
            params["fecha_fin"] = fecha_fin

        # 2. Filtrar por código
        if codigo_estudiante:
            conditions.append("rv.codigo_estudiante LIKE :codigo_estudiante")
            params["codigo_estudiante"] = f"%{codigo_estudiante}%"

        # 3. Filtrar por nombre
        if nombre:
            conditions.append("e.nombre COLLATE utf8mb4_general_ci LIKE :nombre")
            params["nombre"] = f"%{nombre}%"

        # 4. Filtrar por grado
        if grado:
            conditions.append("e.grado = :grado")
            params["grado"] = grado

        # 5. Filtrar por Plan
        if plan and plan.upper() != "TODOS":
            conditions.append("rv.plan = :plan")
            params["plan"] = plan.upper()

        # 6. NUEVO: Filtrar por Estado (Validado o No Registrado)
        if estado and estado.upper() != "TODOS":
            conditions.append("rv.estado = :estado")
            params["estado"] = estado.upper()

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        # --- 1. OBTENER EL TOTAL DE REGISTROS FILTRADOS ---
        count_sql = f"SELECT COUNT(*) {base_query} {where_clause}"
        total_registros = db.execute(text(count_sql), params).scalar()

        # --- 2. OBTENER LOS DATOS PAGINADOS ---
        select_sql = f"""
            SELECT
                rv.id,
                rv.codigo_estudiante,
                e.nombre,
                e.grado,
                e.tipo_alimentacion,
                rv.fecha_hora,
                rv.plan,
                rv.estado
            {base_query}
            {where_clause}
            ORDER BY rv.fecha_hora DESC
            LIMIT :limit OFFSET :offset
        """
        
        params["limit"] = size
        params["offset"] = skip

        result = db.execute(text(select_sql), params).mappings().all()

        return {
            "total": total_registros,
            "page": page,
            "size": size,
            "data": result
        }

    except Exception as e:
        logger.error(f"Error al filtrar registros: {e}")
        raise

# 3️⃣ Registros del día
def get_registers_today(db: Session, codigo_estudiante: str = None):
    try:
        query = """
            SELECT
                rv.id,
                rv.codigo_estudiante,
                e.nombre,
                e.grado,
                e.tipo_alimentacion,
                rv.fecha_hora,
                rv.plan,
                rv.estado
            FROM cafeteria.registros_validacion rv
            INNER JOIN cafeteria.estudiantes e
                ON rv.codigo_estudiante = e.codigo_estudiante
            WHERE rv.fecha = CURDATE()
        """

        params = {}
        if codigo_estudiante:
            query += " AND rv.codigo_estudiante = :codigo_estudiante"
            params["codigo_estudiante"] = codigo_estudiante

        query += " ORDER BY rv.fecha_hora DESC"

        return db.execute(text(query), params).mappings().all()
    except Exception as e:
        logger.error(f"Error al obtener registros del día: {e}")
        raise

def count_all_students(db: Session) -> int:
    try:
        query = text("""
            SELECT COUNT(*) AS total
            FROM cafeteria.estudiantes
        """)
        result = db.execute(query).scalar()  # scalar() devuelve directamente el valor del COUNT(*)
        return result or 0
    except Exception as e:
        logger.error(f"Error al contar estudiantes: {e}")
        raise

def count_students_today(db: Session):
    try:
        query = text("""
            SELECT 
                -- Conteos para SNACK (Solo validados)
                SUM(CASE WHEN rv.plan = 'SNACK' AND CAST(e.grado AS UNSIGNED) BETWEEN 1 AND 5 THEN 1 ELSE 0 END) AS snack_elementary,
                SUM(CASE WHEN rv.plan = 'SNACK' AND CAST(e.grado AS UNSIGNED) BETWEEN 6 AND 12 THEN 1 ELSE 0 END) AS snack_highschool,
                
                -- Conteos para LUNCH (Solo validados)
                SUM(CASE WHEN rv.plan = 'LUNCH' AND CAST(e.grado AS UNSIGNED) BETWEEN 1 AND 5 THEN 1 ELSE 0 END) AS lunch_elementary,
                SUM(CASE WHEN rv.plan = 'LUNCH' AND CAST(e.grado AS UNSIGNED) BETWEEN 6 AND 12 THEN 1 ELSE 0 END) AS lunch_highschool,
                
                -- Totales generales (Solo validados)
                SUM(CASE WHEN rv.plan = 'SNACK' THEN 1 ELSE 0 END) AS total_snack,
                SUM(CASE WHEN rv.plan = 'LUNCH' THEN 1 ELSE 0 END) AS total_lunch,
                COUNT(DISTINCT rv.codigo_estudiante) AS total_unicos
            FROM cafeteria.registros_validacion rv
            INNER JOIN cafeteria.estudiantes e ON rv.codigo_estudiante = e.codigo_estudiante
            WHERE rv.fecha = CURDATE()
            AND rv.estado = 'VALIDADO' -- <--- Filtro crítico agregado
        """)
        
        result = db.execute(query).mappings().first()
        
        return {
            "snack": {
                "elementary": result["snack_elementary"] or 0,
                "highschool": result["snack_highschool"] or 0,
                "total": result["total_snack"] or 0
            },
            "lunch": {
                "elementary": result["lunch_elementary"] or 0,
                "highschool": result["lunch_highschool"] or 0,
                "total": result["total_lunch"] or 0
            },
            "total_estudiantes_hoy": result["total_unicos"] or 0
        }
    except Exception as e:
        logger.error(f"Error al contar consumos segmentados: {e}")
        raise

def total_planalimenticio(db: Session):
    try:
        # 1️⃣ Total de estudiantes con tipo de alimentación ≠ "NINGUNO"
        total_estudiantes_query = text("""
            SELECT COUNT(*) AS total
            FROM cafeteria.estudiantes
            WHERE tipo_alimentacion != 'NINGUNO'
        """)
        total_estudiantes = db.execute(total_estudiantes_query).scalar() or 0

        # 2️⃣ Total de estudiantes que consumieron hoy con tipo de alimentación ≠ "NINGUNO"
        total_consumieron_hoy_query = text("""
            SELECT COUNT(DISTINCT rv.codigo_estudiante) AS total
            FROM cafeteria.registros_validacion rv
            INNER JOIN cafeteria.estudiantes e
                ON rv.codigo_estudiante = e.codigo_estudiante
            WHERE DATE(rv.fecha_hora) = :hoy
            AND e.tipo_alimentacion != 'NINGUNO'
        """)
        total_consumieron_hoy = db.execute(
            total_consumieron_hoy_query, 
            {"hoy": date.today()}
        ).scalar() or 0

        # 3️⃣ Total por tipo de alimentación distinto a "NINGUNO"
        por_tipo_query = text("""
            SELECT e.tipo_alimentacion, COUNT(*) AS total
            FROM cafeteria.estudiantes e
            WHERE e.tipo_alimentacion != 'NINGUNO'
            GROUP BY e.tipo_alimentacion
        """)
        por_tipo = db.execute(por_tipo_query).mappings().all()

        return {
            "total_estudiantes": total_estudiantes,
            "total_consumieron_hoy": total_consumieron_hoy,
            "total_por_tipo": por_tipo
        }

    except Exception as e:
        logger.error(f"Error al calcular totales del dashboard: {e}")
        raise

def consumo_mes_actual(db: Session):
    try:
        # Obtener mes y año actuales
        hoy = date.today()
        mes_actual = hoy.month
        anio_actual = hoy.year

        query = text("""
            SELECT COUNT(DISTINCT rv.codigo_estudiante) AS total_consumo
            FROM cafeteria.registros_validacion rv
            INNER JOIN cafeteria.estudiantes e
                ON rv.codigo_estudiante = e.codigo_estudiante
            WHERE MONTH(rv.fecha_hora) = :mes
            AND YEAR(rv.fecha_hora) = :anio
        """)

        total = db.execute(query, {"mes": mes_actual, "anio": anio_actual}).scalar() or 0
        return total

    except Exception as e:
        logger.error(f"Error al calcular consumo del mes actual: {e}")
        raise

def get_estudiantes_con_plan(db: Session):
    """
    Obtiene estudiantes con tipo de alimentación distinto a 'NINGUNO'
    sin repetir por código de estudiante.
    """
    try:
        query = text("""
            SELECT DISTINCT
                e.codigo_estudiante,
                e.nombre,
                e.grado,
                e.tipo_alimentacion
            FROM cafeteria.estudiantes e
            WHERE e.tipo_alimentacion != 'NINGUNO'
            ORDER BY e.nombre
        """)

        result = db.execute(query).mappings().all()
        return result

    except Exception as e:
        logger.error(f"Error al obtener estudiantes con plan: {e}")
        raise

def buscar_estudiantes(
    db: Session, 
    codigo_estudiante: str = None, 
    nombre: str = None, 
    grado: str = None
):
    try:
        base_query = """
            SELECT DISTINCT
                e.codigo_estudiante,
                e.nombre,
                e.grado,
                e.tipo_alimentacion
            FROM cafeteria.estudiantes e
            WHERE e.tipo_alimentacion != 'NINGUNO'
        """

        conditions = []
        params = {}

        if codigo_estudiante:
            conditions.append("e.codigo_estudiante LIKE :codigo")
            params["codigo"] = f"%{codigo_estudiante}%"

        if nombre:
            # Usamos COLLATE utf8mb4_general_ci para ignorar tildes y mayúsculas
            conditions.append("e.nombre COLLATE utf8mb4_general_ci LIKE :nombre")
            params["nombre"] = f"%{nombre}%"

        if grado:
            conditions.append("e.grado = :grado")
            params["grado"] = grado

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        base_query += " ORDER BY e.nombre"

        result = db.execute(text(base_query), params).mappings().all()
        return result

    except Exception as e:
        logger.error(f"Error en buscador de estudiantes: {e}")
        raise

