/**
 * Módulo para manejar la integración con Chilexpress
 * Adaptado del código JavaScript original para trabajar con el backend Django
 */

class ChilexpressManager {
    constructor() {
        this.regionSelect = document.getElementById("region");
        this.comunaSelect = document.getElementById("comuna");
        this.shippingOptions = document.getElementById("shippingOptions");
        this.calcularBtn = document.getElementById("calcularEnvio");
        this.initialized = false;
        
        this.resumen = {
            subtotal: 0,
            iva: 0,
            envio: 0,
            total: 0
        };
        
        // Prevenir múltiples inicializaciones
        if (this.initialized) return;
        
        this.init();
        this.initialized = true;
    }
    
    init() {
        this.cargarRegiones();
        this.setupEventListeners();
    }
    
    async cargarRegiones() {
        try {
            const response = await fetch('/api/chilexpress/regiones/');
            const data = await response.json();
            console.log(data);
            if (data.success) {
                this.regionSelect.innerHTML = '<option value="">Seleccione una región</option>';
                
                data.regiones.forEach(region => {
                    const option = document.createElement("option");
                    option.value = region.regionId;
                    option.textContent = region.regionName;
                    this.regionSelect.appendChild(option);
                });
            } else {
                console.error("Error cargando regiones:", data.error);
                this.mostrarError("No se pudieron cargar las regiones");
            }
        } catch (error) {
            console.error("Error conectando con el servidor:", error);
            this.mostrarError("Error de conexión al cargar regiones");
        }
    }
    
    async cargarComunas(regionId) {
        try {
            this.comunaSelect.innerHTML = '<option value="">Cargando...</option>';
            
            const response = await fetch(`/api/chilexpress/comunas/${regionId}/`);
            const data = await response.json();
            console.log(data);
            if (data.success) {
                this.comunaSelect.innerHTML = '<option value="">Seleccione una comuna</option>';
                
                data.comunas.forEach(comuna => {
                    const option = document.createElement("option");
                    option.value = comuna.countyCode;
                    option.textContent = comuna.coverageName;
                    this.comunaSelect.appendChild(option);
                });
            } else {
                console.error("Error cargando comunas:", data.error);
                this.mostrarError("No se pudieron cargar las comunas");
            }
        } catch (error) {
            console.error("Error conectando con el servidor:", error);
            this.mostrarError("Error de conexión al cargar comunas");
        }
    }
    
   async calcularTarifasEnvio() {
    const comunaDestino = this.comunaSelect.value;
    if (!comunaDestino) {
        this.mostrarError("Seleccione una comuna");
        return;
    }

    try {
        const token = localStorage.getItem("token");
        if (!token) {
            this.mostrarError("Debe iniciar sesión para calcular envío");
            return;
        }

        // OBTENER PRODUCTOS DEL CARRITO DESDE LOCALSTORAGE
        let productos = [];
        try {
            productos = JSON.parse(localStorage.getItem("carrito")) || [];
        } catch (e) {
            productos = [];
        }

        this.shippingOptions.innerHTML = '<p class="text-muted">Calculando opciones de envío...</p>';

        const response = await fetch('/api/chilexpress/calcular-envio/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${token}`
            },
            body: JSON.stringify({
                comuna_destino: comunaDestino,
                productos: productos
            })
        });

        const data = await response.json();
        console.log(data);
        if (data.success) {
            this.mostrarOpcionesEnvio(data.opciones);
            this.resumen.subtotal = data.subtotal;
            this.actualizarResumen();
        } else {
            console.error("Error calculando envío:", data.error);
            this.mostrarError(data.error);
        }

    } catch (error) {
        console.error("Error conectando con el servidor:", error);
        this.mostrarError("Error de conexión al calcular envío");
    }
}
    
    mostrarOpcionesEnvio(opciones) {
        this.shippingOptions.innerHTML = "";
        
        if (opciones && opciones.length > 0) {
            opciones.forEach((opcion, index) => {
                const optionHTML = `
                    <div class="form-check mb-2">
                        <input class="form-check-input opcion-envio" type="radio" name="opcionEnvio" 
                               id="opcion${index}" value="${opcion.precio}">
                        <label class="form-check-label" for="opcion${index}">
                            <strong>${opcion.descripcion}</strong><br>
                            <span class="text-success">${opcion.precio_formateado}</span>
                        </label>
                    </div>
                `;
                this.shippingOptions.insertAdjacentHTML("beforeend", optionHTML);
            });
            
            // Remover listeners existentes para evitar duplicados
            document.querySelectorAll(".opcion-envio").forEach(radio => {
                radio.removeEventListener("change", this.actualizarResumen);
            });
            
            // Agregar nuevos event listeners
            document.querySelectorAll(".opcion-envio").forEach(radio => {
                radio.addEventListener("change", () => this.actualizarResumen());
            });
            
        } else {
            this.shippingOptions.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    No hay opciones de envío disponibles para esta comuna.
                </div>
            `;
        }
    }
    
    mostrarError(mensaje) {
        this.shippingOptions.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i>
                ${mensaje}
            </div>
        `;
    }
    
    actualizarResumen() {
        const envioSeleccionado = document.querySelector("input[name='opcionEnvio']:checked");
        
        this.resumen.envio = envioSeleccionado ? parseInt(envioSeleccionado.value) : 0;
        this.resumen.iva = this.resumen.subtotal * 0.19;
        this.resumen.total = this.resumen.subtotal + this.resumen.iva + this.resumen.envio;
        
        // Actualizar elementos del DOM
        const subtotalEl = document.getElementById("subtotal");
        const totalFinalEl = document.getElementById("totalFinal");
        const impuestosEl = document.getElementById("impuestos");
        const envioEl = document.getElementById("envio");
        
        if (subtotalEl) {
            subtotalEl.textContent = this.formatearPrecio(this.resumen.subtotal);
        }
        if (impuestosEl) {
            impuestosEl.textContent = this.formatearPrecio(this.resumen.iva);
        }
        if (envioEl) {
            envioEl.textContent = this.formatearPrecio(this.resumen.envio);
        }
        if (totalFinalEl) {
            totalFinalEl.textContent = this.formatearPrecio(this.resumen.total);
        }
        
        // Disparar evento personalizado para que otros componentes puedan reaccionar
        document.dispatchEvent(new CustomEvent('resumenActualizado', {
            detail: this.resumen
        }));
    }
    
    formatearPrecio(precio) {
        return precio.toLocaleString("es-CL", { 
            style: "currency", 
            currency: "CLP" 
        });
    }
    
    setupEventListeners() {
        // Cambio de región
        if (this.regionSelect) {
            this.regionSelect.addEventListener("change", () => {
                const regionId = this.regionSelect.value;
                if (regionId) {
                    this.cargarComunas(regionId);
                } else {
                    this.comunaSelect.innerHTML = '<option value="">Primero seleccione una región</option>';
                }
            });
        }
        
        // Botón calcular envío
        if (this.calcularBtn) {
            this.calcularBtn.addEventListener("click", () => {
                this.calcularTarifasEnvio();
            });
        }
        
        // Manejo del tipo de entrega
        const tipoEntregaInputs = document.querySelectorAll("input[name='tipo_entrega']");
        tipoEntregaInputs.forEach(input => {
            input.addEventListener("change", (e) => {
                const envioContainer = document.getElementById("envioContainer");
                
                if (e.target.value === "envio") {
                    // Mostrar formulario de envío
                    if (envioContainer) envioContainer.style.display = "block";
                    // Limpiar opciones de envío anteriores
                    this.shippingOptions.innerHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            Complete los datos de envío y haga clic en "Calcular costo de envío" para ver las opciones disponibles.
                        </div>
                    `;
                    this.resumen.envio = 0;
                    this.actualizarResumen();
                } else if (e.target.value === "retiro") {
                    // Ocultar formulario de envío y mostrar información de retiro
                    if (envioContainer) envioContainer.style.display = "none";
                    this.shippingOptions.innerHTML = `
                        <div class="alert alert-success">
                            <i class="fas fa-store"></i>
                            <strong>Retiro en tienda</strong><br>
                            <div class="mt-2">
                                <strong>Dirección:</strong> Diez de Julio 525, Santiago Centro<br>
                                <strong>Comuna:</strong> Santiago<br>
                                <strong>Horario:</strong> Lunes a Viernes 9:00 - 18:00<br>
                                <strong>Teléfono:</strong> +56 9 1234 5678<br>
                                <small class="text-muted mt-2 d-block">
                                    <i class="fas fa-check-circle text-success"></i> 
                                    Sin costo adicional por retiro
                                </small>
                            </div>
                        </div>
                    `;
                    this.resumen.envio = 0;
                    this.actualizarResumen();
                }
            });
        });
    }
    
    // Método público para obtener el resumen actual
    getResumen() {
        return { ...this.resumen };
    }
    
    // Método público para obtener la opción de envío seleccionada
    getOpcionEnvioSeleccionada() {
        const seleccionada = document.querySelector("input[name='opcionEnvio']:checked");
        if (seleccionada) {
            return {
                precio: parseInt(seleccionada.value),
                descripcion: seleccionada.nextElementSibling.textContent.trim()
            };
        }
        return null;
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
    // Solo inicializar si estamos en la página del carrito y no existe ya
    if (document.getElementById("region") && document.getElementById("comuna") && !window.chilexpressManager) {
        console.log("Inicializando ChilexpressManager...");
        window.chilexpressManager = new ChilexpressManager();
    }
});

// Exportar para uso en otros scripts
window.ChilexpressManager = ChilexpressManager;
