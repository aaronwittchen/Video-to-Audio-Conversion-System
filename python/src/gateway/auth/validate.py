import os
import requests
import logging
from typing import Optional, Tuple, Union
from requests.exceptions import RequestException, Timeout, ConnectionError
from flask import Request

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
AUTH_SVC_ADDRESS = os.environ.get('AUTH_SVC_ADDRESS')
REQUEST_TIMEOUT = int(os.environ.get('AUTH_REQUEST_TIMEOUT', '10'))  # seconds
MAX_RETRIES = int(os.environ.get('AUTH_MAX_RETRIES', '3'))

def login(request: Request) -> Tuple[Optional[str], Optional[Tuple[str, int]]]:
    """
    Authenticate user with the auth service using basic authentication.
    
    Args:
        request: Flask request object containing authorization headers
    
    Returns:
        Tuple of (token, error) where:
        - token: JWT token string if successful, None if failed
        - error: Tuple of (error_message, status_code) if failed, None if successful
    """
    try:
        # Validate environment configuration
        if not AUTH_SVC_ADDRESS:
            logger.error("AUTH_SVC_ADDRESS environment variable not set")
            return None, ("Authentication service not configured", 500)
        
        # Extract and validate authorization credentials
        auth = request.authorization
        if not auth:
            logger.warning("Login attempt without authorization header")
            return None, ("Missing credentials", 401)
        
        if not auth.username or not auth.password:
            logger.warning(f"Login attempt with incomplete credentials for user: {auth.username or 'unknown'}")
            return None, ("Invalid credentials format", 401)
        
        # Prepare authentication data
        basic_auth = (auth.username.strip(), auth.password)
        auth_url = f"http://{AUTH_SVC_ADDRESS}/login"
        
        logger.info(f"Attempting authentication for user: {auth.username}")
        
        # Make request to auth service with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    auth_url,
                    auth=basic_auth,
                    timeout=REQUEST_TIMEOUT,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'video-service/1.0'
                    }
                )
                
                # Handle successful authentication
                if response.status_code == 200:
                    logger.info(f"Authentication successful for user: {auth.username}")
                    return response.text.strip(), None
                
                # Handle authentication failures
                elif response.status_code == 401:
                    logger.warning(f"Authentication failed for user: {auth.username} - Invalid credentials")
                    return None, ("Invalid credentials", 401)
                
                elif response.status_code == 403:
                    logger.warning(f"Authentication forbidden for user: {auth.username}")
                    return None, ("Access forbidden", 403)
                
                elif response.status_code >= 500:
                    # Server errors - retry
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Auth service error (attempt {attempt + 1}/{MAX_RETRIES}): "
                                     f"Status {response.status_code}")
                        continue
                    else:
                        logger.error(f"Auth service error after {MAX_RETRIES} attempts: "
                                   f"Status {response.status_code}, Response: {response.text}")
                        return None, ("Authentication service unavailable", 503)
                
                else:
                    # Other client errors
                    logger.error(f"Unexpected auth service response: {response.status_code}, {response.text}")
                    return None, (f"Authentication failed: {response.text}", response.status_code)
                    
            except Timeout:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Auth service timeout (attempt {attempt + 1}/{MAX_RETRIES})")
                    continue
                else:
                    logger.error(f"Auth service timeout after {MAX_RETRIES} attempts")
                    return None, ("Authentication service timeout", 504)
                    
            except ConnectionError:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Auth service connection error (attempt {attempt + 1}/{MAX_RETRIES})")
                    continue
                else:
                    logger.error(f"Cannot connect to auth service after {MAX_RETRIES} attempts")
                    return None, ("Authentication service unavailable", 503)
                    
            except RequestException as e:
                logger.error(f"Request error during authentication: {e}")
                return None, ("Authentication request failed", 500)
        
        # Should not reach here, but just in case
        return None, ("Authentication failed", 500)
        
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        return None, ("Internal authentication error", 500)


def token(request: Request) -> Tuple[Optional[str], Optional[Tuple[str, int]]]:
    """
    Validate JWT token with the auth service.
    
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
        
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.warning("Token validation attempt without Authorization header")
            return None, ("Missing authorization header", 401)
        
        # Support both "Bearer token" and just "token" formats
        if auth_header.lower().startswith('bearer '):
            token_value = auth_header[7:].strip()
        else:
            token_value = auth_header.strip()
        
        if not token_value:
            logger.warning("Empty token in authorization header")
            return None, ("Invalid token format", 401)
        
        # Prepare validation request
        validate_url = f"http://{AUTH_SVC_ADDRESS}/validate"
        headers = {
            'Authorization': f'Bearer {token_value}',
            'Content-Type': 'application/json',
            'User-Agent': 'video-service/1.0'
        }
        
        logger.debug("Validating token with auth service")
        
        # Make request to auth service with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    validate_url,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                )
                
                # Handle successful validation
                if response.status_code == 200:
                    logger.debug("Token validation successful")
                    return response.text.strip(), None
                
                # Handle validation failures
                elif response.status_code == 401:
                    logger.warning("Token validation failed - Invalid or expired token")
                    return None, ("Invalid or expired token", 401)
                
                elif response.status_code == 403:
                    logger.warning("Token validation failed - Access forbidden")
                    return None, ("Access forbidden", 403)
                
                elif response.status_code >= 500:
                    # Server errors - retry
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Auth service error during validation (attempt {attempt + 1}/{MAX_RETRIES}): "
                                     f"Status {response.status_code}")
                        continue
                    else:
                        logger.error(f"Auth service error after {MAX_RETRIES} attempts during validation: "
                                   f"Status {response.status_code}")
                        return None, ("Authentication service unavailable", 503)
                
                else:
                    # Other errors
                    logger.error(f"Unexpected response during token validation: {response.status_code}")
                    return None, ("Token validation failed", 401)
                    
            except Timeout:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Token validation timeout (attempt {attempt + 1}/{MAX_RETRIES})")
                    continue
                else:
                    logger.error(f"Token validation timeout after {MAX_RETRIES} attempts")
                    return None, ("Authentication service timeout", 504)
                    
            except ConnectionError:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Token validation connection error (attempt {attempt + 1}/{MAX_RETRIES})")
                    continue
                else:
                    logger.error(f"Cannot connect to auth service for token validation after {MAX_RETRIES} attempts")
                    return None, ("Authentication service unavailable", 503)
                    
            except RequestException as e:
                logger.error(f"Request error during token validation: {e}")
                return None, ("Token validation request failed", 500)
        
        # Should not reach here
        return None, ("Token validation failed", 500)
        
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        return None, ("Internal token validation error", 500)


def check_service_health() -> bool:
    """
    Check if the auth service is healthy and reachable.
    
    Returns:
        True if service is healthy, False otherwise
    """
    try:
        if not AUTH_SVC_ADDRESS:
            return False
        
        health_url = f"http://{AUTH_SVC_ADDRESS}/health"
        response = requests.get(health_url, timeout=5)
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Auth service health check failed: {e}")
        return False