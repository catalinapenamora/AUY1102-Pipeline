FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi:application"]

# Si gunicorn NO está en requirements.txt, usa el comando de desarrollo:
# CMD ["python", "backend/manage.py", "runserver", "0.0.0.0:8000"]
