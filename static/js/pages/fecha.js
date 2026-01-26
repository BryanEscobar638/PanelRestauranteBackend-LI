import { fechaService } from "../api/fecha.service.js";

function CrearFila(data) {
    return `
        <tr>
            <td>${data.codigo_estudiante}</td>
            <td>${data.nombre}</td>
            <td>${data.grado || ""}</td>
            <td>${data.tipo_alimentacion}</td>
            <td>${data.fecha_hora}</td>
            <td>${data.plan}</td>
            <td>${data.estado}</td>
        </tr>
    `;
}

// Formatear fecha ISO
const formatDateTime = (isoString) => {
    if (!isoString) return "";
    return isoString.replace("T", " - ");
};

// 🔹 Cargar TODOS los registros
async function cargarTablaTodos() {
    try {
        const estudiantes_info = await fechaService.getStudentsAll();

        const tbody = document.getElementById("cuerpodedashboard");
        tbody.innerHTML = "";

        const data = estudiantes_info?.data || [];
        let filas = "";

        for (const registro of data) {
            const estudiante = { ...registro };

            for (const key in estudiante) {
                if (
                    typeof estudiante[key] === "string" &&
                    estudiante[key].includes("T")
                ) {
                    estudiante[key] = formatDateTime(estudiante[key]);
                }
            }

            filas += CrearFila(estudiante);
        }

        tbody.innerHTML = filas;

    } catch (error) {
        console.error("❌ Error cargando todos los registros:", error);
    }
}

// 🔹 Cargar registros FILTRADOS
async function cargarTablaFiltrada(filtros) {
    try {
        const estudiantes_info = await fechaService.getRegistersFiltered(filtros);

        const tbody = document.getElementById("cuerpodedashboard");
        tbody.innerHTML = "";

        const data = estudiantes_info?.data || [];
        let filas = "";

        for (const registro of data) {
            const estudiante = { ...registro };

            for (const key in estudiante) {
                if (
                    typeof estudiante[key] === "string" &&
                    estudiante[key].includes("T")
                ) {
                    estudiante[key] = formatDateTime(estudiante[key]);
                }
            }

            filas += CrearFila(estudiante);
        }

        tbody.innerHTML = filas;

    } catch (error) {
        console.error("❌ Error cargando registros filtrados:", error);
    }
}

// null = traer TODO
let ultimoFiltro = null;

async function init() {
    console.log("✅ dashboard.js cargado correctamente");

    const inputInicio = document.getElementById("fecha_inicio");
    const inputFin = document.getElementById("fecha_fin");
    const inputCodigo = document.getElementById("codigoestudiante");

    const btnBuscar = document.getElementById("btnbuscar");
    const btnExcel = document.getElementById("btnexcel");
    const btnBorrarfecha = document.getElementById("borrarfecha");

    btnBorrarfecha.addEventListener("click", () => {
        inputInicio.value = "";
        inputFin.value = "";
    });

    // ✅ Excel SIEMPRE habilitado
    btnExcel.disabled = false;

    // 🔄 CARGA INICIAL → TODOS
    await cargarTablaTodos();
    ultimoFiltro = null;

    // 🔍 BUSCAR
    btnBuscar.addEventListener("click", async (e) => {
        e.preventDefault();

        const inicio = inputInicio.value || null;
        const fin = inputFin.value || null;
        const codigo = inputCodigo.value?.trim() || null;

        // 👉 SIN FILTROS → TODOS
        if (!inicio && !fin && !codigo) {
            ultimoFiltro = null;
            await cargarTablaTodos();
            return;
        }

        // 👉 CON FILTROS
        ultimoFiltro = {
            fecha_inicio: inicio,
            fecha_fin: fin,
            codigo_estudiante: codigo
        };

        await cargarTablaFiltrada(ultimoFiltro);
    });

    // 📥 DESCARGAR EXCEL
    btnExcel.addEventListener("click", (e) => {
        e.preventDefault();

        // 👉 Sin filtros → Excel de TODO
        if (!ultimoFiltro) {
            fechaService.descargarExcelAll();
            return;
        }

        // 👉 Con filtros
        fechaService.descargarExcel(ultimoFiltro);
    });
}

export { init };
