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
        if (!tbody) return;
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
        if (!tbody) return;
        tbody.innerHTML = "";
        const data = estudiantes_info?.data || [];
        let filas = "";

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;">No se encontraron registros con esos filtros</td></tr>`;
            return;
        }

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
    const inputNombre = document.getElementById("nombreestudiante");
    const selectPlan = document.getElementById("selectPlan");

    const btnBuscar = document.getElementById("btnbuscar");
    const btnExcel = document.getElementById("btnexcel");
    const btnBorrarfecha = document.getElementById("borrarfecha");

    const ejecutarBusqueda = async () => {
        const filtros = {
            fecha_inicio: inputInicio.value || null,
            fecha_fin: inputFin.value || null,
            codigo_estudiante: inputCodigo.value?.trim() || null,
            nombre: inputNombre.value?.trim() || null,
            plan: selectPlan.value || "TODOS"
        };

        if (!filtros.fecha_inicio && !filtros.fecha_fin && !filtros.codigo_estudiante && !filtros.nombre && filtros.plan === "TODOS") {
            ultimoFiltro = null;
            await cargarTablaTodos();
        } else {
            ultimoFiltro = filtros;
            await cargarTablaFiltrada(ultimoFiltro);
        }
    };

    // --- CARGA INICIAL (Carga todo al entrar) ---
    await cargarTablaTodos();

    // --- EVENTO CLICK (Asegurando la ejecución) ---
    if (btnBuscar) {
        btnBuscar.addEventListener("click", async (e) => {
            e.preventDefault();
            console.log("Buscando por click...");
            await ejecutarBusqueda();
        });
    }

    // --- EVENTO ENTER ---
    [inputInicio, inputFin, inputCodigo, inputNombre, selectPlan].forEach(input => {
        if (input) {
            input.addEventListener("keypress", async (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    console.log("Buscando por Enter...");
                    await ejecutarBusqueda();
                }
            });
        }
    });

    btnBorrarfecha.addEventListener("click", () => {
        inputInicio.value = "";
        inputFin.value = "";
        inputCodigo.value = "";
        inputNombre.value = "";
        selectPlan.value = "TODOS";
        ultimoFiltro = null;
        cargarTablaTodos();
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