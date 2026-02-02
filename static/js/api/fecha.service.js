
import { request } from './apiClient.js';

export const fechaService = {
    getRegistersFiltered: async ({
        fecha_inicio = null,
        fecha_fin = null,
        codigo_estudiante = null,
        nombre = null, // Nuevo parámetro
        plan = null    // Nuevo parámetro
    }) => {
        try {
            const params = new URLSearchParams();

            if (fecha_inicio) params.append("fecha_inicio", fecha_inicio);
            if (fecha_fin) params.append("fecha_fin", fecha_fin);
            if (codigo_estudiante) params.append("codigo_estudiante", codigo_estudiante);
            if (nombre) params.append("nombre", nombre);
            
            // Solo enviamos el plan si es distinto a "TODOS" para limpiar la URL
            if (plan && plan !== "TODOS") {
                params.append("plan", plan);
            }

            const endpoint = `/registro/filtrar?${params.toString()}`;

            console.log("🔎 Endpoint con filtros avanzados:", endpoint);

            const respuesta = await request(endpoint);
            return respuesta;

        } catch (error) {
            console.error("❌ Error al obtener registros filtrados:", error);
            return null;
        }
    },
    descargarExcel: ({
        fecha_inicio = null,
        fecha_fin = null,
        codigo_estudiante = null,
        nombre = null, // Nuevo
        plan = null    // Nuevo
    }) => {
        const params = new URLSearchParams();

        if (fecha_inicio) params.append("fecha_inicio", fecha_inicio);
        if (fecha_fin) params.append("fecha_fin", fecha_fin);
        if (codigo_estudiante) params.append("codigo_estudiante", codigo_estudiante);
        if (nombre) params.append("nombre", nombre);
        
        // Solo enviamos el plan si es distinto a "TODOS"
        if (plan && plan !== "TODOS") {
            params.append("plan", plan);
        }

        const url = `/registro/excel?${params.toString()}`;

        console.log("⬇️ Descargando Excel con filtros avanzados:", url);

        // 🔥 Esto dispara la descarga real en el navegador
        window.location.href = url;
    },
    getStudentsAll: () => {
        const endpoint = `/registro/all`;
        
        // La lógica es mucho más simple ahora, solo llamamos a nuestro cliente central.
        let respuesta = request(endpoint);

        return respuesta;
    },
    descargarExcelAll: () => {
        const url = `/registro/excel/all`;

        console.log("⬇️ Descargando Excel COMPLETO:", url);

        window.location.href = url;
    }
};