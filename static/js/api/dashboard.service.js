
import { request } from './apiClient.js';

export const dashboardService = {
    getStudents: () => {
        const endpoint = `/registro/`;
        
        // La lógica es mucho más simple ahora, solo llamamos a nuestro cliente central.
        let respuesta = request(endpoint);

        return respuesta;
    },
    getTotalEstudiantes: async () => {
        return await request("/registro/total-estudiantes");
    },
    getConsumidoresHoy: async () => {
        return await request("/registro/total-estudiantes-hoy");
    },
    getPlanesActivos: async () => {
        return await request("/registro/total-planes");
    },
    getConsumoMes: async () => {
        return await request("/registro/dashboard/consumo-mes");
    }
};