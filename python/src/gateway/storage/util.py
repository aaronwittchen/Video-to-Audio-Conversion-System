import os
import requests
import logging
import json
from typing import Optional, Tuple, Dict, Any, Union
from requests.exceptions import RequestException, Timeout, ConnectionError
from flask import Request
from datetime import datetime, timedelta
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
AUTH_SVC_ADDRESS = os.environ.get('AUTH_SVC_ADDRESS')
REQUEST_TIMEOUT = int(os.environ.get('AUTH_REQUEST_TIMEOUT', '10'))
MAX_RETRIES = int(os.environ.get('AUTH_MAX_RETRIES', '3'))

# Token validation cache to reduce auth service calls
TOKEN_CACHE = {}
CACHE_DURATION = int(os.environ.get('TOKEN_CACHE_SECONDS', '300'))  # 5 minutes default

def token(request: Request) -> Tuple[Optional[str], Optional[Tuple[str, int]]]:
    """
    Validate JWT token with the auth service, with caching support.
    
    Args:
        request: Flask request object containing authorization headers
    
    Returns:
        Tuple of (user_data, error) where:
        - user_data: JSON string with user info if valid, None if invalid
        - error: Tuple of (error_message, status_code) if failed, None if successful
    """
    try:
        # Validate environment configuration
        if not AUTH_SVC_ADDRESS:
            logger.error("AUTH_SVC_ADDRESS environment variable not set")
            return None, ("Authentication service not configured", 500)
        
        # Extract and validate Authorization header
        if "Authorization" not in request.headers:
            logger.warning("Token validation attempt without Authorization header")
            return None, ("Missing authorization header", 401)
        
        auth_header = request.headers["Authorization"]
        if not auth_header or not auth_header.strip():
            logger.warning("Empty Authorization header")
            return None, ("Invalid authorization header", 401)
        
        token_value = auth_header.strip()
        
        # Check cache first (optional optimization)
        if CACHE_DURATION > 0:
            cached_result = get_cached_token_validation(token_value)
            if cached_result:
                logger.debug("Token validation served from cache")
                return cached_result, None
        
        # Prepare validation request
        validate_url = f"http://{AUTH_SVC_ADDRESS}/validate"
        headers = {
            "Authorization": token_value,
            "Content-Type": "application/json",
            "User-Agent": "video-service/1.0"
        }
        
        logger.debug("Validating token with auth service")
        
        # Make request to auth service with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    validate_url,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                )
                
                # Handle successful validation
                if response.status_code == 200:
                    user_data = response.text.strip()
                    
                    # Cache successful validation if caching is enabled
                    if CACHE_DURATION > 0:
                        cache_token_validation(token_value, user_data)
                    
                    logger.debug("Token validation successful")
                    return user_data, None
                
                # Handle validation failures
                elif response.status_code == 401:
                    logger.warning("Token validation failed - Invalid or expired token")
                    return None, ("Invalid or expired token", 401)
                
                elif response.status_code == 403:
                    logger.warning("Token validation failed - Access forbidden")
                    return None, ("Access forbidden", 403)
                
                elif response.status_code == 422:
                    logger.warning("Token validation failed - Malformed token")
                    return None, ("Malformed token", 422)
                
                elif response.status_code >= 500:
                    # Server errors - retry
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Auth service error during validation "
                                     f"(attempt {attempt + 1}/{MAX_RETRIES}): "
                                     f"Status {response.status_code}")
                        continue
                    else:
                        logger.error(f"Auth service error after {MAX_RETRIES} attempts: "
                                   f"Status {response.status_code}")
                        return None, ("Authentication service unavailable", 503)
                
                else:
                    # Other client errors
                    error_msg = response.text or "Token validation failed"
                    logger.error(f"Unexpected response during token validation: "
                               f"{response.status_code}, {error_msg}")
                    return None, (error_msg, response.status_code)
                    
            except Timeout:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Token validation timeout "
                                 f"(attempt {attempt + 1}/{MAX_RETRIES})")
                    continue
                else:
                    logger.error(f"Token validation timeout after {MAX_RETRIES} attempts")
                    return None, ("Authentication service timeout", 504)
                    
            except ConnectionError:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Token validation connection error "
                                 f"(attempt {attempt + 1}/{MAX_RETRIES})")
                    continue
                else:
                    logger.error(f"Cannot connect to auth service for token validation "
                               f"after {MAX_RETRIES} attempts")
                    return None, ("Authentication service unavailable", 503)
                    
            except RequestException as e:
                logger.error(f"Request error during token validation: {e}")
                return None, ("Token validation request failed", 500)
        
        # Fallback error
        return None, ("Token validation failed", 500)
        
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        return None, ("Internal token validation error", 500)


def get_cached_token_validation(token_value: str) -> Optional[str]:
    """
    Get cached token validation result if still valid.
    
    Args:
        token_value: The token to check
    
    Returns:
        Cached user data if valid, None otherwise
    """
    try:
        # Create a hash of the token for cache key (for security)
        token_hash = hashlib.sha256(token_value.encode()).hexdigest()
        
        if token_hash in TOKEN_CACHE:
            cached_data, cached_time = TOKEN_CACHE[token_hash]
            
            # Check if cache entry is still valid
            if datetime.now() - cached_time < timedelta(seconds=CACHE_DURATION):
                return cached_data
            else:
                # Remove expired entry
                del TOKEN_CACHE[token_hash]
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking token cache: {e}")
        return None


def cache_token_validation(token_value: str, user_data: str) -> None:
    """
    Cache token validation result.
    
    Args:
        token_value: The validated token
        user_data: The user data from validation
    """
    try:
        # Create a hash of the token for cache key (for security)
        token_hash = hashlib.sha256(token_value.encode()).hexdigest()
        TOKEN_CACHE[token_hash] = (user_data, datetime.now())
        
        # Clean up old cache entries to prevent memory leaks
        cleanup_expired_cache()
        
    except Exception as e:
        logger.error(f"Error caching token validation: {e}")


def cleanup_expired_cache() -> None:
    """Clean up expired entries from the token cache."""
    try:
        current_time = datetime.now()
        expired_keys = []
        
        for key, (_, cached_time) in TOKEN_CACHE.items():
            if current_time - cached_time >= timedelta(seconds=CACHE_DURATION):
                expired_keys.append(key)
        
        for key in expired_keys:
            del TOKEN_CACHE[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
    except Exception as e:
        logger.error(f"Error cleaning up token cache: {e}")


def extract_user_info(user_data_json: str) -> Optional[Dict[str, Any]]:
    """
    Extract user information from JSON response.
    
    Args:
        user_data_json: JSON string containing user data
    
    Returns:
        Dictionary with user information or None if parsing fails
    """
    try:
        user_data = json.loads(user_data_json)
        return {
            "username": user_data.get("username"),
            "user_id": user_data.get("user_id"),
            "admin": user_data.get("admin", False),
            "permissions": user_data.get("permissions", []),
            "email": user_data.get("email")
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse user data JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error extracting user info: {e}")
        return None


def validate_file_size(file_obj, max_size_mb: int = 500) -> Tuple[bool, Optional[str]]:
    """
    Validate file size.
    
    Args:
        file_obj: File object to validate
        max_size_mb: Maximum file size in MB
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not file_obj:
            return False, "No file provided"
        
        # Get file size
        file_obj.seek(0, 2)  # Seek to end
        file_size = file_obj.tell()
        file_obj.seek(0)  # Reset to beginning
        
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return False, f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
        
        if file_size == 0:
            return False, "File is empty"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating file size: {e}")
        return False, "Error validating file size"


def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate filename for security and format.
    
    Args:
        filename: Filename to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not filename or not filename.strip():
            return False, "Filename cannot be empty"
        
        filename = filename.strip()
        
        # Check for dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        if any(char in filename for char in dangerous_chars):
            return False, "Filename contains invalid characters"
        
        # Check filename length
        if len(filename) > 255:
            return False, "Filename too long (max 255 characters)"
        
        # Check for valid extension (basic check)
        if '.' not in filename:
            return False, "Filename must have an extension"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating filename: {e}")
        return False, "Error validating filename"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def clear_token_cache() -> None:
    """Clear all cached token validations (useful for testing or maintenance)."""
    global TOKEN_CACHE
    TOKEN_CACHE.clear()
    logger.info("Token cache cleared")