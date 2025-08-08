import os
import gridfs
import pika
import json
import logging
from contextlib import contextmanager
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pymongo.errors import PyMongoError
from auth import validate
from storage import util  
from auth_service import access

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Flask(__name__)

# Configuration
server.config["MONGO_URI"] = os.getenv(
    "MONGO_URI", 
    "mongodb://host.minikube.internal:27017/videos"
)
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

# Initialize MongoDB
try:
    mongo = PyMongo(server)
    fs = gridfs.GridFS(mongo.db)
    logger.info("MongoDB connection initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MongoDB: {e}")
    raise

# RabbitMQ connection management
@contextmanager
def get_rabbitmq_channel():
    """Context manager for RabbitMQ connections to ensure proper cleanup"""
    connection = None
    channel = None
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                heartbeat=600,
                blocked_connection_timeout=300
            )
        )
        channel = connection.channel()
        yield channel
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"RabbitMQ connection error: {e}")
        raise
    finally:
        if channel and not channel.is_closed:
            channel.close()
        if connection and not connection.is_closed:
            connection.close()

@server.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

@server.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized"}), 401

@server.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@server.route("/login", methods=["POST"])
def login():
    """Authenticate user and return token"""
    try:
        token, err = access.login(request)
        
        if not err:
            return jsonify({"token": token}), 200
        else:
            logger.warning(f"Login failed: {err}")
            return jsonify({"error": str(err)}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

@server.route("/upload", methods=["POST"])
def upload():
    """Upload video file (admin only)"""
    try:
        # Validate token
        access_data, err = validate.token(request)
        if err:
            logger.warning(f"Token validation failed: {err}")
            return jsonify({"error": "Invalid token"}), 401
        
        # Parse access data
        try:
            access_json = json.loads(access_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse access data: {e}")
            return jsonify({"error": "Invalid access data"}), 400
        
        # Check admin privileges
        if not access_json.get("admin", False):
            logger.warning(f"Non-admin user attempted upload: {access_json.get('username', 'unknown')}")
            return jsonify({"error": "Admin privileges required"}), 403
        
        # Validate file upload
        if not request.files:
            return jsonify({"error": "No file provided"}), 400
        
        if len(request.files) != 1:
            return jsonify({"error": "Exactly one file required"}), 400
        
        # Process file upload
        for filename, file_obj in request.files.items():
            if not file_obj or file_obj.filename == '':
                return jsonify({"error": "Invalid file"}), 400
            
            try:
                with get_rabbitmq_channel() as channel:
                    err = util.upload(file_obj, fs, channel, access_json)
                    if err:
                        logger.error(f"Upload failed: {err}")
                        return jsonify({"error": str(err)}), 500
            except Exception as e:
                logger.error(f"RabbitMQ error during upload: {e}")
                return jsonify({"error": "Upload processing failed"}), 500
        
        logger.info(f"File uploaded successfully by {access_json.get('username', 'unknown')}")
        return jsonify({"message": "Upload successful"}), 200
        
    except PyMongoError as e:
        logger.error(f"Database error during upload: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        return jsonify({"error": "Upload failed"}), 500

@server.route("/download", methods=["GET"])
def download():
    """Download video file"""
    try:
        # Validate token
        access_data, err = validate.token(request)
        if err:
            return jsonify({"error": "Invalid token"}), 401
        
        # Get file ID from request
        file_id = request.args.get('file_id')
        if not file_id:
            return jsonify({"error": "file_id parameter required"}), 400
        
        # TODO: Implement download logic
        # - Validate file exists in GridFS
        # - Check user permissions for the file
        # - Stream file content back to client
        return jsonify({"error": "Download not implemented yet"}), 501
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({"error": "Download failed"}), 500

@server.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        mongo.db.command('ping')
        
        # Test RabbitMQ connection
        with get_rabbitmq_channel():
            pass
        
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=False)