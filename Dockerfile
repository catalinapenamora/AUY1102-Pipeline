# Usa una imagen base de Python oficial, ligera y recomendada (slim)
FROM python:3.9-slim

# 1. Instalar herramientas de compilación para dependencias (clave en ambientes slim)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    # Limpia el caché después de la instalación
    && rm -rf /var/lib/apt/lists/*

# Establece variables de entorno y directorio de trabajo
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/app

# 2. Copia e instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copia el resto del código
COPY . .

# 4. Expone el puerto por defecto de Django
EXPOSE 8000

# 5. Comando de inicio (usando runserver como en tu prueba local)
CMD ["python", "backend/manage.py", "runserver", "0.0.0.0:8000"]
