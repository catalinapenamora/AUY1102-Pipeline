// gestion_categorias.js

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

function cargarCategorias() {
  fetch(URL_CATEGORIAS_API, {
    headers: { "Authorization": "Token " + token }
  })
    .then(res => res.json())
    .then(categorias => {
      const tbody = document.getElementById("categorias-lista");
      tbody.innerHTML = '';
      categorias.forEach(c => {
        const fila = `
          <tr>
            <td>${c.nombre}</td>
            <td>${c.descripcion || ''}</td>
            <td>${c.activa ? 'Sí' : 'No'}</td>
            <td>
              <button class="btn-editar me-1" onclick="mostrarFormularioModificar(${c.id})">Modificar</button>
              <button class="btn-eliminar" onclick="eliminarCategoria(${c.id})">Eliminar</button>
            </td>
          </tr>
        `;
        tbody.innerHTML += fila;
      });
    })
    .catch(err => console.error("Error cargando categorías:", err));
}

function mostrarFormularioModificar(id) {
  fetch(`/api/categorias/${id}/`, {
    headers: { "Authorization": "Token " + token }
  })
    .then(res => res.json())
    .then(c => {
      const form = document.getElementById('form-categoria');
      form.dataset.editId = id;

      form.nombre.value = c.nombre;
      form.descripcion.value = c.descripcion;
      form.activa.checked = c.activa;
    })
    .catch(console.error);
}

function limpiarFormulario() {
  const form = document.getElementById('form-categoria');
  form.reset();
  delete form.dataset.editId;
}

document.getElementById('form-categoria').addEventListener('submit', function (e) {
  e.preventDefault();

  const form = e.target;
  const editId = form.dataset.editId;
  const url = editId ? `/api/categorias/${editId}/` : '/api/categorias/';
  const method = editId ? 'PUT' : 'POST';

  const data = {
    nombre: form.nombre.value,
    descripcion: form.descripcion.value,
    activa: form.activa.checked
  };

  fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken,
      'Authorization': 'Token ' + token
    },
    body: JSON.stringify(data)
  })
  .then(res => {
    if (!res.ok) {
      return res.json().then(errorData => {
        console.error("Errores del servidor:", errorData);
        alert('Error al guardar categoría: ' + JSON.stringify(errorData));
        throw new Error('Error en la petición');
      });
    }
    return res.json();
  })
  .then(data => {
    alert(editId ? 'Categoría modificada' : 'Categoría agregada');
    limpiarFormulario();
    cargarCategorias();
  })
  .catch(err => {
    console.error(err);
    alert('Error al guardar categoría');
  });
});

function eliminarCategoria(id) {
  if (!confirm('¿Seguro que quieres eliminar esta categoría?')) return;

  fetch(`/api/categorias/${id}/`, {
    method: 'DELETE',
    headers: {
      'X-CSRFToken': csrftoken,
      'Authorization': 'Token ' + token
    }
  })
  .then(res => {
    if (res.ok) {
      alert('Categoría eliminada');
      cargarCategorias();
    } else {
      alert('Error al eliminar categoría');
    }
  })
  .catch(console.error);
}

document.addEventListener('DOMContentLoaded', cargarCategorias);