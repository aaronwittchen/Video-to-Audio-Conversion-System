import pika
import json
import logging
from typing import Optional, Tuple, Any, Dict
from gridfs import GridFS
from gridfs.errors import GridFSError
from pymongo.errors import PyMongoError

# Configure logging
logger = logging.getLogger(__name__)

def upload(
    file_obj: Any, 
    fs: GridFS, 
    channel: pika.channel.Channel, 
    access: Dict[str, Any]
) -> Optional[Tuple[str, int]]:
    """
    Upload a file to MongoDB GridFS and publish a message to RabbitMQ queue.
    
    Args:
        file_obj: File object to upload
        fs: GridFS instance
        channel: RabbitMQ channel
        access: User access data containing username and permissions
    
    Returns:
        None if successful, tuple of (error_message, status_code) if failed
    """
    fid = None
    
    try:
        # Validate inputs
        if not file_obj:
            logger.error("No file provided for upload")
            return "No file provided", 400
            
        if not access or not access.get("username"):
            logger.error("Invalid access data provided")
            return "Invalid user access data", 400
        
        # Get file info for logging
        filename = getattr(file_obj, 'filename', 'unknown')
        file_size = None
        
        # Try to get file size if possible
        try:
            file_obj.seek(0, 2)  # Seek to end
            file_size = file_obj.tell()
            file_obj.seek(0)  # Reset to beginning
        except (AttributeError, OSError):
            pass
        
        logger.info(f"Starting upload for user {access['username']}, "
                   f"file: {filename}, size: {file_size or 'unknown'}")
        
        # Store file in MongoDB GridFS
        try:
            fid = fs.put(
                file_obj,
                filename=filename,
                metadata={
                    "uploaded_by": access["username"],
                    "upload_timestamp": None,  # GridFS will add this
                    "original_filename": filename
                }
            )
            logger.info(f"File stored in GridFS with ID: {fid}")
            
        except GridFSError as e:
            logger.error(f"GridFS error during file upload: {e}")
            return "Failed to store file", 500
        except PyMongoError as e:
            logger.error(f"MongoDB error during file upload: {e}")
            return "Database error during upload", 500
        except Exception as e:
            logger.error(f"Unexpected error storing file: {e}")
            return "Internal server error during file storage", 500
        
        # Prepare message for RabbitMQ
        message = {
            "video_fid": str(fid),
            "mp3_fid": None,
            "username": access["username"],
            "original_filename": filename,
            "file_size": file_size,
            "status": "uploaded"
        }
        
        # Publish message to RabbitMQ queue
        try:
            # Ensure the queue exists (declare it)
            channel.queue_declare(queue="video", durable=True)
            
            channel.basic_publish(
                exchange="",
                routing_key="video",
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                    content_type="application/json",
                    message_id=str(fid),
                    timestamp=None  # Pika will set this
                )
            )
            logger.info(f"Message published to queue for file {fid}")
            
        except pika.exceptions.AMQPError as e:
            logger.error(f"RabbitMQ error during message publish: {e}")
            # Cleanup: delete the uploaded file since we couldn't queue the job
            try:
                fs.delete(fid)
                logger.info(f"Cleaned up file {fid} after queue failure")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup file {fid} after queue failure: {cleanup_error}")
            return "Failed to queue processing job", 500
            
        except json.JSONEncodeError as e:
            logger.error(f"JSON encoding error: {e}")
            # Cleanup uploaded file
            try:
                fs.delete(fid)
                logger.info(f"Cleaned up file {fid} after JSON error")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup file {fid} after JSON error: {cleanup_error}")
            return "Failed to encode message", 500
            
        except Exception as e:
            logger.error(f"Unexpected error during message publish: {e}")
            # Cleanup uploaded file
            try:
                fs.delete(fid)
                logger.info(f"Cleaned up file {fid} after publish failure")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup file {fid} after publish failure: {cleanup_error}")
            return "Internal server error during job queuing", 500
        
        logger.info(f"Upload completed successfully for user {access['username']}, file ID: {fid}")
        return None  # Success
        
    except Exception as e:
        logger.error(f"Unexpected error in upload function: {e}")
        # Emergency cleanup
        if fid:
            try:
                fs.delete(fid)
                logger.info(f"Emergency cleanup of file {fid}")
            except Exception as cleanup_error:
                logger.error(f"Emergency cleanup failed for file {fid}: {cleanup_error}")
        return "Internal server error", 500


def validate_file_type(filename: str, allowed_extensions: set = None) -> bool:
    """
    Validate file type based on extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed extensions (default: video formats)
    
    Returns:
        True if file type is allowed, False otherwise
    """
    if not filename:
        return False
        
    if allowed_extensions is None:
        allowed_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}
    
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    return f'.{file_extension}' in allowed_extensions


def get_file_info(fs: GridFS, file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get file information from GridFS.
    
    Args:
        fs: GridFS instance
        file_id: File ID to lookup
    
    Returns:
        Dictionary with file info or None if not found
    """
    try:
        from bson import ObjectId
        
        file_obj = fs.find_one({"_id": ObjectId(file_id)})
        if not file_obj:
            return None
            
        return {
            "file_id": str(file_obj._id),
            "filename": file_obj.filename,
            "length": file_obj.length,
            "upload_date": file_obj.upload_date,
            "metadata": file_obj.metadata or {}
        }
        
    except Exception as e:
        logger.error(f"Error getting file info for {file_id}: {e}")
        return None