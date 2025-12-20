FROM python:3.11-slim-bookworm

# Install Java 17 (available on bookworm)
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install flask

ENV PORT=8080

CMD ["python", "server.py"]
