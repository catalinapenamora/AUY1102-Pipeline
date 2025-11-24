console.log("home.js cargado");
// Función para formatear precios con separadores de miles (formato chileno)
function formatPrice(price) {
    return `$${Math.round(price).toLocaleString('es-CL')}`;
}

document.addEventListener("DOMContentLoaded", () => {
    function cargarProductos() {
        let url = "/api/productos/";

        fetch(url)
            .then(res => res.json())
            .then(productos => {
                const container = document.getElementById("bestseller");
                if (!container) {
                    console.error("No se encontró el contenedor #bestseller");
                    return;
                }
                container.innerHTML = '';

                productos.slice(0, 3).forEach(p => {
                    console.log("Producto:", p.nombre, "Precio:", p.precio, "Mayorista:", p.precio_mayorista, "ES_EMPRESA:", window.ES_EMPRESA);
                    const precioMostrar = window.ES_EMPRESA ? p.precio_mayorista : p.precio;
                    const card = `
                        <div class="col-md-6 col-lg-4 loaded">
                            <div class="card h-100 card-hover bg-bestseller border-0 rounded shadow-sm">
                                <img src="${p.imagen}" class="card-img-top img-fluid rounded-top" alt="${p.nombre}" style="max-height: 250px; object-fit: cover; border-bottom: 4px solid #C1121F;">
                                <div class="card-body text-center">
                                    <h5 class="card-title text-azul fw-bold">${p.nombre}</h5>
                                    <div class="d-flex justify-content-center my-2">
                                        <i class="fas fa-star"></i>
                                        <i class="fas fa-star"></i>
                                        <i class="fas fa-star"></i>
                                        <i class="fas fa-star"></i>
                                        <i class="fas fa-star text-muted"></i>
                                    </div>
                                    <h4 class="mb-3 text-dark fw-semibold">${formatPrice(precioMostrar)}</h4>
                                    <a href="/producto/${p.id}" class="btn-bestseller">Ver producto <i class="fas fa-arrow-right ms-1"></i></a>
                                </div>
                            </div>
                        </div>
                    `;
                    container.innerHTML += card;
                });
            })
            .catch(err => console.error("Error cargando productos:", err));
    }

    cargarProductos();
});