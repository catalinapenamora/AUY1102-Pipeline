document.addEventListener("DOMContentLoaded", async function () {
  console.log("🚀 Iniciando carga del perfil...");
  
  // Esperar a que AuthManager esté disponible
  if (typeof window.AuthManager === 'undefined') {
    console.error('AuthManager no está disponible');
    return;
  }

  console.log("✅ AuthManager disponible");

  // Verificar autenticación usando AuthManager
  const isAuthenticated = await window.AuthManager.ensureAuthenticated();
  if (!isAuthenticated) {
    console.log("❌ Usuario no autenticado, redirigiendo...");
    return; // AuthManager maneja la redirección
  }

  console.log("✅ Usuario autenticado, cargando datos del perfil...");

  // Cargar datos del perfil
  await loadProfileData();

  // Configurar evento de logout
  setupLogoutButton();
});

async function loadProfileData() {
  try {
    const response = await window.AuthManager.authenticatedFetch("/api/perfil/");
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Debug: mostrar qué datos llegan
    console.log("🔍 Datos recibidos de la API:", data);
    console.log("🔍 RUT recibido:", data.rut);

    // Llenar los datos del perfil
    const usernameElem = document.getElementById("username");
    const rutElem = document.getElementById("rut");
    const emailElem = document.getElementById("email");

    if (usernameElem) {
      usernameElem.textContent = data.usuario;
      console.log("✅ Username asignado:", data.usuario);
    }
    if (rutElem) {
      rutElem.textContent = data.rut;
      console.log("✅ RUT asignado al elemento:", data.rut);
    }
    if (emailElem) {
      emailElem.textContent = data.email;
      console.log("✅ Email asignado:", data.email);
    }

  } catch (error) {
    console.error("Error al obtener perfil:", error);
    // Si hay error, limpiar autenticación y redirigir
    window.AuthManager.clearAuthentication();
    window.location.href = "/login/";
  }
}

function setupLogoutButton() {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await window.AuthManager.logout();
    });
  }
}