/**
 * Dashboard de Pedidos - AutoParts
 * Gestión completa de pedidos para trabajadores y administradores
 */

class DashboardPedidos {
    constructor() {
        this.pedidos = [];
        this.estadisticas = {};
        this.currentOrderDetail = null;
        this.filtros = {
            estado: '',
            metodo_pago: '',
            fecha_desde: '',
            fecha_hasta: '',
            search: ''
        };
    }

    async init() {
        try {
            console.log("✅ Inicializando Dashboard de Pedidos...");
            
            // Configurar eventos
            this.setupEventListeners();
            
            // Cargar datos iniciales
            await this.cargarDatos();
            
            console.log("✅ Dashboard de Pedidos inicializado correctamente");
        } catch (error) {
            console.error("❌ Error inicializando dashboard:", error);
            this.showError("Error inicializando el dashboard");
        }
    }

    setupEventListeners() {
        // Filtros
        document.getElementById('filtro-estado').addEventListener('change', () => this.aplicarFiltros());
        document.getElementById('filtro-metodo').addEventListener('change', () => this.aplicarFiltros());
        document.getElementById('filtro-fecha-desde').addEventListener('change', () => this.aplicarFiltros());
        document.getElementById('filtro-fecha-hasta').addEventListener('change', () => this.aplicarFiltros());
        
        // Búsqueda con debounce
        let searchTimeout;
        document.getElementById('filtro-buscar').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => this.aplicarFiltros(), 500);
        });

        // Modal events
        const modalElement = document.getElementById('modalDetallePedido');
        if (modalElement) {
            // Botón X para cerrar
            const closeBtn = modalElement.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    this.cerrarModal();
                });
            }
            
            // Todos los botones con data-bs-dismiss="modal"
            const dismissBtns = modalElement.querySelectorAll('[data-bs-dismiss="modal"]');
            dismissBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    this.cerrarModal();
                });
            });
            
            // Cerrar al hacer clic en el backdrop
            modalElement.addEventListener('click', (e) => {
                if (e.target === modalElement) {
                    this.cerrarModal();
                }
            });
            
            // Cerrar con tecla Escape
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && modalElement.classList.contains('show')) {
                    this.cerrarModal();
                }
            });
        }
    }

    async cargarDatos() {
        try {
            this.showLoading(true);
            
            // Construir parámetros de consulta
            const params = new URLSearchParams();
            
            Object.entries(this.filtros).forEach(([key, value]) => {
                if (value) {
                    params.append(key, value);
                }
            });

            const response = await window.AuthManager.authenticatedFetch(`/api/dashboard/pedidos/?${params}`);
            
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log("📦 Datos del dashboard recibidos:", data);
            
            if (data.success) {
                this.pedidos = data.pedidos || [];
                this.estadisticas = data.estadisticas || {};
                
                this.renderEstadisticas();
                this.renderPedidos();
            } else {
                throw new Error(data.error || 'Error cargando datos del dashboard');
            }
            
        } catch (error) {
            console.error("❌ Error cargando datos:", error);
            this.showError(`Error cargando datos: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    renderEstadisticas() {
        const container = document.getElementById('estadisticas-container');
        if (!container) return;

        const stats = this.estadisticas;
        
        container.innerHTML = `
            <!-- Primera fila de estadísticas -->
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number">${stats.total_pedidos || 0}</span>
                    <div class="stat-label">Total Pedidos</div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number" style="font-size: 1.5rem;">${this.formatCurrency(stats.total_ventas || 0)}</span>
                    <div class="stat-label">Total Ventas</div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number">${stats.pedidos_pendientes || 0}</span>
                    <div class="stat-label">Pendientes</div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number">${stats.pedidos_pagados || 0}</span>
                    <div class="stat-label">Pagados</div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number">${stats.pedidos_fallidos || 0}</span>
                    <div class="stat-label">Fallidos</div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number">${stats.pedidos_cancelados || 0}</span>
                    <div class="stat-label">Cancelados</div>
                </div>
            </div>
            
            <!-- Segunda fila con estadísticas de flujo -->
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number">${stats.pedidos_listo_retiro || 0}</span>
                    <div class="stat-label">Listos Retiro</div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number">${stats.pedidos_retirados || 0}</span>
                    <div class="stat-label">Retirados</div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number">${stats.pedidos_preparacion || 0}</span>
                    <div class="stat-label">En Preparación</div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number">${stats.pedidos_enviados || 0}</span>
                    <div class="stat-label">Enviados</div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number">${stats.pedidos_transferencia || 0}</span>
                    <div class="stat-label">Transferencia</div>
                </div>
            </div>
            <div class="col-lg-2 col-md-4 col-sm-6 mb-3">
                <div class="stat-card">
                    <span class="stat-number">${stats.pedidos_webpay || 0}</span>
                    <div class="stat-label">WebPay</div>
                </div>
            </div>
        `;
    }

    renderPedidos() {
        const container = document.getElementById('tabla-pedidos');
        const emptyState = document.getElementById('empty-pedidos');
        const tbody = document.getElementById('tbody-pedidos');
        const totalBadge = document.getElementById('total-pedidos-badge');
        
        if (!container || !tbody) return;

        // Actualizar contador
        if (totalBadge) {
            totalBadge.textContent = `${this.pedidos.length} pedidos`;
        }

        if (this.pedidos.length === 0) {
            container.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        // Mostrar tabla y ocultar estado vacío
        if (emptyState) emptyState.style.display = 'none';
        container.style.display = 'block';
        
        // Generar filas de la tabla
        tbody.innerHTML = this.pedidos.map(pedido => 
            this.createPedidoRow(pedido)
        ).join('');
        
        // Agregar event listeners
        this.setupPedidoEvents();
    }

    createPedidoRow(pedido) {
        const estadoBadge = this.getEstadoBadge(pedido.estado);
        const metodoBadge = this.getMetodoBadge(pedido.metodo_pago);
        
        return `
            <tr class="pedido-row" data-order-id="${pedido.order_id}">
                <td>
                    <strong>#${pedido.order_id}</strong>
                </td>
                <td>
                    <small>${pedido.fecha}</small>
                </td>
                <td>
                    <div>
                        <strong>${pedido.email}</strong>
                        ${pedido.direccion ? `<br><small class="text-muted">${pedido.comuna}</small>` : ''}
                    </div>
                </td>
                <td>
                    <span class="estado-badge ${estadoBadge}">${pedido.estado}</span>
                </td>
                <td>
                    <span class="${metodoBadge}">
                        <i class="fas ${pedido.metodo_pago === 'webpay' ? 'fa-credit-card' : 'fa-university'}"></i>
                        ${pedido.metodo_pago}
                    </span>
                </td>
                <td>
                    <strong>${this.formatCurrency(pedido.monto)}</strong>
                </td>
                <td>
                    <span class="badge bg-secondary">${pedido.cantidad_productos} items</span>
                    ${pedido.total_productos > 1 ? `<br><small class="text-muted">${pedido.total_productos} productos</small>` : ''}
                </td>
                <td>
                    <small class="text-muted">${pedido.tipo_entrega}</small>
                    ${pedido.ot_codigo ? `<br><small class="text-success">OT: ${pedido.ot_codigo}</small>` : ''}
                </td>
                <td>
                    <button type="button" class="btn btn-sm btn-outline-primary ver-pedido-btn" 
                            data-order-id="${pedido.order_id}" 
                            title="Ver detalles del pedido">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    getEstadoBadge(estado) {
        const badges = {
            'pendiente': 'estado-pendiente',
            'pagado': 'estado-pagado',
            'listo_retiro': 'estado-pendiente',
            'retirado': 'estado-pagado',
            'preparacion': 'estado-pendiente',
            'enviado': 'estado-pagado',
            'fallido': 'estado-fallido',
            'cancelado': 'estado-cancelado'
        };
        return badges[estado] || 'estado-pendiente';
    }

    getMetodoBadge(metodo) {
        const badges = {
            'webpay': 'metodo-webpay',
            'transferencia': 'metodo-transferencia'
        };
        return badges[metodo] || '';
    }

    setupPedidoEvents() {
        // Event listeners para botones "ver"
        document.querySelectorAll('.ver-pedido-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                const orderId = btn.getAttribute('data-order-id');
                await this.verDetallePedido(orderId);
            });
        });

        // Event listeners para filas clickeables
        document.querySelectorAll('.pedido-row').forEach(row => {
            row.addEventListener('click', async (e) => {
                // Solo si no se hizo clic en un botón
                if (!e.target.closest('button')) {
                    const orderId = row.getAttribute('data-order-id');
                    await this.verDetallePedido(orderId);
                }
            });
        });
        
        console.log("✅ Eventos de pedidos configurados");
    }

    async verDetallePedido(orderId) {
        try {
            console.log(`🔍 Cargando detalles del pedido ${orderId}...`);
            
            // Mostrar modal usando JavaScript nativo
            const modalElement = document.getElementById('modalDetallePedido');
            modalElement.style.display = 'block';
            modalElement.classList.add('show');
            modalElement.setAttribute('aria-modal', 'true');
            modalElement.setAttribute('role', 'dialog');
            
            // Agregar backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.id = 'modal-backdrop-dashboard';
            document.body.appendChild(backdrop);
            document.body.classList.add('modal-open');
            
            this.showDetalleLoading(true);
            
            // Hacer petición al API del dashboard
            const response = await window.AuthManager.authenticatedFetch(`/api/dashboard/pedidos/${orderId}/`);
            
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log("📦 Detalles del pedido recibidos:", data);
            
            if (data.success) {
                this.currentOrderDetail = data.pedido;
                this.mostrarDetallePedido(data.pedido);
            } else {
                throw new Error(data.error || 'Error obteniendo detalles del pedido');
            }
            
        } catch (error) {
            console.error("❌ Error cargando detalles del pedido:", error);
            this.showError(`No se pudieron cargar los detalles del pedido: ${error.message}`);
            // Cerrar modal en caso de error
            this.cerrarModal();
        }
    }

    mostrarDetallePedido(pedido) {
        try {
            // Información básica
            document.getElementById('detalle-order-id').textContent = `#${pedido.order_id}`;
            document.getElementById('detalle-fecha').textContent = pedido.fecha;
            document.getElementById('detalle-metodo-pago').textContent = pedido.metodo_pago;
            
            // Calcular totales con IVA desglosado
            const totalConIva = parseFloat(pedido.monto);
            const netoSinIva = totalConIva / 1.19;
            const ivaCalculado = totalConIva - netoSinIva;
            
            document.getElementById('detalle-total').textContent = this.formatCurrency(totalConIva);
            document.getElementById('detalle-subtotal-sin-iva').textContent = this.formatCurrency(netoSinIva);
            document.getElementById('detalle-iva').textContent = this.formatCurrency(ivaCalculado);
            document.getElementById('detalle-total-final').textContent = this.formatCurrency(totalConIva);
            
            document.getElementById('detalle-tipo-entrega').textContent = pedido.tipo_entrega;
            
            // Badge de estado
            const estadoBadge = this.getEstadoBadge(pedido.estado);
            const estadoElement = document.getElementById('detalle-estado-badge');
            estadoElement.innerHTML = `<span class="estado-badge ${estadoBadge}">${pedido.estado}</span>`;
            
            // Establecer estado actual en selector
            document.getElementById('nuevo-estado').value = pedido.estado;
            
            // Información del cliente
            if (pedido.cliente) {
                document.getElementById('detalle-cliente-email').textContent = pedido.cliente.email || '-';
                document.getElementById('detalle-cliente-nombre').textContent = pedido.cliente.nombre || 'No especificado';
                document.getElementById('detalle-cliente-rut').textContent = pedido.cliente.rut || 'No especificado';
                
                let tipoCliente = 'Cliente';
                if (pedido.cliente.es_trabajador) tipoCliente = 'Trabajador';
                else if (pedido.cliente.es_empresa) tipoCliente = 'Empresa';
                document.getElementById('detalle-cliente-tipo').textContent = tipoCliente;
            }
            
            // Información de entrega
            const direccionDiv = document.getElementById('detalle-direccion');
            if (pedido.direccion_completa) {
                direccionDiv.style.display = 'block';
                document.getElementById('detalle-direccion-completa').textContent = 
                    `${pedido.direccion_completa.direccion}, ${pedido.direccion_completa.comuna}, ${pedido.direccion_completa.region}`;
            } else {
                direccionDiv.style.display = 'none';
            }
            
            // Información de envío
            const envioDiv = document.getElementById('detalle-envio');
            if (pedido.envio && pedido.envio.ot_codigo) {
                envioDiv.style.display = 'block';
                document.getElementById('detalle-ot-codigo').textContent = pedido.envio.ot_codigo || 'En proceso';
                document.getElementById('detalle-estado-envio').textContent = pedido.envio.estado_envio || 'Sin estado';
                document.getElementById('detalle-peso').textContent = pedido.envio.peso_total ? `${pedido.envio.peso_total} kg` : 'No especificado';
                document.getElementById('detalle-dimensiones').textContent = pedido.envio.dimensiones || 'No especificado';
            } else {
                envioDiv.style.display = 'none';
            }
            
            // Información de transferencia bancaria (si aplica)
            const transferenciaDiv = document.getElementById('detalle-transferencia');
            if (pedido.transferencia) {
                transferenciaDiv.style.display = 'block';
                
                document.getElementById('transferencia-banco').textContent = pedido.transferencia.banco;
                document.getElementById('transferencia-numero-cuenta').textContent = pedido.transferencia.numero_cuenta;
                document.getElementById('transferencia-monto').textContent = this.formatCurrency(pedido.transferencia.monto);
                document.getElementById('transferencia-order-id').textContent = pedido.transferencia.order_id;
            } else {
                transferenciaDiv.style.display = 'none';
            }
            
            // Productos
            const productosContainer = document.getElementById('detalle-productos');
            
            if (pedido.productos && pedido.productos.length > 0) {
                productosContainer.innerHTML = pedido.productos.map(producto => {
                    const subtotal = producto.subtotal || (producto.precio_unitario * producto.cantidad);
                    
                    return `
                    <tr>
                        <td>
                            <div class="d-flex align-items-center">
                                ${producto.imagen ? 
                                    `<img src="${producto.imagen}" alt="${producto.nombre}" class="me-2" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;">` : 
                                    `<div class="me-2" style="width: 40px; height: 40px; background-color: #f8f9fa; border-radius: 4px; display: flex; align-items: center; justify-content: center;"><i class="fas fa-image text-muted"></i></div>`
                                }
                                <span>${producto.nombre}</span>
                            </div>
                        </td>
                        <td>${producto.cantidad}</td>
                        <td>${this.formatCurrency(producto.precio_unitario)}</td>
                        <td><strong>${this.formatCurrency(subtotal)}</strong></td>
                    </tr>
                `;
                }).join('');
            } else {
                productosContainer.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center text-muted">
                            <i class="fas fa-exclamation-triangle"></i> No se encontraron productos
                        </td>
                    </tr>
                `;
            }
            
            // Ocultar loading y mostrar contenido
            this.showDetalleLoading(false);
            
            // Mostrar botones de acción según tipo de entrega
            this.mostrarBotonesAccion(pedido);
            
        } catch (error) {
            console.error("❌ Error mostrando detalles del pedido:", error);
            this.showError('Error mostrando los detalles del pedido');
        }
    }

    mostrarBotonesAccion(pedido) {
        const botonesRetiro = document.getElementById('botones-retiro');
        const botonesEnvio = document.getElementById('botones-envio');
        
        // Ocultar todos los botones primero
        botonesRetiro.style.display = 'none';
        botonesEnvio.style.display = 'none';
        
        // Mostrar botones según el tipo de entrega y estado
        if (pedido.tipo_entrega === 'Retiro en tienda') {
            // Mostrar si: pagado, pendiente con transferencia, o listo para retiro
            const estadosValidos = [
                'pagado', 
                'listo_retiro'
            ];
            
            const esPendienteTransferencia = pedido.estado === 'pendiente' && pedido.metodo_pago === 'transferencia';
            
            if (estadosValidos.includes(pedido.estado) || esPendienteTransferencia) {
                botonesRetiro.style.display = 'block';
                
                // Ajustar botones según el estado específico
                const btnListoRetiro = document.querySelector('#botones-retiro .btn-warning');
                const btnConfirmarRetiro = document.querySelector('#botones-retiro .btn-success');
                
                if (pedido.estado === 'listo_retiro') {
                    // Si ya está listo para retiro, ocultar el botón "Marcar Listo"
                    btnListoRetiro.style.display = 'none';
                    btnConfirmarRetiro.style.display = 'inline-block';
                } else {
                    // Mostrar ambos botones
                    btnListoRetiro.style.display = 'inline-block';
                    btnConfirmarRetiro.style.display = 'inline-block';
                }
            }
        } else if (pedido.tipo_entrega === 'Envío a domicilio') {
            // Mostrar si está pagado, en preparación o enviado
            const estadosValidos = ['pagado', 'preparacion', 'enviado'];
            
            if (estadosValidos.includes(pedido.estado)) {
                botonesEnvio.style.display = 'block';
                
                // Ajustar botones según el estado específico
                const btnPreparacion = document.querySelector('#botones-envio .btn-info');
                const btnEnviado = document.querySelector('#botones-envio .btn-primary');
                
                if (pedido.estado === 'preparacion') {
                    btnPreparacion.style.display = 'none';
                    btnEnviado.style.display = 'inline-block';
                } else if (pedido.estado === 'enviado') {
                    btnPreparacion.style.display = 'none';
                    btnEnviado.style.display = 'none';
                } else {
                    // Estado 'pagado'
                    btnPreparacion.style.display = 'inline-block';
                    btnEnviado.style.display = 'inline-block';
                }
            }
        }
    }

    async actualizarEstadoPedido() {
        if (!this.currentOrderDetail) {
            this.showError('No hay pedido seleccionado');
            return;
        }

        const nuevoEstado = document.getElementById('nuevo-estado').value;
        if (!nuevoEstado) {
            this.showError('Selecciona un estado');
            return;
        }

        if (nuevoEstado === this.currentOrderDetail.estado) {
            this.showError('El estado seleccionado es el mismo actual');
            return;
        }

        try {
            this.showLoadingOverlay(true);

            const response = await window.AuthManager.authenticatedFetch(
                `/api/dashboard/pedidos/${this.currentOrderDetail.order_id}/estado/`, 
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        estado: nuevoEstado
                    })
                }
            );

            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showSuccess(`Estado actualizado correctamente: ${data.message}`);
                
                // Actualizar el estado en el detalle actual
                this.currentOrderDetail.estado = nuevoEstado;
                
                // Actualizar la vista del modal
                const estadoBadge = this.getEstadoBadge(nuevoEstado);
                const estadoElement = document.getElementById('detalle-estado-badge');
                estadoElement.innerHTML = `<span class="estado-badge ${estadoBadge}">${nuevoEstado}</span>`;
                
                // Recargar la lista de pedidos para reflejar el cambio
                await this.cargarDatos();
                
            } else {
                throw new Error(data.error || 'Error actualizando estado');
            }

        } catch (error) {
            console.error("❌ Error actualizando estado:", error);
            this.showError(`Error actualizando estado: ${error.message}`);
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    aplicarFiltros() {
        // Actualizar filtros desde los inputs
        this.filtros = {
            estado: document.getElementById('filtro-estado').value,
            metodo_pago: document.getElementById('filtro-metodo').value,
            fecha_desde: document.getElementById('filtro-fecha-desde').value,
            fecha_hasta: document.getElementById('filtro-fecha-hasta').value,
            search: document.getElementById('filtro-buscar').value
        };

        // Recargar datos con nuevos filtros
        this.cargarDatos();
    }

    limpiarFiltros() {
        document.getElementById('filtro-estado').value = '';
        document.getElementById('filtro-metodo').value = '';
        document.getElementById('filtro-fecha-desde').value = '';
        document.getElementById('filtro-fecha-hasta').value = '';
        document.getElementById('filtro-buscar').value = '';
        
        this.aplicarFiltros();
    }

    recargarDatos() {
        this.cargarDatos();
    }

    showDetalleLoading(show) {
        const loading = document.getElementById('loading-detalle');
        const contenido = document.getElementById('contenido-detalle');
        
        if (loading) loading.style.display = show ? 'block' : 'none';
        if (contenido) contenido.style.display = show ? 'none' : 'block';
    }

    showLoading(show) {
        const loading = document.getElementById('loading-pedidos');
        const tabla = document.getElementById('tabla-pedidos');
        const empty = document.getElementById('empty-pedidos');
        
        if (loading) loading.style.display = show ? 'block' : 'none';
        if (tabla && !show) tabla.style.display = this.pedidos.length > 0 ? 'block' : 'none';
        if (empty && !show) empty.style.display = this.pedidos.length === 0 ? 'block' : 'none';
    }

    showLoadingOverlay(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }

    formatCurrency(amount) {
        return `$${Math.round(amount).toLocaleString('es-CL')}`;
    }

    showError(message) {
        console.error('Error:', message);
        // Mostrar error de forma más elegante
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 10000; max-width: 400px;';
        alertDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertDiv);
        
        // Auto-dismiss después de 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    cerrarModal() {
        const modalElement = document.getElementById('modalDetallePedido');
        const backdrop = document.getElementById('modal-backdrop-dashboard');
        
        if (modalElement) {
            modalElement.style.display = 'none';
            modalElement.classList.remove('show');
            modalElement.removeAttribute('aria-modal');
            modalElement.removeAttribute('role');
        }
        
        if (backdrop) {
            backdrop.remove();
        }
        
        document.body.classList.remove('modal-open');
        this.currentOrderDetail = null;
    }

    showSuccess(message) {
        console.log('Success:', message);
        // Mostrar éxito de forma más elegante
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 10000; max-width: 400px;';
        alertDiv.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <strong>Éxito:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertDiv);
        
        // Auto-dismiss después de 3 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }
}

// Funciones globales para los botones
function recargarDatos() {
    if (window.dashboardInstance) {
        window.dashboardInstance.recargarDatos();
    }
}

function limpiarFiltros() {
    if (window.dashboardInstance) {
        window.dashboardInstance.limpiarFiltros();
    }
}

function actualizarEstadoPedido() {
    if (window.dashboardInstance) {
        window.dashboardInstance.actualizarEstadoPedido();
    }
}

// Guardar instancia global para uso en funciones
document.addEventListener("DOMContentLoaded", async function () {
    console.log("🚀 Iniciando Dashboard de Pedidos...");
    
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

    // Inicializar el dashboard
    const dashboard = new DashboardPedidos();
    window.dashboardInstance = dashboard;
    await dashboard.init();
});

// ================================
// Funciones globales para botones de acción
// ================================

async function marcarListoParaRetiro() {
    if (!window.dashboardInstance || !window.dashboardInstance.currentOrderDetail) {
        console.error('No hay pedido seleccionado');
        return;
    }

    const orderId = window.dashboardInstance.currentOrderDetail.order_id;
    await cambiarEstadoPedido(orderId, 'listo_retiro', 'Listo para Retiro');
}

async function confirmarRetiro() {
     if (!window.dashboardInstance || !window.dashboardInstance.currentOrderDetail) {
        console.error('No hay pedido seleccionado');
        return;
     }
    mostrarConfirmacionRetiro();
 }

async function marcarEnPreparacion() {
    if (!window.dashboardInstance || !window.dashboardInstance.currentOrderDetail) {
        console.error('No hay pedido seleccionado');
        return;
    }

    const orderId = window.dashboardInstance.currentOrderDetail.order_id;
    await cambiarEstadoPedido(orderId, 'preparacion', 'En Preparación');
}

async function marcarEnviado() {
    if (!window.dashboardInstance || !window.dashboardInstance.currentOrderDetail) {
        console.error('No hay pedido seleccionado');
        return;
    }

    const orderId = window.dashboardInstance.currentOrderDetail.order_id;
    await cambiarEstadoPedido(orderId, 'enviado', 'Enviado');
}

async function cambiarEstadoPedido(orderId, nuevoEstado, nombreEstado) {
    try {
        window.dashboardInstance.showLoadingOverlay(true);

        const response = await window.AuthManager.authenticatedFetch(
            `/api/dashboard/pedidos/${orderId}/estado/`, 
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    estado: nuevoEstado
                })
            }
        );

        const data = await response.json();

        if (data.success) {
            window.dashboardInstance.showSuccess(`Pedido marcado como: ${nombreEstado}`);
            
            // Actualizar el estado en el modal
            window.dashboardInstance.currentOrderDetail.estado = nuevoEstado;
            document.getElementById('detalle-estado-badge').innerHTML = 
                `<span class="estado-badge estado-${nuevoEstado}">${nombreEstado}</span>`;
            
            // Actualizar selector de estado
            document.getElementById('nuevo-estado').value = nuevoEstado;
            
            // Actualizar botones de acción
            window.dashboardInstance.mostrarBotonesAccion(window.dashboardInstance.currentOrderDetail);
            
            // Recargar lista de pedidos
            await window.dashboardInstance.cargarDatos();
        } else {
            window.dashboardInstance.showError(data.error || 'Error actualizando el estado');
        }

    } catch (error) {
        console.error('❌ Error cambiando estado:', error);
        window.dashboardInstance.showError('Error de conexión al actualizar el estado');
    } finally {
        window.dashboardInstance.showLoadingOverlay(false);
    }
}

// Función global para actualizar estado desde el selector
async function actualizarEstadoPedido() {
    if (window.dashboardInstance) {
        await window.dashboardInstance.actualizarEstadoPedido();
    }
}

// Función global para recargar datos
async function recargarDatos() {
    if (window.dashboardInstance) {
        await window.dashboardInstance.cargarDatos();
        window.dashboardInstance.showSuccess('Datos actualizados');
    }
}

// Función global para limpiar filtros
function limpiarFiltros() {
    if (window.dashboardInstance) {
        window.dashboardInstance.limpiarFiltros();
    }
}

function mostrarConfirmacionRetiro() {
  const t = document.getElementById('toast-confirmacion-retiro');
  if (t) t.style.display = 'block';
}

// Oculta el toast
function cancelarConfirmacionRetiro() {
  const t = document.getElementById('toast-confirmacion-retiro');
  if (t) t.style.display = 'none';
}

// Si el usuario pulsa “Sí”
async function ejecutarConfirmacionRetiro() {
  cancelarConfirmacionRetiro();
  if (!window.dashboardInstance || !window.dashboardInstance.currentOrderDetail) return;
  const orderId = window.dashboardInstance.currentOrderDetail.order_id;
  await cambiarEstadoPedido(orderId, 'retirado', 'Retirado');
}