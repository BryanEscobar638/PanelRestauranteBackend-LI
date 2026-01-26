
import { request } from './apiClient.js';

export const fechaService = {
    getRegistersFiltered: async ({
    fecha_inicio = null,
    fecha_fin = null,
    codigo_estudiante = null
    }) => {
        try {
            const params = new URLSearchParams();

            if (fecha_inicio) params.append("fecha_inicio", fecha_inicio);
            if (fecha_fin) params.append("fecha_fin", fecha_fin);
            if (codigo_estudiante) params.append("codigo_estudiante", codigo_estudiante);

            const endpoint = `/registro/filtrar?${params.toString()}`;

            console.log("🔎 Endpoint:", endpoint);

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
        codigo_estudiante = null
    }) => {
        const params = new URLSearchParams();

        if (fecha_inicio) params.append("fecha_inicio", fecha_inicio);
        if (fecha_fin) params.append("fecha_fin", fecha_fin);
        if (codigo_estudiante) params.append("codigo_estudiante", codigo_estudiante);

        const url = `/registro/excel?${params.toString()}`;

        console.log("⬇️ Descargando Excel:", url);

        // 🔥 Esto dispara la descarga real
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