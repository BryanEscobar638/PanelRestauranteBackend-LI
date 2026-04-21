from datetime import date, datetime
from fastapi import FastAPI
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

from core.database import SessionLocal

logger = logging.getLogger(__name__)

app = FastAPI()

# 1️⃣ Todos los registros recientes (LIMIT 15)
def get_all_registers(db: Session):
    try:
        # ⚠️ Cambié 'cafeteria.' por 'public.' que es el estándar de Supabase
        # Si tus tablas no tienen esquema, puedes quitar 'public.' y dejar solo los nombres
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
            FROM public.registros_validacion_caf rv
            INNER JOIN public.estudiantes_caf e
                ON rv.codigo_estudiante = e.codigo_estudiante
            ORDER BY rv.fecha_hora DESC
            LIMIT 15;
        """)
        
        result = db.execute(query)
        return result.mappings().all()
        
    except SQLAlchemyError as e:
        # Importante: Supabase puede cerrar conexiones inactivas. 
        # El log nos dirá si es un problema de permisos o de conexión.
        logger.error(f"Error en Supabase al obtener registros: {str(e)}")
        raise

def get_all_registers_all(db: Session, page: int = 1, size: int = 50):
    try:
        # 1. Calcular el salto (offset)
        skip = (page - 1) * size

        # 2. Consulta para contar el total de registros (sin paginar)
        # Cambiamos 'cafeteria.' por 'public.'
        count_query = text("""
            SELECT COUNT(*) 
            FROM public.registros_validacion_caf rv
            INNER JOIN public.estudiantes_caf e 
                ON rv.codigo_estudiante = e.codigo_estudiante
        """)
        total_registros = db.execute(count_query).scalar()

        # 3. Consulta principal con LIMIT y OFFSET
        # Usamos los nombres de tablas de Supabase
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
            FROM public.registros_validacion_caf rv
            INNER JOIN public.estudiantes_caf e
                ON rv.codigo_estudiante = e.codigo_estudiante
            ORDER BY rv.fecha_hora DESC
            LIMIT :limit OFFSET :offset
        """)

        # Ejecución con parámetros nombrados (muy seguro contra inyecciones)
        result = db.execute(query, {"limit": size, "offset": skip}).mappings().all()

        # 4. Retornar estructura completa
        return {
            "total": total_registros,
            "page": page,
            "size": size,
            "data": result
        }

    except SQLAlchemyError as e:
        # Log específico para identificar si el error es de permisos en Supabase
        logger.error(f"Error en paginación de Supabase: {str(e)}")
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
    estado: str = None,
    page: int = 1,
    size: int = 50
):
    try:
        skip = (page - 1) * size

        # Cambiamos 'cafeteria.' por 'public.'
        base_query = """
            FROM public.registros_validacion_caf rv
            INNER JOIN public.estudiantes_caf e
                ON rv.codigo_estudiante = e.codigo_estudiante
        """

        conditions = []
        params = {}

        # 1. Filtrar por fecha (Postgres usa DATE() igual que MySQL)
        if fecha_inicio and fecha_fin:
            conditions.append("DATE(rv.fecha_hora) BETWEEN :fecha_inicio AND :fecha_fin")
            params["fecha_inicio"] = fecha_inicio
            params["fecha_fin"] = fecha_fin

        # 2. Filtrar por código (ILIKE para ignorar case en Postgres)
        if codigo_estudiante:
            conditions.append("rv.codigo_estudiante ILIKE :codigo_estudiante")
            params["codigo_estudiante"] = f"%{codigo_estudiante}%"

        # 3. Filtrar por nombre
        # 🟢 CAMBIO CLAVE: Quitamos COLLATE y usamos ILIKE
        if nombre:
            conditions.append("e.nombre ILIKE :nombre")
            params["nombre"] = f"%{nombre}%"

        # 4. Filtrar por grado
        if grado:
            conditions.append("e.grado = :grado")
            params["grado"] = grado

        # 5. Filtrar por Plan
        if plan and plan.upper() != "TODOS":
            conditions.append("rv.plan = :plan")
            params["plan"] = plan

        # 6. Filtrar por Estado
        if estado and estado.upper() != "TODOS":
            conditions.append("rv.estado = :estado")
            params["estado"] = estado

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        # --- 1. OBTENER EL TOTAL ---
        count_sql = f"SELECT COUNT(*) {base_query} {where_clause}"
        total_registros = db.execute(text(count_sql), params).scalar()

        # --- 2. OBTENER LOS DATOS ---
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
        logger.error(f"Error al filtrar registros en Supabase: {e}")
        raise

# 3️⃣ Registros del día
def get_registers_today(db: Session, codigo_estudiante: str = None):
    try:
        # Cambiamos 'cafeteria.' por 'public.' 
        # y 'CURDATE()' por 'CURRENT_DATE'
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
            FROM public.registros_validacion_caf rv
            INNER JOIN public.estudiantes_caf e
                ON rv.codigo_estudiante = e.codigo_estudiante
            WHERE rv.fecha = CURRENT_DATE
        """

        params = {}
        if codigo_estudiante:
            query += " AND rv.codigo_estudiante = :codigo_estudiante"
            params["codigo_estudiante"] = codigo_estudiante

        query += " ORDER BY rv.fecha_hora DESC"

        return db.execute(text(query), params).mappings().all()
    except Exception as e:
        logger.error(f"Error al obtener registros del día en Supabase: {e}")
        raise

def count_all_students(db: Session) -> int:
    try:
        # Cambiamos 'cafeteria.' por 'public.' o lo eliminamos
        query = text("""
            SELECT COUNT(*)
            FROM public.estudiantes_caf
        """)
        # scalar() es perfecto aquí para obtener el número directamente
        result = db.execute(query).scalar()
        return result if result is not None else 0
    except Exception as e:
        logger.error(f"Error al contar estudiantes en Supabase: {e}")
        raise

def count_students_today(db: Session):
    try:
        query = text("""
            SELECT 
                -- Conteos para SNACK
                SUM(CASE WHEN rv.plan = 'SNACK' AND e.grado ~ '^[0-9]+$' AND (e.grado::INTEGER) BETWEEN 1 AND 5 THEN 1 ELSE 0 END) AS snack_elementary,
                SUM(CASE WHEN rv.plan = 'SNACK' AND e.grado ~ '^[0-9]+$' AND (e.grado::INTEGER) BETWEEN 6 AND 12 THEN 1 ELSE 0 END) AS snack_highschool,
                
                -- Conteos para LUNCH
                SUM(CASE WHEN rv.plan = 'LUNCH' AND e.grado ~ '^[0-9]+$' AND (e.grado::INTEGER) BETWEEN 1 AND 5 THEN 1 ELSE 0 END) AS lunch_elementary,
                SUM(CASE WHEN rv.plan = 'LUNCH' AND e.grado ~ '^[0-9]+$' AND (e.grado::INTEGER) BETWEEN 6 AND 12 THEN 1 ELSE 0 END) AS lunch_highschool,
                
                -- Totales generales
                SUM(CASE WHEN rv.plan = 'SNACK' THEN 1 ELSE 0 END) AS total_snack,
                SUM(CASE WHEN rv.plan = 'LUNCH' THEN 1 ELSE 0 END) AS total_lunch,
                COUNT(DISTINCT rv.codigo_estudiante) AS total_unicos
            FROM public.registros_validacion_caf rv
            INNER JOIN public.estudiantes_caf e ON rv.codigo_estudiante = e.codigo_estudiante
            WHERE rv.fecha = CURRENT_DATE
            AND rv.estado = 'VALIDADO'
        """)
        
        result = db.execute(query).mappings().first()
        
        return {
            "snack": {
                "elementary": int(result["snack_elementary"] or 0),
                "highschool": int(result["snack_highschool"] or 0),
                "total": int(result["total_snack"] or 0)
            },
            "lunch": {
                "elementary": int(result["lunch_elementary"] or 0),
                "highschool": int(result["lunch_highschool"] or 0),
                "total": int(result["total_lunch"] or 0)
            },
            "total_estudiantes_hoy": int(result["total_unicos"] or 0)
        }
    except Exception as e:
        logger.error(f"Error al contar consumos segmentados en Supabase: {e}")
        raise


def total_planalimenticio(db: Session):
    try:
        # 1️⃣ Total de estudiantes con tipo de alimentación ≠ 'NINGUNO'
        # Usamos public.estudiantes_caf
        total_estudiantes_query = text("""
            SELECT COUNT(*) 
            FROM public.estudiantes_caf
            WHERE tipo_alimentacion IS NOT NULL 
              AND tipo_alimentacion != 'NINGUNO'
        """)
        total_estudiantes = db.execute(total_estudiantes_query).scalar() or 0

        # 2️⃣ Total que consumieron hoy (Ajustado a la zona horaria de Colombia)
        # Usamos la columna 'fecha' que ya tienes como DATE en tu esquema para mayor velocidad
        total_consumieron_hoy_query = text("""
            SELECT COUNT(DISTINCT rv.codigo_estudiante)
            FROM public.registros_validacion_caf rv
            INNER JOIN public.estudiantes_caf e
                ON rv.codigo_estudiante = e.codigo_estudiante
            WHERE rv.fecha = CURRENT_DATE
              AND e.tipo_alimentacion != 'NINGUNO'
              AND rv.estado = 'VALIDADO'
        """)
        total_consumieron_hoy = db.execute(total_consumieron_hoy_query).scalar() or 0

        # 3️⃣ Total por tipo de alimentación (Agrupado)
        por_tipo_query = text("""
            SELECT tipo_alimentacion, COUNT(*) AS total
            FROM public.estudiantes_caf
            WHERE tipo_alimentacion IS NOT NULL 
              AND tipo_alimentacion != 'NINGUNO'
            GROUP BY tipo_alimentacion
        """)
        result_tipo = db.execute(por_tipo_query).mappings().all()
        # Convertimos a lista de dicts para asegurar la serialización JSON
        por_tipo = [dict(row) for row in result_tipo]

        return {
            "total_estudiantes": total_estudiantes,
            "total_consumieron_hoy": total_consumieron_hoy,
            "total_por_tipo": por_tipo
        }

    except Exception as e:
        logger.error(f"❌ Error al calcular totales del dashboard en Supabase: {e}")
        raise

def consumo_mes_actual(db: Session):
    try:
        # Obtener mes y año actuales
        hoy = date.today()
        mes_actual = hoy.month
        anio_actual = hoy.year

        # 1️⃣ Cambiamos el esquema a public
        # 2️⃣ Usamos EXTRACT para obtener mes y año en PostgreSQL
        query = text("""
            SELECT COUNT(DISTINCT rv.codigo_estudiante)
            FROM public.registros_validacion_caf rv
            INNER JOIN public.estudiantes_caf e
                ON rv.codigo_estudiante = e.codigo_estudiante
            WHERE EXTRACT(MONTH FROM rv.fecha_hora) = :mes
            AND EXTRACT(YEAR FROM rv.fecha_hora) = :anio
        """)

        total = db.execute(query, {"mes": mes_actual, "anio": anio_actual}).scalar() or 0
        return int(total)

    except Exception as e:
        logger.error(f"Error al calcular consumo del mes actual en Supabase: {e}")
        raise

def get_estudiantes_con_plan(db: Session):
    """
    Obtiene estudiantes con tipo de alimentación distinto a 'NINGUNO'
    sin repetir por código de estudiante de forma alfabética.
    """
    try:
        # 1️⃣ Cambiamos el esquema de 'cafeteria.' a 'public.'
        # 2️⃣ DISTINCT funciona igual, pero Postgres es más rápido si 
        #    la columna codigo_estudiante tiene un índice.
        query = text("""
            SELECT DISTINCT
                e.codigo_estudiante,
                e.nombre,
                e.grado,
                e.tipo_alimentacion
            FROM public.estudiantes_caf e
            WHERE e.tipo_alimentacion != 'NINGUNO'
            ORDER BY e.nombre ASC
        """)

        result = db.execute(query).mappings().all()
        
        # Opcional: Convertir a lista de diccionarios para asegurar 
        # compatibilidad total con el JSON de FastAPI
        return [dict(row) for row in result]

    except Exception as e:
        logger.error(f"Error al obtener estudiantes con plan en Supabase: {e}")
        raise

def buscar_estudiantes(
    db: Session, 
    codigo_estudiante: str = None, 
    nombre: str = None, 
    grado: str = None
):
    try:
        # 1️⃣ Cambiamos el esquema a 'public.'
        base_query = """
            SELECT DISTINCT
                e.codigo_estudiante,
                e.nombre,
                e.grado,
                e.tipo_alimentacion
            FROM public.estudiantes_caf e
            WHERE e.tipo_alimentacion != 'NINGUNO'
        """

        conditions = []
        params = {}

        # 2️⃣ En Postgres, ILIKE es excelente para búsquedas que ignoran mayúsculas/minúsculas
        if codigo_estudiante:
            conditions.append("e.codigo_estudiante ILIKE :codigo")
            params["codigo"] = f"%{codigo_estudiante}%"

        if nombre:
            # 🟢 CAMBIO CLAVE: Eliminamos COLLATE y usamos ILIKE
            # ILIKE en Postgres ignora mayúsculas y minúsculas por defecto
            conditions.append("e.nombre ILIKE :nombre")
            params["nombre"] = f"%{nombre}%"

        if grado:
            conditions.append("e.grado = :grado")
            params["grado"] = grado

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        base_query += " ORDER BY e.nombre ASC"

        # Ejecución
        result = db.execute(text(base_query), params).mappings().all()
        
        # Convertimos a lista de diccionarios para asegurar compatibilidad
        return [dict(row) for row in result]

    except Exception as e:
        logger.error(f"Error en buscador de estudiantes en Supabase: {e}")
        raise