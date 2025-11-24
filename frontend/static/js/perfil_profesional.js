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
            // No mostrar error visual para no asustar al usuario
            // Solo log en consola para debugging
        }
    }

    async loadProfileData() {
        try {
            console.log("📋 Cargando datos del perfil...");
            const response = await window.AuthManager.authenticatedFetch("/api/perfil/");
            
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log("📋 Datos del perfil recibidos:", data);
            
            // Actualizar información personal
            this.updatePersonalInfo(data);
            
            return data;
        } catch (error) {
            console.error("❌ Error cargando perfil:", error);
            // Mostrar información básica aunque falle la carga del perfil
            this.updatePersonalInfo({
                usuario: "Usuario",
                email: "No disponible",
                rut: "No disponible",
                is_staff: false,
                is_trabajador: false,
                is_empresa: false
            });
            // No lanzar el error para que continúe cargando el historial
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
        // Información personal en la nueva estructura
        const infoElements = {
            'info-nombre': data.first_name && data.last_name ? 
                         `${data.first_name} ${data.last_name}` : 
                         data.usuario || 'Usuario',
            'info-rut': data.rut || 'Sin especificar',
            'info-email': data.email || 'No disponible'
        };

        Object.entries(infoElements).forEach(([id, value]) => {
            const elem = document.getElementById(id);
            if (elem) {
                elem.textContent = value;
            }
        });

        // Actualizar badge de rol
        const roleElem = document.getElementById("perfil-role");
        if (roleElem) {
            let role = "Cliente";
            let badgeColor = "#003049"; // Color secundario de la empresa
            
            if (data.is_staff) {
                role = "Administrador";
                badgeColor = "#780000"; // Color principal de la empresa
            } else if (data.is_trabajador) {
                role = "Trabajador";
                badgeColor = "#dc3545"; // Rojo para trabajador
            } else if (data.is_empresa) {
                role = "Empresa";
                badgeColor = "#28a745"; // Verde para empresa
            }
            
            roleElem.textContent = role;
            roleElem.style.backgroundColor = badgeColor;
            roleElem.style.color = "white";
        }
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
            
            // Mostrar pedidos
            this.renderPedidos();
            
            // Ocultar loading
            this.showLoading(false);
            
        } catch (error) {
            console.error("❌ Error cargando historial:", error);
            this.showLoading(false);
            this.showEmptyState();
            
            // Solo mostrar error si es un error grave, no si simplemente no hay pedidos
            if (error.message && !error.message.includes('404')) {
                this.showError("Hubo un problema cargando el historial de pedidos");
            }
        }
    }

    renderPedidos() {
        const container = document.getElementById("historial-pedidos");
        const emptyState = document.getElementById("empty-historial");
        const tbody = document.getElementById("tbody-pedidos");
        
        if (!container || !tbody) return;

        if (this.filteredPedidos.length === 0) {
            container.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        // Ocultar estado vacío y mostrar tabla
        if (emptyState) emptyState.style.display = 'none';
        container.style.display = 'block';
        
        // Generar filas de la tabla
        tbody.innerHTML = this.filteredPedidos.map(pedido => 
            this.createPedidoRow(pedido)
        ).join('');
        
        // Agregar event listeners
        this.setupPedidoEvents();
    }

    createPedidoRow(pedido) {
        const estadoBadge = this.getEstadoBadge(pedido.estado);
        
        return `
            <tr>
                <td>
                    <strong>#${pedido.order_id}</strong>
                </td>
                <td>
                    <small class="text-muted">${pedido.fecha}</small>
                </td>
                <td>
                    <span class="badge ${estadoBadge}">${pedido.estado}</span>
                </td>
                <td>
                    <strong>${this.formatCurrency(pedido.monto)}</strong>
                </td>
                <td>
                    <small class="text-muted">${pedido.tipo_entrega}</small>
                    ${pedido.total_productos ? `<br><small class="text-muted">(${pedido.total_productos} productos)</small>` : ''}
                </td>
                <td>
                    <button type="button" class="btn btn-sm btn-outline-primary ver-pedido-btn" 
                            data-order-id="${pedido.order_id}" 
                            title="Ver detalles del pedido">
                        <i class="fas fa-eye"></i> Ver
                    </button>
                </td>
            </tr>
        `;
    }

    getEstadoBadge(estado) {
        const badges = {
            'pagado': 'text-white',
            'pendiente': 'text-dark',
            'fallido': 'text-white',
            'cancelado': 'text-white'
        };
        
        const colors = {
            'pagado': '#28a745',
            'pendiente': '#ffc107', 
            'fallido': '#dc3545',
            'cancelado': '#6c757d'
        };
        
        const textClass = badges[estado] || 'text-white';
        const bgColor = colors[estado] || '#6c757d';
        
        return `${textClass}" style="background-color: ${bgColor}`;
    }

    setupPedidoEvents() {
        // Event listeners para botones "ver"
        document.querySelectorAll('.ver-pedido-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const orderId = btn.getAttribute('data-order-id');
                await this.verDetallePedido(orderId);
            });
        });
        
        console.log("✅ Eventos de pedidos configurados");
    }

    setupEventListeners() {
        // Botón de logout
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async () => {
                await window.AuthManager.logout();
            });
        }
        
        // Event listeners para cerrar el modal
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

    getEstadoClass(estado) {
        const estados = {
            'pagado': 'completado',
            'pendiente': 'pendiente',
            'fallido': 'cancelado',
            'cancelado': 'cancelado'
        };
        return estados[estado] || 'pendiente';
    }

    formatCurrency(amount) {
        return `$${Math.round(amount).toLocaleString('es-CL')}`;
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
            backdrop.id = 'modal-backdrop-temp';
            document.body.appendChild(backdrop);
            document.body.classList.add('modal-open');
            
            this.showDetalleLoading(true);
            
            // Hacer petición al API
            const response = await window.AuthManager.authenticatedFetch(`/api/detalle-pedido/${orderId}/`);
            
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log("📦 Detalles del pedido recibidos:", data);
            
            if (data.success) {
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
            estadoElement.innerHTML = `<span class="badge ${estadoBadge}">${pedido.estado}</span>`;
            
            // Información de entrega
            if (pedido.direccion_completa) {
                const direccionDiv = document.getElementById('detalle-direccion');
                const direccionCompleta = document.getElementById('detalle-direccion-completa');
                
                direccionDiv.style.display = 'block';
                direccionCompleta.textContent = `${pedido.direccion_completa.direccion}, ${pedido.direccion_completa.comuna}, ${pedido.direccion_completa.region}`;
            }
            
            // Información de envío
            if (pedido.envio && pedido.envio.ot_codigo) {
                const envioDiv = document.getElementById('detalle-envio');
                const otCodigo = document.getElementById('detalle-ot-codigo');
                
                envioDiv.style.display = 'block';
                otCodigo.textContent = pedido.envio.ot_codigo || 'En proceso';
            }
            
            // Información de transferencia bancaria (si aplica)
            if (pedido.transferencia) {
                const transferenciaDiv = document.getElementById('detalle-transferencia');
                if (transferenciaDiv) {
                    transferenciaDiv.style.display = 'block';
                    
                    // Rellenar datos de transferencia
                    document.getElementById('transferencia-banco').textContent = pedido.transferencia.banco;
                    document.getElementById('transferencia-tipo-cuenta').textContent = pedido.transferencia.tipo_cuenta;
                    document.getElementById('transferencia-numero-cuenta').textContent = pedido.transferencia.numero_cuenta;
                    document.getElementById('transferencia-titular').textContent = pedido.transferencia.titular;
                    document.getElementById('transferencia-rut-titular').textContent = pedido.transferencia.rut_titular;
                    document.getElementById('transferencia-monto').textContent = this.formatCurrency(pedido.transferencia.monto);
                    document.getElementById('transferencia-order-id').textContent = pedido.transferencia.order_id;
                    document.getElementById('transferencia-email').textContent = pedido.transferencia.email_confirmacion;
                }
            } else {
                const transferenciaDiv = document.getElementById('detalle-transferencia');
                if (transferenciaDiv) {
                    transferenciaDiv.style.display = 'none';
                }
            }
            
            // Productos
            const productosContainer = document.getElementById('detalle-productos');
            let totalProductos = 0;
            
            if (pedido.productos && pedido.productos.length > 0) {
                productosContainer.innerHTML = pedido.productos.map(producto => {
                    const subtotal = producto.subtotal || (producto.precio_unitario * producto.cantidad);
                    totalProductos += subtotal;
                    
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
                
                // Calcular desglose de IVA
                // Los precios ya vienen con IVA incluido, así que calculamos hacia atrás
                const subtotalSinIva = Math.round(totalProductos / 1.19);
                const iva = totalProductos - subtotalSinIva;
                
                // Actualizar elementos del desglose
                const subtotalSinIvaElem = document.getElementById('detalle-subtotal-sin-iva');
                const ivaElem = document.getElementById('detalle-iva');
                const totalFinalElem = document.getElementById('detalle-total-final');
                
                if (subtotalSinIvaElem) subtotalSinIvaElem.textContent = this.formatCurrency(subtotalSinIva);
                if (ivaElem) ivaElem.textContent = this.formatCurrency(iva);
                if (totalFinalElem) totalFinalElem.textContent = this.formatCurrency(totalProductos);
                
            } else {
                productosContainer.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center text-muted">
                            <i class="fas fa-exclamation-triangle"></i> No se encontraron productos
                        </td>
                    </tr>
                `;
                
                // Limpiar desglose si no hay productos
                const subtotalSinIvaElem = document.getElementById('detalle-subtotal-sin-iva');
                const ivaElem = document.getElementById('detalle-iva');
                const totalFinalElem = document.getElementById('detalle-total-final');
                
                if (subtotalSinIvaElem) subtotalSinIvaElem.textContent = this.formatCurrency(0);
                if (ivaElem) ivaElem.textContent = this.formatCurrency(0);
                if (totalFinalElem) totalFinalElem.textContent = this.formatCurrency(0);
            }
            
            // Ocultar loading y mostrar contenido
            this.showDetalleLoading(false);
            
        } catch (error) {
            console.error("❌ Error mostrando detalles del pedido:", error);
            this.showError('Error mostrando los detalles del pedido');
        }
    }

    showDetalleLoading(show) {
        const loading = document.getElementById('loading-detalle');
        const contenido = document.getElementById('contenido-detalle');
        
        if (loading) loading.style.display = show ? 'block' : 'none';
        if (contenido) contenido.style.display = show ? 'none' : 'block';
    }

    cerrarModal() {
        const modalElement = document.getElementById('modalDetallePedido');
        const backdrop = document.getElementById('modal-backdrop-temp');
        
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
    }

    showLoading(show) {
        const loading = document.getElementById('loading-historial');
        const historial = document.getElementById('historial-pedidos');
        
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
        }
        if (historial) {
            historial.style.display = show ? 'none' : 'block';
        }
    }

    showError(message) {
        console.error('Error:', message);
        // Mostrar error de forma más elegante
        const container = document.querySelector('.container');
        if (container) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-warning alert-dismissible fade show mt-3';
            alertDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <strong>Aviso:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-dismiss después de 5 segundos
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }

    showEmptyState() {
        const container = document.getElementById("historial-pedidos");
        const emptyState = document.getElementById("empty-historial");
        
        if (container) container.style.display = 'none';
        if (emptyState) emptyState.style.display = 'block';
    }
}
