import { dashboardService } from "../api/dashboard.service.js";

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

function cargarCartas(totalestudiantes, consumoshoy, planes, consumosmes) {
    const totalHoy = consumoshoy.total_estudiantes_hoy ?? 0;
    const snack = consumoshoy.desglose?.snack || { elementary: 0, highschool: 0, total: 0 };
    const lunch = consumoshoy.desglose?.lunch || { elementary: 0, highschool: 0, total: 0 };

    return `
        <div class="cards-grid">
            <div class="card shadow-sm border-0 p-3 card-item d-flex flex-column">
                <h4 class="text-muted small text-uppercase fw-bold text-center mb-0">Total Estudiantes</h4>
                <div class="flex-grow-1 d-flex align-items-center justify-content-center">
                    <p class="card-text fw-bold mb-0" style="font-size: 3.5rem;" id="totalestudiantes">${totalestudiantes.total_estudiantes || 0}</p>
                </div>
            </div>
            
            <div class="card shadow-sm border-0 p-3 card-item d-flex flex-column">
                <h4 class="text-muted small text-uppercase fw-bold text-center mb-0">Planes Activos</h4>
                <div class="flex-grow-1 d-flex align-items-center justify-content-center">
                    <p class="card-text fw-bold mb-0" style="font-size: 3.5rem;" id="planesactivos">${planes.total_estudiantes || 0}</p>
                </div>
            </div>

            <div class="card shadow-sm border-0 p-3 card-item">
                <h4 class="text-muted small text-uppercase fw-bold text-center mb-3">Consumos Hoy (${totalHoy})</h4>
                <div class="d-flex flex-column justify-content-around h-100">
                    <div class="text-center">
                        <div class="d-flex justify-content-around align-items-center">
                            <span class="text-secondary fw-bold small">SNACKS</span>
                            <span class="fw-bold text-primary" style="font-size: 2.5rem;">${snack.total}</span>
                        </div>
                        <div class="d-flex justify-content-center gap-3">
                            <small class="text-muted">Elem: <span class="fw-bold">${snack.elementary}</span></small>
                            <small class="text-muted">High: <span class="fw-bold">${snack.highschool}</span></small>
                        </div>
                    </div>

                    <hr class="my-2 opacity-25">

                    <div class="text-center">
                        <div class="d-flex justify-content-around align-items-center">
                            <span class="text-secondary fw-bold small">LUNCH</span>
                            <span class="fw-bold text-success" style="font-size: 2.5rem;">${lunch.total}</span>
                        </div>
                        <div class="d-flex justify-content-center gap-3">
                            <small class="text-muted">Elem: <span class="fw-bold">${lunch.elementary}</span></small>
                            <small class="text-muted">High: <span class="fw-bold">${lunch.highschool}</span></small>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card shadow-sm border-0 p-3 card-item d-flex flex-column">
                <h4 class="text-muted small text-uppercase fw-bold text-center mb-0">Consumos del Mes</h4>
                <div class="flex-grow-1 d-flex align-items-center justify-content-center">
                    <p class="card-text fw-bold mb-0" style="font-size: 3.5rem;" id="consumosmes">${consumosmes.total_consumo || 0}</p>
                </div>
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
        if (divcartas) {
            divcartas.innerHTML = cargarCartas(totalestudiantes, consumoshoy, planes, consumosmes);
        }

        const tbody = document.getElementById("cuerpodedashboard");
        if (tbody) {
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

            tbody.innerHTML = filas || `<tr><td colspan="7" class="text-center">No hay registros recientes</td></tr>`;
        }

    } catch (error) {
        console.error("❌ Error inicializando el dashboard:", error);
    }
}

export { init };