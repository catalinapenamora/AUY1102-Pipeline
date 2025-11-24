/**
 * Sistema de Inventario - Taller de Manolo
 * Integración con AutoParts API Externa
 */

class TallerManoloAPI {
    constructor() {
        this.apiBaseUrl = window.location.origin + '/api/external';
        this.apiKey = 'TALLER_MANOLO_2024';
        this.currentPage = 1;
        this.currentQuery = '';
        this.currentFilters = {};
        this.categorias = [];
        
        this.init();
    }

    async init() {
        console.log('🔧 Inicializando Sistema del Taller de Manolo...');
        
        // Verificar conexión con la API
        await this.verificarConexionAPI();
        
        // Cargar categorías
        await this.cargarCategorias();
        
        // Configurar eventos
        this.setupEventListeners();
        
        // Mostrar estado inicial
        this.mostrarEstadoVacio();
        
        console.log('✅ Sistema del Taller inicializado correctamente');
    }

    async verificarConexionAPI() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/info/`, {
                headers: {
                    'X-API-Key': this.apiKey,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.actualizarEstadoConexion(true, 'Conectado a AutoParts API');
                    document.getElementById('connection-details').textContent = 
                        `Conectado correctamente - API v${data.data.version}`;
                    return true;
                }
            }
            
            throw new Error('Error en la respuesta de la API');
            
        } catch (error) {
            console.error('❌ Error conectando con AutoParts API:', error);
            this.actualizarEstadoConexion(false, 'Error de conexión');
            return false;
        }
    }

    actualizarEstadoConexion(conectado, mensaje) {
        const statusElement = document.getElementById('api-status');
        const statusSpan = statusElement.querySelector('span');
        
        if (conectado) {
            statusElement.className = 'api-status api-connected';
            statusElement.innerHTML = '<i class="fas fa-wifi"></i><span>' + mensaje + '</span>';
        } else {
            statusElement.className = 'api-status api-error';
            statusElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i><span>' + mensaje + '</span>';
        }
    }

    async cargarCategorias() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/categories/`, {
                headers: {
                    'X-API-Key': this.apiKey,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.categorias = data.data;
                    this.renderizarCategorias();
                }
            }
        } catch (error) {
            console.error('❌ Error cargando categorías:', error);
        }
    }

    renderizarCategorias() {
        const select = document.getElementById('category-filter');
        
        // Limpiar opciones existentes (excepto la primera)
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        // Agregar categorías
        this.categorias.forEach(categoria => {
            const option = document.createElement('option');
            option.value = categoria.id;
            option.textContent = `${categoria.nombre} (${categoria.total_productos})`;
            select.appendChild(option);
        });
    }

    setupEventListeners() {
        // Enter en búsqueda
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.buscarRepuestos();
            }
        });

        // Cambios en filtros
        document.getElementById('category-filter').addEventListener('change', () => {
            if (this.currentQuery) {
                this.buscarRepuestos();
            }
        });

        document.getElementById('stock-filter').addEventListener('change', () => {
            if (this.currentQuery) {
                this.buscarRepuestos();
            }
        });
    }

    async buscarRepuestos(query = null, page = 1) {
        const searchInput = document.getElementById('search-input');
        const searchQuery = query || searchInput.value.trim();
        
        if (!searchQuery) {
            alert('Por favor ingresa un término de búsqueda');
            return;
        }

        this.currentQuery = searchQuery;
        this.currentPage = page;
        
        // Obtener filtros
        const categoria = document.getElementById('category-filter').value;
        const stock = document.getElementById('stock-filter').value;
        
        this.currentFilters = {
            q: searchQuery,
            limit: 12,
            page: page
        };
        
        if (categoria) this.currentFilters.category = categoria;
        if (stock) this.currentFilters.in_stock = stock;

        this.mostrarLoading(true);
        this.actualizarUltimaConsulta();

        try {
            // Usar endpoint de búsqueda para consultas específicas
            const endpoint = searchQuery ? '/search/' : '/catalog/';
            const params = new URLSearchParams(this.currentFilters);
            
            const response = await fetch(`${this.apiBaseUrl}${endpoint}?${params}`, {
                headers: {
                    'X-API-Key': this.apiKey,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.mostrarResultados(data.data, data.meta);
                } else {
                    throw new Error(data.message);
                }
            } else {
                throw new Error(`Error HTTP ${response.status}`);
            }
            
        } catch (error) {
            console.error('❌ Error en búsqueda:', error);
            this.mostrarError('Error al buscar productos: ' + error.message);
        } finally {
            this.mostrarLoading(false);
        }
    }

    async verCatalogoCompleto(page = 1) {
        this.currentQuery = '';
        this.currentPage = page;
        
        const categoria = document.getElementById('category-filter').value;
        const stock = document.getElementById('stock-filter').value;
        
        this.currentFilters = {
            limit: 12,
            page: page
        };
        
        if (categoria) this.currentFilters.category = categoria;
        if (stock) this.currentFilters.in_stock = stock;

        this.mostrarLoading(true);
        this.actualizarUltimaConsulta();

        try {
            const params = new URLSearchParams(this.currentFilters);
            
            const response = await fetch(`${this.apiBaseUrl}/catalog/?${params}`, {
                headers: {
                    'X-API-Key': this.apiKey,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.mostrarResultados(data.data, data.meta);
                } else {
                    throw new Error(data.message);
                }
            } else {
                throw new Error(`Error HTTP ${response.status}`);
            }
            
        } catch (error) {
            console.error('❌ Error obteniendo catálogo:', error);
            this.mostrarError('Error al obtener catálogo: ' + error.message);
        } finally {
            this.mostrarLoading(false);
        }
    }

    mostrarResultados(productos, meta = null) {
        this.ocultarTodosLosEstados();
        
        const resultsSection = document.getElementById('results-section');
        const productsContainer = document.getElementById('products-container');
        const resultsTitle = document.getElementById('results-title');
        const resultsCount = document.getElementById('results-count');
        
        // Título y contador
        if (this.currentQuery) {
            resultsTitle.textContent = `Resultados para "${this.currentQuery}"`;
        } else {
            resultsTitle.textContent = 'Catálogo de AutoParts';
        }
        
        resultsCount.textContent = `${productos.length} productos`;
        
        // Limpiar contenedor
        productsContainer.innerHTML = '';
        
        if (productos.length === 0) {
            this.mostrarEstadoVacio();
            return;
        }
        
        // Renderizar productos
        productos.forEach(producto => {
            const productCard = this.crearTarjetaProducto(producto);
            productsContainer.appendChild(productCard);
        });
        
        // Mostrar paginación si hay meta
        if (meta && meta.pagination) {
            this.renderizarPaginacion(meta.pagination);
        }
        
        resultsSection.style.display = 'block';
    }

    crearTarjetaProducto(producto) {
        const col = document.createElement('div');
        col.className = 'col-md-4 col-lg-3 mb-4';
        
        // Determinar estado del stock
        let stockBadge = '';
        let stockClass = '';
        
        if (producto.stock > 10) {
            stockBadge = `${producto.stock} disponibles`;
            stockClass = 'stock-available';
        } else if (producto.stock > 0) {
            stockBadge = `${producto.stock} disponibles`;
            stockClass = 'stock-low';
        } else {
            stockBadge = 'Sin stock';
            stockClass = 'stock-out';
        }
        
        col.innerHTML = `
            <div class="card product-card h-100">
                <div class="position-relative">
                    ${producto.imagen_url ? 
                        `<img src="${producto.imagen_url}" class="card-img-top" alt="${producto.nombre}" style="height: 200px; object-fit: cover;">` :
                        `<div class="card-img-top d-flex align-items-center justify-content-center bg-light" style="height: 200px;">
                            <i class="fas fa-cog fa-3x text-muted"></i>
                        </div>`
                    }
                    <span class="stock-badge ${stockClass}">${stockBadge}</span>
                </div>
                <div class="card-body d-flex flex-column">
                    <h6 class="card-title">${producto.nombre}</h6>
                    <p class="card-text text-muted small flex-grow-1">
                        <strong>Marca:</strong> ${producto.marca || 'No especificada'}<br>
                        ${producto.categoria ? `<strong>Categoría:</strong> ${producto.categoria}` : ''}
                    </p>
                    <div class="mt-auto">
                        <div class="price-tag text-center">
                            $${this.formatearPrecio(producto.precio)}
                            ${producto.precio_mayorista ? 
                                `<br><small>Mayorista: $${this.formatearPrecio(producto.precio_mayorista)}</small>` : 
                                ''
                            }
                        </div>
                        <div class="d-grid gap-2 mt-3">
                            <button class="btn btn-outline-primary btn-sm" onclick="tallerManolo.verDetalle(${producto.id})">
                                <i class="fas fa-eye"></i> Ver Detalle
                            </button>
                            ${producto.disponible ? 
                                `<button class="btn btn-primary btn-sm" onclick="tallerManolo.cotizar(${producto.id})">
                                    <i class="fas fa-calculator"></i> Cotizar
                                </button>` :
                                `<button class="btn btn-secondary btn-sm" disabled>
                                    <i class="fas fa-times"></i> No Disponible
                                </button>`
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return col;
    }

    async verDetalle(productoId) {
        const modal = new bootstrap.Modal(document.getElementById('modalDetalleProducto'));
        const modalContent = document.getElementById('modal-content');
        const modalLoading = document.getElementById('modal-loading');
        
        modalLoading.style.display = 'block';
        modalContent.style.display = 'none';
        modal.show();

        try {
            const response = await fetch(`${this.apiBaseUrl}/catalog/${productoId}/`, {
                headers: {
                    'X-API-Key': this.apiKey,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.renderizarDetalleProducto(data.data);
                } else {
                    throw new Error(data.message);
                }
            } else {
                throw new Error(`Error HTTP ${response.status}`);
            }
            
        } catch (error) {
            console.error('❌ Error obteniendo detalle:', error);
            modalContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    Error al cargar los detalles del producto
                </div>
            `;
        } finally {
            modalLoading.style.display = 'none';
            modalContent.style.display = 'block';
        }
    }

    renderizarDetalleProducto(producto) {
        const modalContent = document.getElementById('modal-content');
        
        // Almacenar producto actual para botones
        this.productoActual = producto;
        
        modalContent.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    ${producto.imagenes && producto.imagenes.principal ? 
                        `<img src="${producto.imagenes.principal}" class="img-fluid rounded" alt="${producto.nombre}">` :
                        `<div class="bg-light rounded d-flex align-items-center justify-content-center" style="height: 250px;">
                            <i class="fas fa-cog fa-4x text-muted"></i>
                        </div>`
                    }
                </div>
                <div class="col-md-8">
                    <h4>${producto.nombre}</h4>
                    <p class="text-muted">${producto.descripcion || 'Sin descripción disponible'}</p>
                    
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong>Marca:</strong><br>
                            ${producto.marca || 'No especificada'}
                        </div>
                        <div class="col-6">
                            <strong>Categoría:</strong><br>
                            ${producto.categoria ? producto.categoria.nombre : 'Sin categoría'}
                        </div>
                    </div>
                    
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong>Stock Disponible:</strong><br>
                            <span class="badge ${producto.disponibilidad.en_stock ? 'bg-success' : 'bg-danger'}">
                                ${producto.stock} unidades
                            </span>
                        </div>
                        <div class="col-6">
                            <strong>Estado:</strong><br>
                            <span class="text-capitalize">${producto.disponibilidad.estado}</span>
                        </div>
                    </div>
                    
                    ${producto.especificaciones.peso || 
                      producto.especificaciones.dimensiones.largo || 
                      producto.especificaciones.dimensiones.ancho || 
                      producto.especificaciones.dimensiones.alto ? 
                        `<div class="mb-3">
                            <strong>Especificaciones:</strong><br>
                            ${producto.especificaciones.peso ? `Peso: ${producto.especificaciones.peso} kg<br>` : ''}
                            ${(producto.especificaciones.dimensiones.largo || 
                               producto.especificaciones.dimensiones.ancho || 
                               producto.especificaciones.dimensiones.alto) ? 
                                `Dimensiones: ${producto.especificaciones.dimensiones.largo || '?'} x ${producto.especificaciones.dimensiones.ancho || '?'} x ${producto.especificaciones.dimensiones.alto || '?'} cm` : 
                                ''
                            }
                        </div>` : ''
                    }
                    
                    <div class="bg-light p-3 rounded">
                        <h5 class="mb-2">Precios</h5>
                        <div class="row">
                            <div class="col-6">
                                <strong>Precio Unitario:</strong><br>
                                <span class="h4 text-primary">$${this.formatearPrecio(producto.precios.precio_unitario)}</span>
                            </div>
                            ${producto.precios.precio_mayorista ? 
                                `<div class="col-6">
                                    <strong>Precio Mayorista:</strong><br>
                                    <span class="h5 text-success">$${this.formatearPrecio(producto.precios.precio_mayorista)}</span>
                                </div>` : ''
                            }
                        </div>
                        <small class="text-muted">
                            ${producto.precios.incluye_iva ? 'IVA incluido' : 'IVA no incluido'} | 
                            Moneda: ${producto.precios.moneda}
                        </small>
                    </div>
                </div>
            </div>
        `;
    }

    cotizar(productoId) {
        // Aquí iría la lógica para agregar al presupuesto
        alert(`Función de cotización para producto ID: ${productoId}\n\nEsta funcionalidad se integraría con el sistema de presupuestos del taller.`);
    }

    consultarDisponibilidad() {
        if (this.productoActual) {
            alert(`Consulta de disponibilidad para:\n\n${this.productoActual.nombre}\nStock actual: ${this.productoActual.stock} unidades\n\nEn un sistema real, esto podría generar una llamada o email automático a AutoParts.`);
        }
    }

    agregarAPresupuesto() {
        if (this.productoActual) {
            alert(`Producto agregado al presupuesto:\n\n${this.productoActual.nombre}\nPrecio: $${this.formatearPrecio(this.productoActual.precio)}\n\nEn un sistema real, esto se agregaría al presupuesto del cliente.`);
        }
    }

    renderizarPaginacion(pagination) {
        const container = document.getElementById('pagination-container');
        container.innerHTML = '';
        
        if (pagination.total_pages <= 1) return;
        
        // Botón anterior
        if (pagination.has_previous) {
            const prevBtn = document.createElement('li');
            prevBtn.className = 'page-item';
            prevBtn.innerHTML = `
                <a class="page-link" href="#" onclick="tallerManolo.cambiarPagina(${pagination.current_page - 1})">
                    <i class="fas fa-chevron-left"></i>
                </a>
            `;
            container.appendChild(prevBtn);
        }
        
        // Páginas
        for (let i = 1; i <= pagination.total_pages; i++) {
            const pageBtn = document.createElement('li');
            pageBtn.className = `page-item ${i === pagination.current_page ? 'active' : ''}`;
            pageBtn.innerHTML = `
                <a class="page-link" href="#" onclick="tallerManolo.cambiarPagina(${i})">${i}</a>
            `;
            container.appendChild(pageBtn);
        }
        
        // Botón siguiente
        if (pagination.has_next) {
            const nextBtn = document.createElement('li');
            nextBtn.className = 'page-item';
            nextBtn.innerHTML = `
                <a class="page-link" href="#" onclick="tallerManolo.cambiarPagina(${pagination.current_page + 1})">
                    <i class="fas fa-chevron-right"></i>
                </a>
            `;
            container.appendChild(nextBtn);
        }
    }

    cambiarPagina(page) {
        if (this.currentQuery) {
            this.buscarRepuestos(this.currentQuery, page);
        } else {
            this.verCatalogoCompleto(page);
        }
    }

    formatearPrecio(precio) {
        return new Intl.NumberFormat('es-CL').format(precio);
    }

    actualizarUltimaConsulta() {
        const now = new Date();
        document.getElementById('last-update').textContent = 
            now.toLocaleTimeString('es-CL', { hour12: false });
    }

    mostrarLoading(mostrar) {
        document.getElementById('loading-section').style.display = mostrar ? 'block' : 'none';
    }

    mostrarEstadoVacio() {
        this.ocultarTodosLosEstados();
        document.getElementById('empty-state').style.display = 'block';
    }

    mostrarError(mensaje) {
        this.ocultarTodosLosEstados();
        const errorState = document.getElementById('error-state');
        errorState.querySelector('p').textContent = mensaje;
        errorState.style.display = 'block';
    }

    ocultarTodosLosEstados() {
        document.getElementById('loading-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('error-state').style.display = 'none';
    }

    limpiarResultados() {
        document.getElementById('search-input').value = '';
        document.getElementById('category-filter').value = '';
        document.getElementById('stock-filter').value = '';
        this.currentQuery = '';
        this.currentFilters = {};
        this.mostrarEstadoVacio();
    }

    exportarResultados() {
        alert('Función de exportación\n\nEn un sistema real, esto exportaría los resultados a Excel o PDF para compartir con el cliente.');
    }

    async reintentar() {
        await this.verificarConexionAPI();
        if (this.currentQuery) {
            this.buscarRepuestos();
        } else {
            this.mostrarEstadoVacio();
        }
    }
}

// Funciones globales para eventos
function buscarRepuestos() {
    tallerManolo.buscarRepuestos();
}

function verCatalogoCompleto() {
    tallerManolo.verCatalogoCompleto();
}

function limpiarResultados() {
    tallerManolo.limpiarResultados();
}

function exportarResultados() {
    tallerManolo.exportarResultados();
}

function reintentar() {
    tallerManolo.reintentar();
}

function consultarDisponibilidad() {
    tallerManolo.consultarDisponibilidad();
}

function agregarAPresupuesto() {
    tallerManolo.agregarAPresupuesto();
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.tallerManolo = new TallerManoloAPI();
});
