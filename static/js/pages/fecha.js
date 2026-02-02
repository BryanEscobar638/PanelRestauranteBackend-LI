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

const formatDateTime = (isoString) => {
    if (!isoString) return "";
    return isoString.replace("T", " - ");
};

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
                if (typeof estudiante[key] === "string" && estudiante[key].includes("T")) {
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
                if (typeof estudiante[key] === "string" && estudiante[key].includes("T")) {
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

let ultimoFiltro = null;

async function init() {
    console.log("✅ dashboard.js cargado correctamente");

    const inputInicio = document.getElementById("fecha_inicio");
    const inputFin = document.getElementById("fecha_fin");
    const inputCodigo = document.getElementById("codigoestudiante");

    const btnBuscar = document.getElementById("btnbuscar");
    const btnExcel = document.getElementById("btnexcel");
    const btnBorrarfecha = document.getElementById("borrarfecha");

    // --- 🔍 FUNCIÓN CENTRALIZADA DE BÚSQUEDA ---
    const ejecutarBusqueda = async () => {
        const inicio = inputInicio.value || null;
        const fin = inputFin.value || null;
        const codigo = inputCodigo.value?.trim() || null;

        if (!inicio && !fin && !codigo) {
            ultimoFiltro = null;
            await cargarTablaTodos();
        } else {
            ultimoFiltro = {
                fecha_inicio: inicio,
                fecha_fin: fin,
                codigo_estudiante: codigo
            };
            await cargarTablaFiltrada(ultimoFiltro);
        }
    };

    btnBorrarfecha.addEventListener("click", () => {
        inputInicio.value = "";
        inputFin.value = "";
    });

    btnExcel.disabled = false;
    await cargarTablaTodos();
    ultimoFiltro = null;

    // 🔹 CLICK EN BOTÓN
    btnBuscar.addEventListener("click", async (e) => {
        e.preventDefault();
        await ejecutarBusqueda();
    });

    // 🔹 ENTER EN INPUTS
    [inputInicio, inputFin, inputCodigo].forEach(input => {
        if (input) {
            input.addEventListener("keypress", async (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    await ejecutarBusqueda();
                }
            });
        }
    });

    btnExcel.addEventListener("click", (e) => {
        e.preventDefault();
        if (!ultimoFiltro) {
            fechaService.descargarExcelAll();
        } else {
            fechaService.descargarExcel(ultimoFiltro);
        }
    });
}

export { init };