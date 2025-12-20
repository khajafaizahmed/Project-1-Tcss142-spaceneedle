FROM python:3.11-slim

# Install Java
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk && \
    apt-get clean

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flask

ENV PORT=8080

CMD ["python", "server.py"]
