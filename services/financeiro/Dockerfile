# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .

EXPOSE 8005

# No --reload: this is the production image. The dev stack overrides the
# command with its own --reload in docker-compose.dev.yml.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
