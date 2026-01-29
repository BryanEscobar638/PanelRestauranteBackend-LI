// apiClient.js - Cliente central para realizar todas las peticiones a la API
const API_BASE_URL = 'http://127.0.0.1:8000'; // pc oficina
// const API_BASE_URL = 'http://172.16.0.28:8000'; // ip pc oficina
// const API_BASE_URL = 'http://172.16.0.47:8000/'; // ip pc restaurante

/**
 * Cliente central para realizar todas las peticiones a la API.
 * @param {string} endpoint - El endpoint al que se llamará (ej. '/users/get-by-centro').
 * @param {object} [options={}] - Opciones para la petición fetch (method, headers, body).
 * @returns {Promise<any>} - La respuesta de la API en formato JSON.
 */
export async function request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = localStorage.getItem('access_token');

    // Configuramos las cabeceras por defecto
    const headers = {
        'accept': 'application/json',
        ...options.headers, // Permite sobrescribir o añadir cabeceras
    };

    // CRÍTICO: Solo añadir Content-Type si NO es FormData
    // FormData establece automáticamente el Content-Type con el boundary correcto
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    // Si hay un token, lo añadimos a la cabecera de Authorization
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, { 
            ...options, 
            headers 
        });

        // Manejo centralizado del error 401 (Token inválido/expirado)
        if (response.status === 401) {
            alert("No tiene permisos");
            return Promise.reject(new Error('No tiene permisos'));
        }

        if (response.status === 403) {
            alert("Token inválido");
            return Promise.reject(new Error('Token inválido'));
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ 
                detail: 'Ocurrió un error en la petición.' 
            }));
            throw new Error(errorData.detail || errorData.message || 'Error desconocido');
        }

        // Si la respuesta no tiene contenido (ej. status 204), devolvemos un objeto vacío.
        return response.status === 204 ? {} : await response.json();

    } catch (error) {
        console.error(`Error en la petición a ${endpoint}:`, error);
        throw error;
    }
}