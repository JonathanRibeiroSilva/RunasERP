# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Dependências de sistema — layer separada, muda raramente
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python com cache do BuildKit
# Esta layer só é invalidada quando requirements.txt muda
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Código copiado por último — em dev é sobrescrito pelo volume
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
