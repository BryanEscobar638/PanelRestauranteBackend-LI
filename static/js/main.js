// main.js - Sistema de navegación y carga dinámica de contenido

const mainContent = document.getElementById('contenido');
const navLinks = document.getElementById('sidenavAccordion');

// Manejar clicks en el navbar
navLinks.addEventListener('click', (event) => {
    console.log(event);
    const link = event.target.closest('a[data-page]');
    
    if (link) {
        event.preventDefault();
        const pageToLoad = link.dataset.page;
        console.log(`Paso 1: Clic detectado. Se va a cargar la página: '${pageToLoad}'`);
        
        // Cargar contenido HTML + JS
        loadContent(pageToLoad);
        
        // Actualizar logo con ícono y texto
        updateLogoFromNav(pageToLoad);
    }
});

// Función principal para cargar contenido HTML dinámicamente
const loadContent = async (page) => {
    console.log(`Paso 2: Se llamó a loadContent con el parámetro: '${page}'`);

    try {
        const response = await fetch(`/static/pages/${page}.html`);
        console.log("Paso 3: Se intentó hacer fetch. Respuesta recibida:", response);

        if (!response.ok) {
            throw new Error(`Error de red: ${response.status} - ${response.statusText}`);
        }
        
        const html = await response.text();
        mainContent.innerHTML = html;
        console.log("Paso 4: El contenido HTML se ha inyectado en #main-content.");
        
        // ============= INICIALIZACIÓN DE MÓDULOS POR PÁGINA =============

        if (page === 'dashboard') {
        import('/static/js/pages/dashboard.js')
            .then(module => {
                console.log("📦 dashboard module:", module);
                console.log("📦 typeof init:", typeof module.init);
                module.init();
            })
            .catch(err => {
                console.error("❌ Error importando dashboard.js", err);
            });
        }

        if (page === 'fecha') {
        import('/static/js/pages/fecha.js')
            .then(module => {
                console.log("📦 fecha module:", module);
                console.log("📦 typeof init:", typeof module.init);
                module.init();
            })
            .catch(err => {
                console.error("❌ Error importando fecha.js", err);
            });
        }

        if (page === "estudiantes") {
        import("/static/js/pages/estudiantes.js")
            .then(({ init }) => {
                if (typeof init === "function") {
                    init();
                } else {
                    console.error("❌ init no está exportado en estudiantes.js");
                }
            })
            .catch(err => {
                console.error("❌ Error importando estudiantes.js", err);
            });
}


    } catch (error) {
        console.error("¡ERROR! Algo falló dentro de loadContent:", error);
        mainContent.innerHTML = `<h3 class="text-center text-danger p-5">No se pudo cargar el contenido. Revisa la consola (F12).</h3>`;
    }
};



// ============= INICIALIZACIÓN AL CARGAR LA PÁGINA =============
document.addEventListener("DOMContentLoaded", function() {
    loadContent('dashboard');
});