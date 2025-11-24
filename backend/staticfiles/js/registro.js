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

document.getElementById("register-form").addEventListener("submit", async function(e) {
  e.preventDefault();

  const mensajeError = document.getElementById("mensaje-error");
  mensajeError.style.display = "none";
  mensajeError.textContent = "";

  const username = document.querySelector('input[name="username"]').value.trim();
  const email = document.querySelector('input[name="email"]').value.trim();
  const rut = document.querySelector('input[name="rut"]').value;
  const password = document.querySelector('input[name="password"]').value;
  const passwordConfirm = document.querySelector('input[name="password_confirm"]').value;

  if (password !== passwordConfirm) {
    mensajeError.textContent = "Las contraseñas no coinciden.";
    mensajeError.style.display = "block";
    return;
  }

  const hasUppercase = /[A-Z]/.test(password);
  const hasSymbol = /[!@#$%^&*(),.?":{}|<>]/.test(password);

  if (!hasUppercase || !hasSymbol) {
    mensajeError.textContent = "La contraseña debe contener al menos una letra mayúscula y un símbolo.";
    mensajeError.style.display = "block";
    return;
  }

  const csrftoken = getCookie('csrftoken');

  try {
    const response = await fetch("/api/registro/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken
      },
      body: JSON.stringify({
        usuario: username,
        rut: rut,
        email: email,
        contraseña: password,
        contraseña_confirm: passwordConfirm
      })
    });

    const data = await response.json();

    if (response.ok) {
      const token = data.token;
      localStorage.setItem("token", token);

      // 🔄 Crear trabajador a través del endpoint admin
      const perfilResponse = await fetch("/api/perfil/", {
        headers: { "Authorization": `Token ${token}` }
      });
      const perfil = await perfilResponse.json();

      const userId = perfil.id ?? perfil.user_id ?? null;

      if (userId) {
        await fetch(`/api/admin/trabajadores/${userId}/`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Token ${token}`,
            "X-CSRFToken": csrftoken
          },
          body: JSON.stringify({
            trabajador: true
          })
        });
      }

      window.location.href = "/";
    } else {
      mensajeError.textContent = data.error || "Error desconocido";
      mensajeError.style.display = "block";
    }

  } catch (error) {
    console.error("Error en el registro:", error);
    mensajeError.textContent = "Error en el servidor";
    mensajeError.style.display = "block";
  }
});
