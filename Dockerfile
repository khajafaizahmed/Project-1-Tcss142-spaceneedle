FROM python:3.11-slim

# Install Java (headless is correct for servers)
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk-headless && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install flask

ENV PORT=8080

CMD ["python", "server.py"]
