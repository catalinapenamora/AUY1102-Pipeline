/**
 * Perfil - Funcionalidad específica del perfil de usuario
 * Usa el AuthManager centralizado para autenticación
 */

document.addEventListener("DOMContentLoaded", async function () {
  // Usar AuthManager para autenticación
  const token = await window.authManager.asegurarToken();
  if (!token) return;

  try {
    // Usar AuthManager para obtener perfil
    const data = await window.authManager.obtenerPerfil(token);
    if (!data) return;

    // Asegurarse de que los elementos existen antes de intentar llenarlos
    const usernameElem = document.getElementById("username");
    const emailElem = document.getElementById("email");

    if (usernameElem) usernameElem.textContent = data.usuario;
    if (emailElem) emailElem.textContent = data.email;

  } catch (error) {
    console.error("Error al obtener perfil:", error);
    window.authManager.limpiarYRedirigir();
  }

  // Evento para cerrar sesión usando AuthManager
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await window.authManager.cerrarSesion();
    });
  }
});
