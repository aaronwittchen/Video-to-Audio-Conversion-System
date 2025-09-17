import os
import jwt
import bcrypt
import datetime
import logging
import re # For regex password validation
from flask import Flask, request
from flask_mysqldb import MySQL
from dotenv import load_dotenv
from flasgger import Swagger
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from response_utils import (success_response, validation_error, unauthorized_error, conflict_error, server_error, created_response, too_many_requests_error) # Standardize the API responses

load_dotenv()

# App Setup
server = Flask(__name__)

# Configuration
server.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
server.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
server.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
server.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'auth_db')
server.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', 3306))

# Only initialize Swagger if not in testing mode and flasgger is available
swagger = None

try:
    if not server.config.get('TESTING', False):
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'swagger.yaml')
        swagger = Swagger(server, template_file=template_path)
except ImportError:
    pass
except Exception as e:
    print(f"Swagger initialization failed: {e}")

if swagger:
    print("Swagger UI available at: http://localhost:5000/apidocs/")
else:
    print("Swagger UI not available")

# Only initialize MySQL if not in testing mode
if not server.config.get('TESTING', False):
    mysql = MySQL(server)
else:
    mysql = None

def get_mysql():
    global mysql
    if mysql is None:
        from flask_mysqldb import MySQL
        mysql = MySQL(server)
    return mysql

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure JWT_SECRET is set at startup
JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    logger.error("JWT_SECRET environment variable is missing")
    exit(1)

# Rate Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

limiter.init_app(server)

# Helper Functions
def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt(username, secret, is_admin):
    """Generate a JWT token."""
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    return jwt.encode(
        {
            "username": username,
            "exp": now + datetime.timedelta(days=1),
            "iat": now,
            "admin": is_admin
        },
        secret,
        algorithm="HS256"
    )
    
def validate_password_strength(password):
    """Validate password strength against multiple criteria."""
    rules = [
        (r'.{6,}', 'at least 6 characters'),
        (r'[A-Z]', 'at least one uppercase letter'),
        (r'[a-z]', 'at least one lowercase letter'),
        (r'\d', 'at least one number'),
        (r'[!@#$%^&*(),.?":{}|<>]', 'at least one special character')
    ]
    
    for pattern, message in rules:
        if not re.search(pattern, password):
            return f'Password must contain {message}'
    
    return None

@server.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    return too_many_requests_error()

# Global Exception Handler
@server.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return server_error()

# Routes
@server.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()

    if not data or 'email' not in data or 'password' not in data:
        return validation_error('Email and password are required')

    email = data['email']
    password = data['password']

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return validation_error('Invalid email format')

    password_error = validate_password_strength(password)
    if password_error:
        return validation_error(password_error)

    try:
        with get_mysql().connection.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return conflict_error('User already exists')

            hashed_password = hash_password(password)
            cur.execute(
                "INSERT INTO users (email, password, created_at) VALUES (%s, %s, NOW())",
                (email, hashed_password)
            )
            get_mysql().connection.commit()

            logger.info(f"New user registered: {email}")
            return created_response('User registered successfully')
    
    except Exception as db_error:
        logger.error(f"Database error during registration: {str(db_error)}")
        return server_error('Registration failed')

@server.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        logger.warning("Login attempt with missing credentials")
        return unauthorized_error('Could not verify')

    try:
        # Database connection to execute SQL queries
        with get_mysql().connection.cursor() as cur:
            cur.execute(
                "SELECT email, password FROM users WHERE email = %s", (auth.username,)
            )
            row = cur.fetchone() # Returns a tuple for MySQL, or sqlite3.Row for SQLite

            if not row:
                logger.warning(f"Login attempt for unknown user: {auth.username}")
                return unauthorized_error('Could not verify')

            # If row is a tuple (MySQL), unpack directly
            # If row is a dict-like object (sqlite3.Row), extract fields
            email, stored_password = row if isinstance(row, tuple) else (row['email'], row['password'])

            if auth.username != email or not verify_password(auth.password, stored_password):
                logger.warning(f"Failed login for user: {auth.username}")
                return unauthorized_error('Could not verify')

            token = create_jwt(auth.username, JWT_SECRET, is_admin=True)
            logger.info(f"Successful login for user: {auth.username}")
            return success_response(data={'token': token})

    except Exception as db_error:
        logger.error(f"Database error during login: {str(db_error)}")
        return server_error('Authentication failed')

@server.route('/validate', methods=['POST'])
@limiter.limit("30 per minute")
def validate():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return unauthorized_error('Authorization header missing')

    if not auth_header.startswith("Bearer "):
        return unauthorized_error('Invalid auth header format')

    try:
        token = auth_header.split(" ")[1]
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        logger.info(f"Token validated for user: {decoded.get('username')}")
        return success_response(data=decoded)
    
    except jwt.ExpiredSignatureError:
        logger.warning("Expired token used")
        return unauthorized_error('Token expired')
    except jwt.InvalidTokenError:
        logger.warning("Invalid token used")
        return unauthorized_error('Invalid token')

@server.route('/health', methods=['GET'])
@limiter.limit("5 per minute")
def health():
    return success_response(data={'status': 'healthy'})

if __name__ == '__main__':
    logger.info("Starting authentication server...")
    server.run(host='0.0.0.0', port=5000, debug=False)
