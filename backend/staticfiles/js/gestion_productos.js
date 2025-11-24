
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');
const token = localStorage.getItem("token");
if (!token) {
  window.location.href = "/login/";
}

function formatearCLP(valor) {
  return `$${Math.round(valor).toLocaleString('es-CL')}`;
}

function cargarProductos() {
  fetch('/api/productos/', {
    headers: {
      "Authorization": "Token " + token
    }
  })
    .then(res => res.json())
    .then(data => {
      // Manejar el formato paginado de la API
      const productos = data.productos || data; // Compatibilidad con ambos formatos
      const tbody = document.getElementById("productos-lista");
      tbody.innerHTML = '';
      
      if (!productos || productos.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="9" class="text-center py-4">
              <i class="fas fa-box-open fa-3x text-muted mb-3"></i>
              <p class="text-muted">No hay productos registrados</p>
            </td>
          </tr>
        `;
        return;
      }
      
      productos.forEach(p => {
        const fila = `
          <tr>
            <td class="product-name">${p.nombre}</td>
            <td class="product-description">${p.descripcion}</td>
            <td class="product-price">${formatearCLP(p.precio)}</td>
            <td class="product-price-wholesale">${formatearCLP(p.precio_mayorista)}</td>
            <td class="product-stock">${p.stock}</td>
            <td class="product-weight">${p.peso} kg</td>
            <td class="product-dimensions">${p.largo} × ${p.ancho} × ${p.alto} cm</td>
            <td class="product-image">
              ${p.imagen ? `<img src="${p.imagen}" alt="${p.nombre}" class="product-thumbnail">` : '<span class="text-muted">Sin imagen</span>'}
            </td>
            <td class="product-actions">
              <button class="btn btn-outline-primary btn-sm me-1" onclick="mostrarFormularioModificar(${p.id})" title="Editar">
                <i class="fas fa-edit"></i>
              </button>
              <button class="btn btn-outline-danger btn-sm" onclick="eliminarProducto(${p.id})" title="Eliminar">
                <i class="fas fa-trash"></i>
              </button>
            </td>
          </tr>
        `;
        tbody.innerHTML += fila;
      });
    })
    .catch(err => {
      console.error("Error cargando productos:", err);
      const tbody = document.getElementById("productos-lista");
      tbody.innerHTML = `
        <tr>
          <td colspan="9" class="text-center py-4 text-danger">
            <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
            <p>Error al cargar productos. Por favor, recarga la página.</p>
          </td>
        </tr>
      `;
    });
}

function mostrarFormularioModificar(id) {
  fetch(`/api/productos/${id}/`, {
    headers: {
      "Authorization": "Token " + token
    }
  })
    .then(res => res.json())
    .then(p => {
      const form = document.getElementById('form-producto');
      form.dataset.editId = id;  

      form.nombre.value = p.nombre;
      form.precio.value = p.precio;
      form.precio_mayorista.value = p.precio_mayorista;
      form.descripcion.value = p.descripcion;
      form.stock.value = p.stock;
      form.categoria.value = p.categoria; 
      form.peso.value = p.peso;
      form.largo.value = p.largo;
      form.ancho.value = p.ancho;
      form.alto.value = p.alto;
    })
    .catch(console.error);
}

function limpiarFormulario() {
  const form = document.getElementById('form-producto');
  form.reset();
  delete form.dataset.editId;
}

document.getElementById('form-producto').addEventListener('submit', function (e) {
  e.preventDefault();

  const form = e.target;
  const editId = form.dataset.editId;
  const url = editId ? `/api/productos/${editId}/` : '/api/productos/';
  const method = editId ? 'PUT' : 'POST';

  const formData = new FormData(form);

  // Mostrar indicador de carga
  const btnSubmit = form.querySelector('button[type="submit"]');
  const originalText = btnSubmit.innerHTML;
  btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Guardando...';
  btnSubmit.disabled = true;

  fetch(url, {
    method,
    headers: {
      'X-CSRFToken': csrftoken,
      'Authorization': 'Token ' + token
    },
    body: formData,
  })
  .then(res => {
    if (!res.ok) {
      return res.json().then(errorData => {
        console.error("Errores del servidor:", errorData);
        throw new Error(JSON.stringify(errorData));
      });
    }
    return res.json();
  })
  .then(data => {
    mostrarNotificacion(
      editId ? 'Producto actualizado exitosamente' : 'Producto agregado exitosamente',
      'success'
    );
    limpiarFormulario();
    cargarProductos();
  })
  .catch(err => {
    console.error(err);
    mostrarNotificacion('Error al guardar el producto. Revisa los datos e intenta nuevamente.', 'error');
  })
  .finally(() => {
    // Restaurar botón
    btnSubmit.innerHTML = originalText;
    btnSubmit.disabled = false;
  });
});

function eliminarProducto(id) {
  if (!confirm('¿Estás seguro de que quieres eliminar este producto?\n\nEsta acción no se puede deshacer.')) return;

  fetch(`/api/productos/${id}/`, {
    method: 'DELETE',
    headers: {
      'X-CSRFToken': csrftoken,
      'Authorization': 'Token ' + token
    }
  })
  .then(res => {
    if (res.ok) {
      mostrarNotificacion('Producto eliminado exitosamente', 'success');
      cargarProductos();
    } else {
      throw new Error('Error del servidor');
    }
  })
  .catch(err => {
    console.error(err);
    mostrarNotificacion('Error al eliminar el producto', 'error');
  });
}

function mostrarNotificacion(mensaje, tipo = 'success') {
  const notif = document.createElement('div');
  notif.className = `alert alert-${tipo === 'error' ? 'danger' : 'success'} alert-dismissible fade show position-fixed`;
  notif.style.top = '130px';
  notif.style.right = '20px';
  notif.style.zIndex = '10000';
  notif.style.minWidth = '300px';
  notif.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
  notif.style.fontWeight = '600';
  
  notif.innerHTML = `
    <i class="fas fa-${tipo === 'error' ? 'exclamation-triangle' : 'check-circle'} me-2"></i>
    ${mensaje}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  document.body.appendChild(notif);

  // Auto-remover después de 5 segundos
  setTimeout(() => {
    if (notif.parentNode) {
      notif.remove();
    }
  }, 5000);
}

document.addEventListener('DOMContentLoaded', cargarProductos);
