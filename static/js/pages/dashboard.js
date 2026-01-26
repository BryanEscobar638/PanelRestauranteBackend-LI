import { dashboardService } from "../api/dashboard.service.js";

function CrearFila(data){
    return `
        <tr>
            <td>${data.codigo_estudiante}</td>
            <td>${data.nombre}</td>
            <td>${data.grado}</td>
            <td>${data.tipo_alimentacion}</td>
            <td>${data.fecha_hora}</td>
            <td>${data.plan}</td>
            <td>${data.estado}</td>
        </tr>
    `;
}

function cargarCartas(totalestudiantes, consumoshoy, planes, consumosmes){
    return `
        <div class="cards-grid">
            <div class="card-item">
                <h4>Total Estudiantes</h4>
                <p class="card-text fs-1 fw-bold" id="totalestudiantes">${totalestudiantes.total_estudiantes}</p>
            </div>
            <div class="card-item">
                <h4>Planes Activos</h4>
                <p class="card-text fs-1 fw-bold" id="planesactivos">${planes.total_estudiantes}</p>
            </div>
            <div class="card-item">
                <h4>Consumos Hoy</h4>
                <p class="card-text fs-1 fw-bold" id="consumoshoy">${consumoshoy.total_estudiantes_hoy}</p>
            </div>
            <div class="card-item">
                <h4>Consumos del Mes</h4>
                <p class="card-text fs-1 fw-bold" id="consumosmes">${consumosmes.total_consumo}</p>
            </div>
        </div>
    `;
}


async function init() {
    console.log("✅ dashboard.js cargado correctamente");

    const totalestudiantes = await dashboardService.getTotalEstudiantes();
    const consumoshoy = await dashboardService.getConsumidoresHoy();
    const planes = await dashboardService.getPlanesActivos();
    const consumosmes = await dashboardService.getConsumoMes();
    let divcartas = document.getElementById("cartas");

    divcartas.innerHTML = "";
    divcartas.innerHTML = cargarCartas(totalestudiantes, consumoshoy, planes, consumosmes);
    console.log("totalestudiantes: ", totalestudiantes);
    console.log("consumoshoy: ", consumoshoy);
    console.log("planes: ", planes);
    console.log("consumosmes: ", consumosmes);
    console.log("AHHHHHHHHH");

    const estudiantes_info = await dashboardService.getStudents();
    console.log("estudiantes_info:", estudiantes_info);

    const tbody = document.getElementById("cuerpodedashboard");
    tbody.innerHTML = "";
    let filas = "";

    const data = estudiantes_info.data; // arreglo real
    console.log("data:", data);
    console.log("antes del for");

    // Función para formatear fecha/hora ISO a "YYYY-MM-DD - HH:MM:SS"
    const formatDateTime = (isoString) => {
        if (!isoString) return "";
        return isoString.replace("T", " - ");
    };

    for (let i = 0; i < data.length; i++) {
        const estudiante = { ...data[i] }; // clonamos el objeto para no modificar original

        // Recorremos todas las propiedades del objeto
        for (const key in estudiante) {
            if (typeof estudiante[key] === "string" && estudiante[key].includes("T")) {
                estudiante[key] = formatDateTime(estudiante[key]);
            }
        }

        const fila = CrearFila(estudiante);
        filas += fila;
        console.log("entra", estudiante);
    }

    console.log("después del for");
    tbody.innerHTML = filas;
}



export { init };
