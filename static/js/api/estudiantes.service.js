import { request } from "./apiClient.js";

export const estudiantesService = {

    // 🔹 TRAER TODOS LOS QUE TIENEN PLAN
    obtenerConPlan: async () => {
        try {
            const endpoint = "/registro/estudiantes-con-plan";
            console.log("📥 Endpoint todos con plan:", endpoint);
            return await request(endpoint);
        } catch (error) {
            console.error("❌ Error obteniendo estudiantes con plan:", error);
            return null;
        }
    },

    // 🔹 BUSCAR CON FILTROS
    buscarEstudiantes: async ({
        nombre = null,
        codigo_estudiante = null,
        grado = null
    }) => {
        try {
            const params = new URLSearchParams();

            if (nombre) params.append("nombre", nombre);
            if (codigo_estudiante) params.append("codigo_estudiante", codigo_estudiante);
            if (grado) params.append("grado", grado);

            const endpoint = `/registro/buscar-estudiantes?${params.toString()}`;
            console.log("🔎 Endpoint búsqueda:", endpoint);

            return await request(endpoint);
        } catch (error) {
            console.error("❌ Error buscando estudiantes:", error);
            return null;
        }
    }
};
