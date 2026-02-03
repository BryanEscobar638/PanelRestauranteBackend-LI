import { fechaService } from "../api/fecha.service.js";

// --- VARIABLES DE ESTADO ---
let paginaActual = 1;
const registrosPorPagina = 50;
let ultimoFiltro = null;
let cargando = false;

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
    return isoString.replace("T", " - ").split('.')[0];
};

async function actualizarTabla() {
    if (cargando) return;
    cargando = true;

    try {
        const btnAnt = document.getElementById("btnAnterior");
        const btnSig = document.getElementById("btnSiguiente");
        const tbody = document.getElementById("cuerpodedashboard");

        if (btnAnt) btnAnt.disabled = true;
        if (btnSig) btnSig.disabled = true;

        let respuesta;
        if (!ultimoFiltro) {
            respuesta = await fechaService.getStudentsAll(paginaActual, registrosPorPagina);
        } else {
            respuesta = await fechaService.getRegistersFiltered({
                ...ultimoFiltro,
                page: paginaActual,
                size: registrosPorPagina
            });
        }

        if (!tbody) return;
        tbody.innerHTML = ""; 

        const data = respuesta?.data || [];
        const total = respuesta?.total || 0;

        // Actualizar indicadores visuales (con validación de existencia)
        const elPagina = document.getElementById("numPagina");
        const elTotal = document.getElementById("totalRegistros");
        const elVisibles = document.getElementById("regVisibles");

        if (elPagina) elPagina.innerText = paginaActual;
        if (elTotal) elTotal.innerText = total;
        if (elVisibles) elVisibles.innerText = data.length;

        // Control de botones
        if (btnAnt) btnAnt.disabled = paginaActual <= 1;
        if (btnSig) btnSig.disabled = (paginaActual * registrosPorPagina) >= total;

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;">No se encontraron registros</td></tr>`;
            return;
        }

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

        // --- MEJORA: Volver arriba al cambiar de página ---
        window.scrollTo({ top: 0, behavior: 'smooth' });

    } catch (error) {
        console.error("❌ Error al actualizar la tabla:", error);
        const tbody = document.getElementById("cuerpodedashboard");
        if (tbody) tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:red;">Error al cargar datos</td></tr>`;
    } finally {
        cargando = false;
    }
}

async function init() {
    console.log("✅ dashboard.js cargado correctamente");

    // Referencias
    const btnAnterior = document.getElementById("btnAnterior");
    const btnSiguiente = document.getElementById("btnSiguiente");
    const btnBuscar = document.getElementById("btnbuscar");
    const btnBorrar = document.getElementById("borrarfecha");
    const btnExcel = document.getElementById("btnexcel");

    const inputInicio = document.getElementById("fecha_inicio");
    const inputFin = document.getElementById("fecha_fin");
    const inputCodigo = document.getElementById("codigoestudiante");
    const inputNombre = document.getElementById("nombreestudiante");
    const selectPlan = document.getElementById("selectPlan");

    const ejecutarBusqueda = async () => {
        // Capturar valores actuales
        const filtros = {
            fecha_inicio: inputInicio?.value || null,
            fecha_fin: inputFin?.value || null,
            codigo_estudiante: inputCodigo?.value?.trim() || null,
            nombre: inputNombre?.value?.trim() || null,
            plan: selectPlan?.value || "TODOS"
        };

        // Evaluar si realmente hay filtros
        const tieneFiltros = filtros.fecha_inicio || filtros.fecha_fin || 
                            filtros.codigo_estudiante || filtros.nombre || 
                            filtros.plan !== "TODOS";

        ultimoFiltro = tieneFiltros ? filtros : null;
        paginaActual = 1; // Siempre resetear a 1 en búsqueda nueva
        await actualizarTabla();
    };

    // --- ASIGNACIÓN DE EVENTOS ---
    if (btnAnterior) {
        btnAnterior.onclick = async () => {
            if (paginaActual > 1 && !cargando) {
                paginaActual--;
                await actualizarTabla();
            }
        };
    }

    if (btnSiguiente) {
        btnSiguiente.onclick = async () => {
            const elTotal = document.getElementById("totalRegistros");
            const total = parseInt(elTotal?.innerText) || 0;
            if ((paginaActual * registrosPorPagina) < total && !cargando) {
                paginaActual++;
                await actualizarTabla();
            }
        };
    }

    if (btnBuscar) {
        btnBuscar.onclick = async (e) => {
            e.preventDefault();
            await ejecutarBusqueda();
        };
    }

    if (btnBorrar) {
        btnBorrar.onclick = async () => {
            if (inputInicio) inputInicio.value = "";
            if (inputFin) inputFin.value = "";
            if (inputCodigo) inputCodigo.value = "";
            if (inputNombre) inputNombre.value = "";
            if (selectPlan) selectPlan.value = "TODOS";
            ultimoFiltro = null;
            paginaActual = 1;
            await actualizarTabla();
        };
    }

    // Tecla Enter
    [inputInicio, inputFin, inputCodigo, inputNombre, selectPlan].forEach(input => {
        if (input) {
            input.onkeypress = async (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    await ejecutarBusqueda();
                }
            };
        }
    });

    if (btnExcel) {
        btnExcel.onclick = (e) => {
            e.preventDefault();
            // Usamos la variable de estado actual para el Excel
            !ultimoFiltro ? fechaService.descargarExcelAll() : fechaService.descargarExcel(ultimoFiltro);
        };
    }

    // Carga inicial
    await actualizarTabla();
}

export { init };