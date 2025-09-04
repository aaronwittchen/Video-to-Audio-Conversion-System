# Video to Audio Conversion System

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![MongoDB](https://img.shields.io/badge/database-mongodb-green)
![MySQL](https://img.shields.io/badge/database-mysql-orange)
![RabbitMQ](https://img.shields.io/badge/messaging-rabbitmq-red)
![Flask](https://img.shields.io/badge/framework-flask-lightgrey)
![Prometheus](https://img.shields.io/badge/monitoring-prometheus-orange)
![Swagger](https://img.shields.io/badge/docs-swagger-brightgreen)

This project converts uploaded video files to MP3 using a microservices architecture:

> [!IMPORTANT]
> Active development in progress!

- **API Gateway (Flask)**: login, upload, download
- **Auth Service (Flask + MySQL)**: login and token validation
- **Converter (Worker)**: consumes RabbitMQ jobs, writes MP3 to MongoDB
- **Notification (Worker)**: consumes MP3 jobs, notifies users
- **RabbitMQ**: inter-service messaging
- **MongoDB (GridFS)**: binary storage for videos and mp3s

![ConverterDiagram](public/ConverterDiagram.png)

### Core Services

- **API Gateway (Flask)**: Entry point for all client requests, handles authentication, uploads, and downloads
- **Auth Service (Flask + MySQL)**: Manages user authentication and JWT token validation
- **Converter Service**: Processes video files asynchronously via RabbitMQ messages
- **Notification Service**: Sends email notifications upon conversion completion
- **RabbitMQ**: Message broker for inter-service communication
- **MongoDB (GridFS)**: Distributed file storage for videos and MP3s
- **Prometheus + Grafana**: Monitoring and metrics collection

## Microservice Architecture and Distributed Systems

This project implements a robust microservice architecture to convert video files to MP3 format, utilizing:

- **Python** for service implementation
- **RabbitMQ** for asynchronous message queuing
- **MongoDB** with GridFS for binary file storage
- **Docker** for containerization
- **Kubernetes** for orchestration
- **MySQL** for user authentication data

### MP4 to MP3 Conversion Flow

1. **Upload & Authentication**
   - User authenticates and receives a JWT token
   - Uploaded video is received by the API Gateway
   - Video is stored in MongoDB GridFS
   - A message is published to RabbitMQ for processing

2. **Asynchronous Processing**
   - Converter service consumes the message from the queue
   - Video is processed and converted to MP3 format
   - MP3 is stored back in MongoDB
   - Completion notification is published to RabbitMQ

3. **Notification & Download**
   - Notification service sends an email with download link
   - User can download the MP3 using their JWT token

## Authentication & Security

### JWT Authentication Flow

1. User submits credentials to `/login` endpoint
2. Auth Service validates against MySQL database
3. On success, a signed JWT is issued
4. Client includes JWT in `Authorization: Bearer <token>` header for subsequent requests

### JWT Structure
- **Header**: Contains token type and signing algorithm
- **Payload**: Contains claims (user info, permissions)
- **Signature**: Ensures token integrity

## Communication Patterns

### Synchronous Communication
- Used between Gateway and Auth Service
- Blocking requests with immediate responses
- Ensures strong consistency

### Asynchronous Communication
- Used for video processing via RabbitMQ
- Non-blocking, improves scalability
- Implements eventual consistency

## Data Storage

### MongoDB GridFS
- Handles files larger than 16MB (MongoDB document limit)
- Automatically chunks large files
- Stores metadata and file chunks in separate collections

### MySQL
- Stores user credentials and authentication data
- Provides ACID compliance for user management

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- Kubernetes (for production deployment)

### Local Development

1. Start infrastructure services:
   ```bash
   docker-compose up -d rabbitmq mongodb mysql
   ```

2. Set up environment variables (see `.env.example`)

3. Start the services:
   ```bash
   # Start auth service
   python -m src.auth.server
   
   # Start gateway
   python -m src.gateway.server
   
   # Start converter worker
   python -m src.converter.consumer
   
   # Start notification worker
   python -m src.notification.consumer
   ```

## Monitoring

- **Prometheus**: Metrics collection at `http://localhost:9090`
- **Grafana**: Visualization at `http://localhost:3000`
- **RabbitMQ Management**: `http://localhost:15672`

## API Documentation

Once services are running, access the interactive API documentation at `http://localhost:8080/docs`

## License

MIT

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
