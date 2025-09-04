# MP4 to MP3 Conversion System

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![MongoDB](https://img.shields.io/badge/database-mongodb-green)
![MySQL](https://img.shields.io/badge/database-mysql-orange)
![RabbitMQ](https://img.shields.io/badge/messaging-rabbitmq-red)
![Flask](https://img.shields.io/badge/framework-flask-lightgrey)
![Prometheus](https://img.shields.io/badge/monitoring-prometheus-orange)
![Swagger](https://img.shields.io/badge/docs-swagger-brightgreen)

This project converts uploaded video files to MP3 using a microservices architecture:

- **API Gateway (Flask)**: login, upload, download
- **Auth Service (Flask + MySQL)**: login and token validation
- **Converter (Worker)**: consumes RabbitMQ jobs, writes MP3 to MongoDB
- **Notification (Worker)**: consumes MP3 jobs, notifies users
- **RabbitMQ**: inter-service messaging
- **MongoDB (GridFS)**: binary storage for videos and mp3s

![ConverterDiagram](public/ConverterDiagram.png)

---

### High-level flow

1. Client logs in via Gateway and gets a token from Auth.
2. Client uploads a video to Gateway; video is stored in MongoDB GridFS and a message is queued.
3. Converter consumes the message, produces an MP3, stores it in MongoDB, and publishes a notification message.
4. Client downloads the MP3 via Gateway.

---

## Quick start (local, without Kubernetes)

**Prerequisites**: Docker, Python 3.9+, MongoDB, RabbitMQ, MySQL (for auth).

### 1) Start infra services

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
docker run -d --name mongo -p 27017:27017 mongo:6
docker run -d --name mysql -e MYSQL_ROOT_PASSWORD=root -p 3306:3306 mysql:8
```

````

### 2) Configure environment

Set at least these variables when running services:

```bash
export AUTH_SVC_ADDRESS=localhost:5000
export VIDEO_QUEUE=video
export MP3_QUEUE=mp3
```

### 3) Run services from the `python/src` tree

```bash
# Terminal 1: Auth service
cd python/src/auth
pip install -r requirements.txt
python server.py

# Terminal 2: Gateway
cd python/src/gateway
pip install -r requirements.txt
python server.py

# Terminal 3: Converter worker
cd python/src/converter
pip install -r requirements.txt
python consumer.py

# Terminal 4: Notification worker
cd python/src/notification
pip install -r requirements.txt
python consumer.py
```

### 4) Basic usage

> A sample video file is provided at **`python/src/files/test.mp4`** to test the workflow.

```bash
# Login (basic auth), receive a token
curl -u user@example.com:password -X POST http://localhost:8080/login

# Upload a video (using the provided test file)
curl -X POST http://localhost:8080/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@python/src/files/test.mp4"

# Download an mp3 by id (admin token required)
curl -L -X GET "http://localhost:8080/download?fid=<OBJECT_ID>" \
  -H "Authorization: Bearer <TOKEN>" -o output.mp3
```

---

## Configuration reference

- Gateway MongoDB URIs: `mongodb://host.minikube.internal:27017/videos`, `mongodb://host.minikube.internal:27017/mp3s`
- RabbitMQ host: `rabbitmq`
- Queues: `VIDEO_QUEUE=video`, `MP3_QUEUE=mp3`
- Auth env: `AUTH_SVC_ADDRESS=<host:port>`

---

### Metrics

- Gateway exposes Prometheus metrics at `GET /metrics` (port 8080 by default). Metrics include `http_requests_total` and `http_request_duration_seconds` histograms.
- Converter and Notification workers expose metrics via `prometheus_client.start_http_server` on `METRICS_PORT` (default 9100).
- Add `prometheus.io/scrape: "true"`, `prometheus.io/port: "8080"` (or `9100` for workers) and `prometheus.io/path: "/metrics"` annotations to scrape in Kubernetes.

**Grafana panel examples (PromQL):**

- Requests per second:

  ```promql
  sum(rate(http_requests_total[5m]))
  ```

- Error rate:

  ```promql
  sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
  ```

- P95 latency:

  ```promql
  histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
  ```

- Converter success/error:

  ```promql
  sum(rate(converter_jobs_total{result="success"}[5m]))
  sum(rate(converter_jobs_total{result="error"}[5m]))
  ```

---

## Kubernetes (optional)

Kubernetes manifests are under each service `manifests/`. With a registry available:

```bash
docker build -t <registry>/auth:latest python/src/auth
docker build -t <registry>/gateway:latest python/src/gateway
docker build -t <registry>/converter:latest python/src/converter
docker build -t <registry>/notification:latest python/src/notification
```

Apply manifests per service in your cluster. Ensure DNS for `rabbitmq` and Mongo endpoints resolves inside the cluster, and that `AUTH_SVC_ADDRESS` is set to the auth service ClusterIP\:Port.
````

Interactive API documentation is available via **Swagger UI**: `http://localhost:5000/apidocs/`
