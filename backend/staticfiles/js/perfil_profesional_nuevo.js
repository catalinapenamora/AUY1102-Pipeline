/**
 * Perfil Profesional - AutoParts
 * Manejo completo de perfil de usuario e historial de pedidos
 */

document.addEventListener("DOMContentLoaded", async function () {
    console.log("🚀 Iniciando perfil profesional...");
    
    // Esperar a que AuthManager esté disponible
    if (typeof window.AuthManager === 'undefined') {
        console.error('AuthManager no está disponible');
        return;
    }

    // Verificar autenticación
    const isAuthenticated = await window.AuthManager.ensureAuthenticated();
    if (!isAuthenticated) {
        console.log("❌ Usuario no autenticado, redirigiendo...");
        return;
    }

    // Inicializar el perfil profesional
    const perfilManager = new PerfilProfesional();
    await perfilManager.init();
});

class PerfilProfesional {
    constructor() {
        this.currentOrderDetail = null;
        this.pedidos = [];
        this.filteredPedidos = [];
    }

    async init() {
        try {
            console.log("✅ Inicializando perfil profesional...");
            
            // Cargar datos del perfil
            await this.loadProfileData();
            
            // Cargar historial de pedidos
            await this.loadHistorialPedidos();
            
            // Configurar eventos
            this.setupEventListeners();
            
            console.log("✅ Perfil profesional inicializado correctamente");
        } catch (error) {
            console.error("❌ Error inicializando perfil:", error);
            this.showError("Error cargando el perfil");
        }
    }

    async loadProfileData() {
        try {
            const response = await window.AuthManager.authenticatedFetch("/api/perfil/");
            
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log("📋 Datos del perfil:", data);
            
            // Actualizar información del header
            this.updateProfileHeader(data);
            
            // Actualizar información personal
            this.updatePersonalInfo(data);
            
            return data;
        } catch (error) {
            console.error("Error cargando perfil:", error);
            throw error;
        }
    }

    updateProfileHeader(data) {
        // Nombre en el header
        const nombreElem = document.getElementById("perfil-nombre");
        if (nombreElem) {
            nombreElem.textContent = data.usuario || "Usuario";
        }
        
        // Rol del usuario
        const roleElem = document.getElementById("perfil-role");
        if (roleElem) {
            let role = "Cliente";
            if (data.is_staff) {
                role = "Administrador";
            } else if (data.is_trabajador) {
                role = "Trabajador";
            } else if (data.is_empresa) {
                role = "Empresa";
            }
            roleElem.textContent = role;
        }
    }

    updatePersonalInfo(data) {
        // Información personal en la sección de detalles
        const infoElements = {
            'info-username': data.usuario || '-',
            'info-rut': data.rut || '-',
            'info-email': data.email || '-',
            'info-fecha-registro': data.fecha_registro || '-'
        };

        Object.entries(infoElements).forEach(([id, value]) => {
            const elem = document.getElementById(id);
            if (elem) {
                elem.textContent = value;
            }
        });
    }

    async loadHistorialPedidos() {
        try {
            console.log("📦 Cargando historial de pedidos...");
            
            // Mostrar loading
            this.showLoading(true);
            
            const response = await window.AuthManager.authenticatedFetch("/api/historial-pedidos/");
            
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log("📦 Pedidos recibidos:", data);
            
            this.pedidos = data.pedidos || [];
            this.filteredPedidos = [...this.pedidos];
            
            // Actualizar estadísticas
            this.updateStats(data.estadisticas || {});
            
            // Mostrar pedidos
            this.renderPedidos();
            
            // Ocultar loading
            this.showLoading(false);
            
        } catch (error) {
            console.error("Error cargando historial:", error);
            this.showLoading(false);
            this.showEmptyState();
        }
    }

    updateStats(stats) {
        const statsElements = {
            'total-pedidos': stats.total_pedidos || 0,
            'total-gastado': this.formatCurrency(stats.total_gastado || 0),
            'productos-comprados': stats.productos_comprados || 0,
            'ultimo-pedido': stats.ultimo_pedido || '-'
        };

        Object.entries(statsElements).forEach(([id, value]) => {
            const elem = document.getElementById(id);
            if (elem) {
                elem.textContent = value;
            }
        });
    }

    renderPedidos() {
        const container = document.getElementById("historial-pedidos");
        const emptyState = document.getElementById("empty-historial");
        
        if (!container) return;

        if (this.filteredPedidos.length === 0) {
            container.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        // Ocultar estado vacío y mostrar pedidos
        if (emptyState) emptyState.style.display = 'none';
        container.style.display = 'block';
        
        container.innerHTML = this.filteredPedidos.map(pedido => 
            this.createPedidoCard(pedido)
        ).join('');
        
        // Agregar event listeners para los pedidos
        this.setupPedidoEvents();
    }

    createPedidoCard(pedido) {
        const estadoClass = this.getEstadoClass(pedido.estado);
        const fecha = new Date(pedido.fecha_pedido).toLocaleDateString('es-CL');
        
        return `
            <div class="pedido-card slide-in" data-pedido-id="${pedido.id}">
                <div class="pedido-header" onclick="togglePedido(${pedido.id})">
                    <div class="pedido-info">
                        <div class="pedido-numero">Pedido #${pedido.id}</div>
                        <div class="pedido-fecha">${fecha}</div>
                    </div>
                    <div class="d-flex align-items-center gap-3">
                        <div class="pedido-total">${this.formatCurrency(pedido.total)}</div>
                        <span class="pedido-estado estado-${estadoClass}">${pedido.estado}</span>
                        <i class="fas fa-chevron-down pedido-expand"></i>
                    </div>
                </div>
                
                <div class="pedido-detalle">
                    <div class="row">
                        <div class="col-md-8">
                            <h6>Productos</h6>
                            <ul class="productos-list">
                                ${pedido.productos.map(producto => `
                                    <li class="producto-item">
                                        <div class="producto-info">
                                            <div class="producto-nombre">${producto.nombre}</div>
                                            <div class="producto-cantidad">Cantidad: ${producto.cantidad}</div>
                                        </div>
                                        <div class="producto-precio">${this.formatCurrency(producto.precio_unitario)}</div>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                        <div class="col-md-4">
                            <div class="d-flex flex-column gap-2">
                                <button class="btn-ver-detalle" onclick="verDetallePedido(${pedido.id})">
                                    <i class="fas fa-eye"></i> Ver Detalle
                                </button>
                                ${pedido.factura_url ? `
                                    <button class="btn-descargar-pdf" onclick="descargarPDF('${pedido.factura_url}')">
                                        <i class="fas fa-download"></i> Descargar PDF
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    setupPedidoEvents() {
        // Los eventos se manejan con funciones globales para evitar problemas de scope
        window.togglePedido = (pedidoId) => {
            const card = document.querySelector(`[data-pedido-id="${pedidoId}"]`);
            if (card) {
                card.classList.toggle('expanded');
            }
        };

        window.verDetallePedido = async (pedidoId) => {
            try {
                const response = await window.AuthManager.authenticatedFetch(`/api/pedido/${pedidoId}/`);
                
                if (!response.ok) {
                    throw new Error('Error cargando detalle del pedido');
                }

                const detalle = await response.json();
                this.showDetalleModal(detalle);
                
            } catch (error) {
                console.error('Error:', error);
                this.showError('Error cargando el detalle del pedido');
            }
        };

        window.descargarPDF = (url) => {
            if (url) {
                window.open(url, '_blank');
            }
        };
    }

    showDetalleModal(detalle) {
        const modalBody = document.getElementById('detalle-modal-body');
        const modal = new bootstrap.Modal(document.getElementById('detalleModal'));
        
        if (!modalBody) return;

        modalBody.innerHTML = `
            <div class="detalle-seccion">
                <h6 class="detalle-titulo">Información del Pedido</h6>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Número:</strong> #${detalle.id}</p>
                        <p><strong>Fecha:</strong> ${new Date(detalle.fecha_pedido).toLocaleDateString('es-CL')}</p>
                        <p><strong>Estado:</strong> <span class="badge bg-success">${detalle.estado}</span></p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Total:</strong> ${this.formatCurrency(detalle.total)}</p>
                        <p><strong>Método de Pago:</strong> ${detalle.metodo_pago || 'Webpay'}</p>
                    </div>
                </div>
            </div>

            <div class="detalle-seccion">
                <h6 class="detalle-titulo">Productos</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Producto</th>
                                <th>Cantidad</th>
                                <th>Precio Unit.</th>
                                <th>Subtotal</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${detalle.productos.map(producto => `
                                <tr>
                                    <td>${producto.nombre}</td>
                                    <td>${producto.cantidad}</td>
                                    <td>${this.formatCurrency(producto.precio_unitario)}</td>
                                    <td>${this.formatCurrency(producto.cantidad * producto.precio_unitario)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                
                <!-- Resumen de costos -->
                <div class="row justify-content-end mt-3">
                    <div class="col-md-6">
                        <div class="card border-0 bg-light">
                            <div class="card-body py-2">
                                <div class="d-flex justify-content-between mb-1">
                                    <span>Subtotal (sin IVA):</span>
                                    <span>${this.formatCurrency(Math.round(detalle.total / 1.19))}</span>
                                </div>
                                <div class="d-flex justify-content-between mb-1">
                                    <span>IVA (19%):</span>
                                    <span>${this.formatCurrency(detalle.total - Math.round(detalle.total / 1.19))}</span>
                                </div>
                                <hr class="my-2">
                                <div class="d-flex justify-content-between fw-bold">
                                    <span>Total:</span>
                                    <span>${this.formatCurrency(detalle.total)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            ${detalle.direccion_envio ? `
                <div class="detalle-seccion">
                    <h6 class="detalle-titulo">Dirección de Envío</h6>
                    <p>${detalle.direccion_envio}</p>
                </div>
            ` : ''}
        `;

        // Configurar botón de descarga en el modal
        const btnDescargar = document.getElementById('btn-descargar-modal');
        if (btnDescargar && detalle.factura_url) {
            btnDescargar.onclick = () => window.open(detalle.factura_url, '_blank');
        } else if (btnDescargar) {
            btnDescargar.style.display = 'none';
        }

        modal.show();
    }

    setupEventListeners() {
        // Botón de logout
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async () => {
                await window.AuthManager.logout();
            });
        }

        // Filtros
        const filtroEstado = document.getElementById('filtro-estado');
        const filtroMes = document.getElementById('filtro-mes');

        if (filtroEstado) {
            filtroEstado.addEventListener('change', () => this.applyFilters());
        }

        if (filtroMes) {
            filtroMes.addEventListener('change', () => this.applyFilters());
        }
    }

    applyFilters() {
        const estadoFilter = document.getElementById('filtro-estado')?.value || '';
        const mesFilter = document.getElementById('filtro-mes')?.value || '';

        this.filteredPedidos = this.pedidos.filter(pedido => {
            let passFilter = true;

            // Filtro por estado
            if (estadoFilter && pedido.estado !== estadoFilter) {
                passFilter = false;
            }

            // Filtro por mes
            if (mesFilter) {
                const pedidoDate = new Date(pedido.fecha_pedido);
                const filterDate = new Date(mesFilter + '-01');
                if (pedidoDate.getFullYear() !== filterDate.getFullYear() ||
                    pedidoDate.getMonth() !== filterDate.getMonth()) {
                    passFilter = false;
                }
            }

            return passFilter;
        });

        this.renderPedidos();
    }

    getEstadoClass(estado) {
        const estados = {
            'completado': 'completado',
            'pendiente': 'pendiente',
            'cancelado': 'cancelado'
        };
        return estados[estado] || 'pendiente';
    }

    formatCurrency(amount) {
        return `$${Math.round(amount).toLocaleString('es-CL')}`;
    }

    showLoading(show) {
        const loading = document.getElementById('loading-historial');
        const historial = document.getElementById('historial-pedidos');
        
        if (loading) {
            loading.style.display = show ? 'flex' : 'none';
        }
        if (historial) {
            historial.style.display = show ? 'none' : 'block';
        }
    }

    showEmptyState() {
        const container = document.getElementById("historial-pedidos");
        const emptyState = document.getElementById("empty-historial");
        
        if (container) container.style.display = 'none';
        if (emptyState) emptyState.style.display = 'block';
    }

    showError(message) {
        console.error('Error:', message);
        // Aquí podrías mostrar un toast o notificación
        alert(message);
    }
}
