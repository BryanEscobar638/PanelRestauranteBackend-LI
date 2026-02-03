
import { request } from './apiClient.js';

export const fechaService = {
    getRegistersFiltered: async ({
        fecha_inicio = null,
        fecha_fin = null,
        codigo_estudiante = null,
        nombre = null,
        plan = null,
        page = 1,   // Nuevo: parámetro de página
        size = 50   // Nuevo: parámetro de tamaño
    }) => {
        try {
            const params = new URLSearchParams();

            // Filtros básicos
            if (fecha_inicio) params.append("fecha_inicio", fecha_inicio);
            if (fecha_fin) params.append("fecha_fin", fecha_fin);
            if (codigo_estudiante) params.append("codigo_estudiante", codigo_estudiante);
            if (nombre) params.append("nombre", nombre);
            
            if (plan && plan !== "TODOS") {
                params.append("plan", plan);
            }

            // --- NUEVO: Parámetros de paginación ---
            params.append("page", page);
            params.append("size", size);

            const endpoint = `/registro/filtrar?${params.toString()}`;

            console.log("🔎 Buscando con filtros y paginación:", endpoint);

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
        nombre = null,
        plan = null
    }) => {
        const params = new URLSearchParams();

        // Agregamos los filtros a la URL
        if (fecha_inicio) params.append("fecha_inicio", fecha_inicio);
        if (fecha_fin) params.append("fecha_fin", fecha_fin);
        if (codigo_estudiante) params.append("codigo_estudiante", codigo_estudiante);
        if (nombre) params.append("nombre", nombre);
        
        if (plan && plan !== "TODOS") {
            params.append("plan", plan);
        }

        const url = `/registro/excel?${params.toString()}`;

        console.log("⬇️ Descargando Excel FILTRADO:", url);

        // Creamos un link temporal para disparar la descarga sin afectar la navegación
        const link = document.createElement('a');
        link.href = url;
        // El nombre del archivo lo definirá el servidor, pero esto ayuda al navegador
        link.setAttribute('download', 'reporte_filtrado.xlsx'); 
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },
    getStudentsAll: (page = 1, size = 50) => {
    // Usamos Template Literals para inyectar los parámetros en la URL
    const endpoint = `/registro/all?page=${page}&size=${size}`;
    
    // Llamamos al cliente central con la URL paginada
    let respuesta = request(endpoint);

    return respuesta;
    },
    descargarExcelAll: () => {
        // Asegúrate de que la ruta coincida con el @router del backend
        const url = `/registro/excel/all`;

        console.log("⬇️ Descargando Excel COMPLETO:", url);

        // Creamos un elemento 'a' invisible para forzar la descarga sin salir de la página actual
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'registros_completos.xlsx'); // Sugiere el nombre del archivo
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
};