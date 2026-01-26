import { estudiantesService } from "../api/estudiantes.service.js";

async function cargarTablaEstudiantes({ filtros = null } = {}) {
    try {
        let response;

        // 🧠 Decidir qué endpoint usar
        if (!filtros) {
            response = await estudiantesService.obtenerConPlan();
        } else {
            response = await estudiantesService.buscarEstudiantes(filtros);
        }

        const tbody = document.getElementById("cuerpodeestudiantes");
        tbody.innerHTML = "";

        const data = response?.data || [];

        if (data.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center">No se encontraron resultados</td>
                </tr>
            `;
            return;
        }

        let filas = "";
        data.forEach(est => {
            filas += `
                <tr>
                    <td>${est.codigo_estudiante}</td>
                    <td>${est.nombre}</td>
                    <td>${est.grado}</td>
                    <td>${est.tipo_alimentacion}</td>
                </tr>
            `;
        });

        tbody.innerHTML = filas;

    } catch (error) {
        console.error("❌ Error cargando estudiantes:", error);
    }
}

async function init() {
    console.log("✅ estudiantes.js cargado");

    const inputNombre = document.getElementById("nombreestudiante");
    const inputCodigo = document.getElementById("codigoestudiante");
    const inputGrado = document.getElementById("grado");
    const btnBuscar = document.getElementById("btnBuscar");

    // 🔹 AL CARGAR → todos los que tienen plan
    await cargarTablaEstudiantes();

    btnBuscar.addEventListener("click", async (e) => {
        e.preventDefault();

        const filtros = {
            nombre: inputNombre.value.trim() || null,
            codigo_estudiante: inputCodigo.value.trim() || null,
            grado: inputGrado?.value.trim() || null
        };

        // 🧠 Si no hay filtros → volver a todos
        if (!filtros.nombre && !filtros.codigo_estudiante && !filtros.grado) {
            await cargarTablaEstudiantes();
            return;
        }

        // 🔍 Buscar con filtros
        await cargarTablaEstudiantes({ filtros });
    });
}

export { init };
