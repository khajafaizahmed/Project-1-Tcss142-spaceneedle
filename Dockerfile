FROM python:3.11-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flask

ENV PORT=8080

CMD ["python", "server.py"]
