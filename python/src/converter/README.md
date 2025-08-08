# Converter Service

A Python-based service that handles MP4 to MP3 file conversion using FFmpeg, with asynchronous processing via RabbitMQ message queues.

## 🔄 **Purpose**

This service provides:
- **File Conversion** - Convert MP4 video files to MP3 audio files
- **Asynchronous Processing** - Handle conversion jobs via message queues
- **Progress Tracking** - Monitor conversion progress and status
- **Quality Control** - Ensure output quality and file integrity
- **Error Handling** - Robust error handling and retry mechanisms

## 🏗️ **Architecture**

```
┌─────────────────┐
│  Gateway Service│
└─────────┬───────┘
          │ RabbitMQ
          ▼
┌─────────────────┐
│ Converter Service│
│  (Python App)   │
└─────────┬───────┘
          │ FFmpeg
          ▼
┌─────────────────┐
│   File System   │
│  (MP3 Output)   │
└─────────────────┘
```

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
pip install -r requirements.txt

# Install FFmpeg (system dependency)
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### **2. Configure Environment**
```bash
# Copy environment file
cp .env.example .env

# Edit with your settings
nano .env
```

### **3. Run the Service**
```bash
# Development mode
python consumer.py

# Production mode
python -m uvicorn consumer:app --host 0.0.0.0 --port 5002
```

## 📋 **API Endpoints**

### **Conversion Endpoints**

#### **Convert File (Direct)**
```http
POST /convert
Content-Type: application/json

{
  "file_path": "/path/to/video.mp4",
  "output_path": "/path/to/output.mp3",
  "quality": "high",
  "bitrate": "192k"
}
```

**Response:**
```json
{
  "job_id": "job_123456789",
  "status": "processing",
  "progress": 0,
  "estimated_time": "00:05:30"
}
```

#### **Get Conversion Status**
```http
GET /status/{job_id}
```

**Response:**
```json
{
  "job_id": "job_123456789",
  "status": "completed",
  "progress": 100,
  "output_file": "/path/to/output.mp3",
  "file_size": "15.2 MB",
  "duration": "00:05:30",
  "created_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:05:30Z"
}
```

#### **Health Check**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "ffmpeg_version": "4.4.2",
  "active_jobs": 3,
  "completed_jobs": 150,
  "failed_jobs": 2
}
```

## 🔧 **Configuration**

### **Environment Variables**

| Variable | Description | Default |
|----------|-------------|---------|
| `RABBITMQ_HOST` | RabbitMQ host | `localhost` |
| `RABBITMQ_PORT` | RabbitMQ port | `5672` |
| `RABBITMQ_USER` | RabbitMQ username | `guest` |
| `RABBITMQ_PASSWORD` | RabbitMQ password | `guest` |
| `INPUT_DIR` | Input file directory | `./uploads` |
| `OUTPUT_DIR` | Output file directory | `./converted` |
| `TEMP_DIR` | Temporary files directory | `./temp` |
| `MAX_CONCURRENT_JOBS` | Maximum concurrent conversions | `4` |
| `DEFAULT_BITRATE` | Default MP3 bitrate | `192k` |
| `DEFAULT_QUALITY` | Default conversion quality | `high` |
| `FFMPEG_PATH` | FFmpeg executable path | `ffmpeg` |
| `FLASK_ENV` | Flask environment | `development` |
| `FLASK_DEBUG` | Debug mode | `True` |

### **File Structure**

```
converter/
├── uploads/          # Input MP4 files
├── converted/        # Output MP3 files
├── temp/            # Temporary files
├── logs/            # Conversion logs
└── jobs/            # Job metadata
```

## 🧪 **Testing**

### **Run Tests**
```bash
# Run all tests
pytest

# Run specific test categories
pytest test_conversion/
pytest test_queue/
pytest test_ffmpeg/
```

### **Integration Tests**
```bash
# Test with real FFmpeg
pytest integration/

# Test with mocked FFmpeg
pytest unit/
```

## 🐳 **Docker Deployment**

### **Build Image**
```bash
docker build -t converter-service .
```

### **Run Container**
```bash
docker run -p 5002:5002 \
  -e RABBITMQ_HOST=rabbitmq \
  -e RABBITMQ_USER=guest \
  -e RABBITMQ_PASSWORD=guest \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/converted:/app/converted \
  -v $(pwd)/temp:/app/temp \
  converter-service
```

## ☸️ **Kubernetes Deployment**

### **Apply Manifests**
```bash
kubectl apply -f manifests/
```

### **Check Deployment**
```bash
kubectl get pods -l app=converter-service
kubectl get services -l app=converter-service
```

## 🔄 **Message Queue Integration**

### **RabbitMQ Setup**
```python
# Connect to RabbitMQ
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=pika.PlainCredentials(
            RABBITMQ_USER, 
            RABBITMQ_PASSWORD
        )
    )
)
channel = connection.channel()

# Declare queue
channel.queue_declare(queue='conversion_jobs', durable=True)
```

### **Job Processing**
```python
# Process conversion jobs
def process_job(ch, method, properties, body):
    job_data = json.loads(body)
    
    try:
        # Start conversion
        result = convert_mp4_to_mp3(
            job_data['input_file'],
            job_data['output_file'],
            job_data.get('quality', 'high')
        )
        
        # Update job status
        update_job_status(job_data['job_id'], 'completed', result)
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        # Handle errors
        update_job_status(job_data['job_id'], 'failed', str(e))
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
```

## 🔧 **FFmpeg Integration**

### **Conversion Function**
```python
def convert_mp4_to_mp3(input_file, output_file, quality='high'):
    """Convert MP4 file to MP3 using FFmpeg"""
    
    # Quality settings
    quality_settings = {
        'low': {'bitrate': '128k', 'sample_rate': '22050'},
        'medium': {'bitrate': '192k', 'sample_rate': '44100'},
        'high': {'bitrate': '320k', 'sample_rate': '48000'}
    }
    
    settings = quality_settings.get(quality, quality_settings['high'])
    
    # FFmpeg command
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-vn',  # No video
        '-acodec', 'mp3',
        '-ab', settings['bitrate'],
        '-ar', settings['sample_rate'],
        '-y',  # Overwrite output
        output_file
    ]
    
    # Execute conversion
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=3600  # 1 hour timeout
    )
    
    if result.returncode != 0:
        raise ConversionError(f"FFmpeg failed: {result.stderr}")
    
    return {
        'output_file': output_file,
        'file_size': os.path.getsize(output_file),
        'duration': get_audio_duration(output_file)
    }
```

### **Progress Monitoring**
```python
def monitor_conversion(process, job_id):
    """Monitor FFmpeg conversion progress"""
    
    while process.poll() is None:
        # Read FFmpeg output for progress
        output = process.stdout.readline()
        if output:
            progress = parse_ffmpeg_progress(output)
            update_job_progress(job_id, progress)
        
        time.sleep(1)
    
    return process.returncode == 0
```

## 📊 **Monitoring**

### **Health Checks**
```bash
# Service health
curl http://localhost:5002/health

# FFmpeg availability
curl http://localhost:5002/health/ffmpeg

# Queue status
curl http://localhost:5002/health/queue
```

### **Metrics**
```bash
# Conversion statistics
curl http://localhost:5002/metrics

# Job queue status
curl http://localhost:5002/queue/status
```

### **Logs**
```bash
# View application logs
docker logs converter-service

# Kubernetes logs
kubectl logs -f deployment/converter-service

# FFmpeg logs
tail -f logs/conversion.log
```

## 📈 **Performance**

### **Optimizations**
- **Parallel processing** with multiple worker processes
- **Memory management** for large files
- **Disk I/O optimization** with streaming
- **CPU utilization** monitoring and throttling

### **Benchmarks**
- **Small files (<50MB)**: ~30 seconds average
- **Medium files (50-200MB)**: ~2-5 minutes average
- **Large files (>200MB)**: ~5-15 minutes average
- **Concurrent jobs**: Up to 4 simultaneous conversions

### **Resource Requirements**
- **CPU**: 2-4 cores recommended
- **Memory**: 4-8 GB RAM
- **Storage**: SSD recommended for faster I/O
- **Network**: Minimal (local file processing)

## 🚨 **Troubleshooting**

### **Common Issues**

#### **FFmpeg Not Found**
```bash
# Check FFmpeg installation
which ffmpeg

# Verify FFmpeg version
ffmpeg -version

# Install FFmpeg if missing
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
```

#### **File Permission Errors**
```bash
# Check directory permissions
ls -la uploads/
ls -la converted/

# Fix permissions
chmod 755 uploads/ converted/ temp/
chown -R app:app uploads/ converted/ temp/
```

#### **Memory Issues**
```bash
# Check available memory
free -h

# Monitor memory usage
htop

# Adjust concurrent jobs
export MAX_CONCURRENT_JOBS=2
```

#### **Queue Connection Issues**
```bash
# Test RabbitMQ connection
rabbitmq-diagnostics ping

# Check queue status
rabbitmqctl list_queues

# Restart RabbitMQ
sudo systemctl restart rabbitmq-server
```

## 🔒 **Security Features**

### **File Security**
- **Input validation** for file types and sizes
- **Path traversal prevention**
- **Temporary file cleanup**
- **Virus scanning** integration (optional)

### **Process Security**
- **Subprocess isolation** for FFmpeg
- **Resource limits** to prevent abuse
- **Timeout handling** for long conversions
- **Error logging** without sensitive data

## 🔧 **Development**

### **Local Development Setup**
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run linting
flake8 .
black .
isort .
```

### **Testing Strategy**
- **Unit tests** for conversion functions
- **Integration tests** with real FFmpeg
- **Performance tests** for large files
- **Error handling tests** for edge cases

### **Code Style**
- Follow PEP 8 guidelines
- Use type hints for function parameters
- Add comprehensive docstrings
- Maintain high test coverage (>80%)

## 📚 **API Documentation**

### **Swagger UI**
Access the interactive API documentation at:
```
http://localhost:5002/docs
```

### **OpenAPI Specification**
The API specification is available at:
```
http://localhost:5002/swagger.json
```

## 🤝 **Contributing**

1. Follow the existing code structure
2. Add tests for new functionality
3. Test with various file formats and sizes
4. Follow security best practices
5. Document new features and configurations

---

**Part of the MP4 to MP3 Converter Microservices Architecture** 