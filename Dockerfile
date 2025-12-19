# Backend Dockerfile

# Usamos una imagen de Python ligera
FROM python:3.11-slim

# Evitar archivos basura de python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalación de dependencias de sistema (WeasyPrint + Herramientas de compilación)
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libgobject-2.0-0 \
    gcc \
    libpq-dev \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . /app/

# Exponer el puerto
EXPOSE 8003

# Comando de arranque
CMD ["python", "manage.py", "runserver", "0.0.0.0:8003"]