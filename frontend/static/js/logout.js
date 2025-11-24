document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      try {
        await fetch('/logout/', {
          method: 'GET',
          credentials: 'include'
        });
      } catch (error) {
        console.error("Error cerrando sesión en el backend:", error);
      }
      localStorage.clear();
      window.location.href = "/";
    });
  }
});