const API_BASE = window.location.origin; // http://localhost:8000

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("login-form");

  if (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();

      const email = document.querySelector('input[name="username"]').value.trim();
      const password = document.querySelector('input[name="password"]').value;

      if (!email || !password) {
        alert("Por favor, completa todos los campos.");
        return;
      }

      try {
        const response = await fetch(`${API_BASE}/api/login/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
          },
          body: JSON.stringify({
            usuario: email,
            contraseña: password
          })
        });

        const data = await response.json();

        if (response.ok && data.token) {
          localStorage.setItem("token", data.token);

          // Espera breve para que el token quede bien guardado
          setTimeout(() => {
            window.location.href = "/";
          }, 300);
        } else {
          alert(data.error || "Credenciales incorrectas.");
        }
      } catch (error) {
        console.error("Error en login:", error);
        alert("Hubo un problema al intentar iniciar sesión.");
      }
    });
  }
});