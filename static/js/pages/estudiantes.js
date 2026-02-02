import { estudiantesService } from "../api/estudiantes.service.js";

async function cargarTablaEstudiantes({ filtros = null } = {}) {
    try {
        let response;
        if (!filtros) {
            response = await estudiantesService.obtenerConPlan();
        } else {
            response = await estudiantesService.buscarEstudiantes(filtros);
        }

        const tbody = document.getElementById("cuerpodeestudiantes");
        tbody.innerHTML = "";
        const data = response?.data || [];

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center">No se encontraron resultados</td></tr>`;
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

    // --- FUNCIÓN DE BÚSQUEDA ---
    const ejecutarBusqueda = async () => {
        const filtros = {
            nombre: inputNombre.value.trim() || null,
            codigo_estudiante: inputCodigo.value.trim() || null,
            grado: inputGrado?.value.trim() || null
        };

        if (!filtros.nombre && !filtros.codigo_estudiante && !filtros.grado) {
            await cargarTablaEstudiantes();
        } else {
            await cargarTablaEstudiantes({ filtros });
        }
    };

    // 🔹 AL CARGAR → todos los que tienen plan
    await cargarTablaEstudiantes();

    // 🔹 EVENTO CLICK
    btnBuscar.addEventListener("click", async (e) => {
        e.preventDefault();
        await ejecutarBusqueda();
    });

    // 🔹 EVENTO ENTER EN INPUTS
    // Agrupamos los inputs en un array para asignarles el evento a todos de una vez
    [inputNombre, inputCodigo, inputGrado].forEach(input => {
        if (input) {
            input.addEventListener("keypress", async (e) => {
                if (e.key === "Enter") {
                    e.preventDefault(); // Evita que la página se recargue
                    await ejecutarBusqueda();
                }
            });
        }
    });
}

export { init };