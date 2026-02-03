import { dashboardService } from "../api/dashboard.service.js";

function CrearFila(data) {
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

function cargarCartas(totalestudiantes, consumoshoy, planes, consumosmes) {
    // Extraemos los valores con las nuevas llaves del backend: snack y lunch
    const snacks = consumoshoy.conteo?.snack ?? 0;
    const lunchs = consumoshoy.conteo?.lunch ?? 0;
    const totalHoy = consumoshoy.total_estudiantes_hoy ?? 0;

    return `
        <div class="cards-grid">
            <div class="card-item">
                <h4>Total Estudiantes</h4>
                <p class="card-text fs-1 fw-bold" id="totalestudiantes">${totalestudiantes.total_estudiantes || 0}</p>
            </div>
            
            <div class="card-item">
                <h4>Planes Activos</h4>
                <p class="card-text fs-1 fw-bold" id="planesactivos">${planes.total_estudiantes || 0}</p>
            </div>

            <div class="card shadow-sm border-0 p-3 card-item">
                <div class="card-body p-0">
                    <h4 class="text-muted small text-uppercase fw-bold mb-3">Consumos Hoy (${totalHoy})</h4>
                    
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="text-secondary fw-medium">SNACKS</span>
                        <span class="fs-3 fw-bold text-primary" id="consumosrefrigerio">${snacks}</span>
                    </div>

                    <hr class="my-2 opacity-25">

                    <div class="d-flex justify-content-between align-items-center">
                        <span class="text-secondary fw-medium">LUNCH</span>
                        <span class="fs-3 fw-bold text-success" id="consumosalmuerzo">${lunchs}</span>
                    </div>
                </div>
            </div>

            <div class="card-item">
                <h4>Consumos del Mes</h4>
                <p class="card-text fs-1 fw-bold" id="consumosmes">${consumosmes.total_consumo || 0}</p>
            </div>
        </div>
    `;
}

async function init() {
    console.log("✅ dashboard.js cargado correctamente");

    try {
        const [totalestudiantes, consumoshoy, planes, consumosmes, estudiantes_info] = await Promise.all([
            dashboardService.getTotalEstudiantes(),
            dashboardService.getConsumidoresHoy(),
            dashboardService.getPlanesActivos(),
            dashboardService.getConsumoMes(),
            dashboardService.getStudents()
        ]);

        let divcartas = document.getElementById("cartas");
        divcartas.innerHTML = cargarCartas(totalestudiantes, consumoshoy, planes, consumosmes);

        const tbody = document.getElementById("cuerpodedashboard");
        const data = estudiantes_info.data || [];
        
        const formatDateTime = (isoString) => {
            if (!isoString) return "";
            return isoString.replace("T", " - ").split('.')[0];
        };

        let filas = "";
        data.forEach(item => {
            const estudiante = { ...item };
            for (const key in estudiante) {
                if (typeof estudiante[key] === "string" && estudiante[key].includes("T")) {
                    estudiante[key] = formatDateTime(estudiante[key]);
                }
            }
            filas += CrearFila(estudiante);
        });

        tbody.innerHTML = filas;

    } catch (error) {
        console.error("❌ Error inicializando el dashboard:", error);
    }
}

export { init };