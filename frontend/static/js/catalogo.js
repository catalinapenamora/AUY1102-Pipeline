// Función para formatear precios con separadores de miles (formato chileno)
function formatPrice(price) {
    return `$${Math.round(price).toLocaleString('es-CL')}`;
}

// Variables globales para paginación
let currentPage = 1;
let totalPages = 1;
let currentFilters = {};

document.addEventListener("DOMContentLoaded", () => {
    // Esperar a que AuthManager esté disponible
    const waitForAuthManager = () => {
        return new Promise((resolve) => {
            if (window.authManager) {
                resolve();
            } else {
                setTimeout(() => waitForAuthManager().then(resolve), 100);
            }
        });
    };

    waitForAuthManager().then(() => {
        console.log("✅ CATÁLOGO: AuthManager disponible");
        initializeCatalog();
    });
});

function initializeCatalog() {
    const selectOrden = document.getElementById("ordenar-select");

    // Obtener página inicial de la URL
    const urlParams = new URLSearchParams(window.location.search);
    currentPage = parseInt(urlParams.get("page")) || 1;

    function cargarProductos(page = 1) {
        const params = new URLSearchParams(window.location.search);
        const categoria = params.get("categoria");
        const orden = params.get("orden");

        // Actualizar filtros actuales
        currentFilters = { categoria, orden };
        currentPage = page;

        if (selectOrden && orden) {
            selectOrden.value = orden;
        }

        let url = "/api/productos/";
        const queryParams = new URLSearchParams();
        
        if (categoria) queryParams.append("categoria", categoria);
        if (orden) queryParams.append("orden", orden);
        queryParams.append("page", page);
        queryParams.append("per_page", 12); // 12 productos por página

        if (queryParams.toString()) {
            url += "?" + queryParams.toString();
        }

        console.log("🔗 Cargando productos:", url);

        fetch(url)
            .then(res => res.json())
            .then(data => {
                console.log("📦 Datos recibidos:", data);
                
                // Verificar si la respuesta tiene el formato de paginación
                const productos = data.productos || data; // Compatibilidad con formato anterior
                const pagination = data.pagination;

                const container = document.getElementById("productos-container");
                container.innerHTML = '';

                // Mostrar mensaje si no hay productos
                if (!productos || productos.length === 0) {
                    container.innerHTML = `
                        <div class="col-12 text-center py-5">
                            <i class="fas fa-search fa-3x text-muted mb-3"></i>
                            <h4 class="text-muted">No se encontraron productos</h4>
                            <p class="text-muted">Intenta cambiar los filtros o el orden.</p>
                        </div>
                    `;
                    updatePagination(null);
                    return;
                }

                productos.forEach(p => {
                    console.log("Producto:", p);
                    const card = `
                    <div class="col-md-6 col-lg-6 col-xl-4">
                        <a href="/producto/${p.id}" class="text-decoration-none">
                        <div class="rounded position-relative fruite-item">
                            <div class="fruite-img">
                            <img src="${p.imagen}" class="img-fluid w-100 rounded-top" alt="${p.nombre}">
                            </div>
                            <div class="text-white bg-secondary px-3 py-1 rounded position-absolute" style="top: 10px; left: 10px;">${p.nombre_categoria}</div>
                            <div class="p-4 border border-secondary border-top-0 rounded-bottom">
                            <h4>${p.nombre}</h4>
                            <p>${p.descripcion}</p>
                            <div class="d-flex justify-content-between flex-lg-wrap">
                                <div class="price-info">
                                    <p class="text-dark fs-5 fw-bold mb-0">
                                    ${ES_EMPRESA 
                                        ? formatPrice(p.precio_mayorista)
                                        : formatPrice(p.precio)}
                                    </p>
                                    <small class="text-muted">IVA incluido</small>
                                </div>
                            </div>
                            </div>
                        </div>
                        </a>
                        <button onclick="agregarAlCarrito(${p.id})" class="btn border border-secondary rounded-pill px-3 text-primary">
                                <i class="fa fa-shopping-bag me-2 text-primary"></i> Añadir al carro
                         </button>
                    </div>`;
                    container.innerHTML += card;
                });

                // Actualizar paginación
                if (pagination) {
                    totalPages = pagination.total_pages;
                    updatePagination(pagination);
                    updateProductCount(pagination);
                }
            })
            .catch(err => {
                console.error("Error cargando productos:", err);
                const container = document.getElementById("productos-container");
                container.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                        <h4 class="text-muted">Error cargando productos</h4>
                        <p class="text-muted">Por favor, recarga la página.</p>
                    </div>
                `;
            });
        }

        if (selectOrden) {
            selectOrden.addEventListener("change", () => {
                const orden = selectOrden.value;
                const params = new URLSearchParams(window.location.search);

                if (orden) {
                    params.set("orden", orden);
                } else {
                    params.delete("orden");
                }
                
                // Resetear a página 1 cuando cambie el orden
                params.delete("page");

                const nuevaUrl = `${window.location.pathname}?${params.toString()}`;
                window.history.replaceState({}, '', nuevaUrl);
                cargarProductos(1);
            });
        }

        cargarProductos(currentPage);
    }

    // Función para actualizar la paginación
    function updatePagination(pagination) {
        const paginationContainer = document.getElementById("pagination-container");
        
        if (!pagination || pagination.total_pages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        const { current_page, total_pages, has_previous, has_next } = pagination;
        
        let paginationHTML = '<nav aria-label="Paginación de productos"><ul class="pagination justify-content-center">';
        
        // Botón "Anterior"
        if (has_previous) {
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="changePage(${current_page - 1})" aria-label="Anterior">
                        <span aria-hidden="true">&laquo;</span>
                    </a>
                </li>
            `;
        } else {
            paginationHTML += `
                <li class="page-item disabled">
                    <span class="page-link">&laquo;</span>
                </li>
            `;
        }

        // Números de página
        const startPage = Math.max(1, current_page - 2);
        const endPage = Math.min(total_pages, current_page + 2);

        if (startPage > 1) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(1)">1</a></li>`;
            if (startPage > 2) {
                paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            if (i === current_page) {
                paginationHTML += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else {
                paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${i})">${i}</a></li>`;
            }
        }

        if (endPage < total_pages) {
            if (endPage < total_pages - 1) {
                paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${total_pages})">${total_pages}</a></li>`;
        }

        // Botón "Siguiente"
        if (has_next) {
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="changePage(${current_page + 1})" aria-label="Siguiente">
                        <span aria-hidden="true">&raquo;</span>
                    </a>
                </li>
            `;
        } else {
            paginationHTML += `
                <li class="page-item disabled">
                    <span class="page-link">&raquo;</span>
                </li>
            `;
        }

        paginationHTML += '</ul></nav>';
        paginationContainer.innerHTML = paginationHTML;
    }

    // Función para actualizar el contador de productos
    function updateProductCount(pagination) {
        const countContainer = document.getElementById("product-count");
        if (countContainer && pagination) {
            const { current_page, total_items, per_page } = pagination;
            const startItem = (current_page - 1) * per_page + 1;
            const endItem = Math.min(current_page * per_page, total_items);
            
            countContainer.innerHTML = `
                <p class="text-muted">
                    Mostrando ${startItem}-${endItem} de ${total_items} productos
                </p>
            `;
        }
    }

// Función global para cambiar de página
window.changePage = function(page) {
    const params = new URLSearchParams(window.location.search);
    params.set("page", page);
    
    const nuevaUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, '', nuevaUrl);
    
    // Scroll hacia arriba suavemente
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Necesitamos redefinir cargarProductos aquí o pasarla como referencia
    const selectOrden = document.getElementById("ordenar-select");
    const params2 = new URLSearchParams(window.location.search);
    const categoria = params2.get("categoria");
    const orden = params2.get("orden");

    let url = "/api/productos/";
    const queryParams = new URLSearchParams();
    
    if (categoria) queryParams.append("categoria", categoria);
    if (orden) queryParams.append("orden", orden);
    queryParams.append("page", page);
    queryParams.append("per_page", 12);

    if (queryParams.toString()) {
        url += "?" + queryParams.toString();
    }

    fetch(url)
        .then(res => res.json())
        .then(data => {
            const productos = data.productos || data;
            const pagination = data.pagination;

            const container = document.getElementById("productos-container");
            container.innerHTML = '';

            if (!productos || productos.length === 0) {
                container.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fas fa-search fa-3x text-muted mb-3"></i>
                        <h4 class="text-muted">No se encontraron productos</h4>
                        <p class="text-muted">Intenta cambiar los filtros o el orden.</p>
                    </div>
                `;
                updatePagination(null);
                return;
            }

            productos.forEach(p => {
                const card = `
                <div class="col-md-6 col-lg-6 col-xl-4">
                    <a href="/producto/${p.id}" class="text-decoration-none">
                    <div class="rounded position-relative fruite-item">
                        <div class="fruite-img">
                        <img src="${p.imagen}" class="img-fluid w-100 rounded-top" alt="${p.nombre}">
                        </div>
                        <div class="text-white bg-secondary px-3 py-1 rounded position-absolute" style="top: 10px; left: 10px;">${p.nombre_categoria}</div>
                        <div class="p-4 border border-secondary border-top-0 rounded-bottom">
                        <h4>${p.nombre}</h4>
                        <p>${p.descripcion}</p>
                        <div class="d-flex justify-content-between flex-lg-wrap">
                            <div class="price-info">
                                <p class="text-dark fs-5 fw-bold mb-0">
                                ${ES_EMPRESA 
                                    ? formatPrice(p.precio_mayorista)
                                    : formatPrice(p.precio)}
                                </p>
                                <small class="text-muted">IVA incluido</small>
                            </div>
                        </div>
                        </div>
                    </div>
                    </a>
                    <button onclick="agregarAlCarrito(${p.id})" class="btn border border-secondary rounded-pill px-3 text-primary">
                            <i class="fa fa-shopping-bag me-2 text-primary"></i> Añadir al carro
                     </button>
                </div>`;
                container.innerHTML += card;
            });

            if (pagination) {
                updatePagination(pagination);
                updateProductCount(pagination);
            }
        })
        .catch(err => {
            console.error("Error cargando productos:", err);
        });
};

async function agregarAlCarrito(productoId) {
            try {
                // Usar AuthManager para agregar al carrito (híbrido)
                const resultado = await window.authManager.agregarAlCarrito(productoId, 1);
                
                if (resultado.success) {
                    if (resultado.type === 'guest') {
                        mostrarNotificacion('Producto agregado al carrito de invitado. Inicia sesión para finalizar tu compra.', 'success');
                    } else {
                        mostrarNotificacion('Producto agregado al carrito', 'success');
                    }
                } else {
                    mostrarNotificacion(resultado.error || 'Error al agregar producto', 'error');
                }
            } catch (error) {
                console.error("Error al agregar al carrito:", error);
                mostrarNotificacion('Error al agregar producto al carrito', 'error');
            }
        }
        function mostrarNotificacion(mensaje, tipo = 'success') {
        const notif = document.createElement('div');
        notif.className = `alert alert-${tipo === 'error' ? 'danger' : 'success'} fixed-top m-3`;
        notif.style.zIndex = 9999;
        notif.innerText = mensaje;
        document.body.appendChild(notif);

        setTimeout(() => {
            notif.remove();
        }, 3000);
        }
        async function actualizarContadorCarrito() {
            // Usar AuthManager para actualizar contador híbrido
            if (window.authManager) {
                await window.authManager.actualizarContadorCarrito();
            }
        }
        