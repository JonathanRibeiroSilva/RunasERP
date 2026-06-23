FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME ["/app/output"]

ENTRYPOINT ["python", "main.py"]
CMD ["--all"]
