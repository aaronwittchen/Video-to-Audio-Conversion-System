import os
import jwt
import bcrypt
import datetime
import logging
import re          # Provides regular expression matching operations for validating email formats and password strength.
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from dotenv import load_dotenv
load_dotenv()


# App Setup
server = Flask(__name__)    # Initializes a Flask application instance.

# Configuration
server.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
server.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
server.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
server.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'auth_db')
server.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', 3306))


# Only initialize Swagger if not in testing mode and flasgger is available
try:
    if not server.config.get('TESTING', False):
        from flasgger import Swagger
        swagger = Swagger(server, template_file='../docs/swagger.yml')
    else:
        swagger = None
except ImportError:
    # flasgger not available, skip swagger initialization
    swagger = None

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
logger = logging.getLogger(__name__)  # logger: A logger instance specific to this module (__name__) for logging events

# Helper Functions
def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Converts the password to bytes, Generates a random salt using, Hashes the password with the salt, Converts the hashed password back to a string

def verify_password(password, hashed):
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))  # Verifies a provided password against a stored bcrypt hash.

def create_jwt(username, secret, is_admin):
    """Generate a JWT token."""
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    return jwt.encode(
        {
            "username": username,
            "exp": now + datetime.timedelta(days=1),  # Expiration time (current time + 1 day).
            "iat": now,                               # Issued-at time (current UTC time).
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
    
    return None  # All validations passed

# --- Routes ---
@server.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'message': 'Email and password are required'}), 400

        email = data['email']
        password = data['password']

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({'message': 'Invalid email format'}), 400

        password_error = validate_password_strength(password)
        if password_error:
            return jsonify({'message': password_error}), 400

        try:
            cur = get_mysql().connection.cursor()

            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({'message': 'User already exists'}), 409

            hashed_password = hash_password(password)
            cur.execute(
                "INSERT INTO users (email, password, created_at) VALUES (%s, %s, NOW())",
                (email, hashed_password)
            )
            get_mysql().connection.commit()

            logger.info(f"New user registered: {email}")
            return jsonify({'message': 'User registered successfully'}), 201

        except Exception as db_error:
            logger.error(f"Database error during registration: {str(db_error)}")
            return jsonify({'message': 'Database error'}), 500
        finally:
            if 'cur' in locals():
                cur.close()

    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

@server.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        logger.warning("Login attempt with missing credentials")
        return jsonify({'message': 'Could not verify'}), 401

    try:
        cur = get_mysql().connection.cursor()
        result = cur.execute(
            "SELECT email, password FROM users WHERE email = %s", (auth.username,)
        )

        if result == 0:  # No user found
            logger.warning(f"Login attempt for unknown user: {auth.username}")
            return jsonify({'message': 'Could not verify'}), 401

        email, stored_password = cur.fetchone()

        # Verify credentials
        if auth.username != email or not verify_password(auth.password, stored_password):
            logger.warning(f"Failed login for user: {auth.username}")
            return jsonify({'message': 'Could not verify'}), 401

        jwt_secret = os.environ.get("JWT_SECRET")
        if not jwt_secret:
            logger.error("JWT_SECRET not set in environment")
            return jsonify({'message': 'Server config error'}), 500
        
        token = create_jwt(auth.username, jwt_secret, is_admin=True)  # TODO: Improve is_admin logic
        logger.info(f"Successful login for user: {auth.username}")
        return jsonify({'token': token}), 200

    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500
    finally:
        if 'cur' in locals():
            cur.close()

@server.route('/validate', methods=['POST'])
# TODO: Validate that the token is a Bearer token
def validate():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Authorization header missing'}), 401

    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return jsonify({'message': 'Invalid auth header format'}), 401

    try:
        jwt_secret = os.environ.get("JWT_SECRET")
        if not jwt_secret:
            logger.error("JWT_SECRET not set")
            return jsonify({'message': 'Server config error'}), 500

        decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        logger.info(f"Token validated for users: {decoded.get('username')}")
        return jsonify(decoded), 200

    except jwt.ExpiredSignatureError:
        logger.warning("Expired token used")
        return jsonify({'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        logger.warning("Invalid token used")
        return jsonify({'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        return jsonify({'message': 'Token validation failed'}), 401

@server.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    required_env_vars = ['JWT_SECRET']
    missing = [var for var in required_env_vars if not os.environ.get(var)]
    if missing:
        logger.error(f"Missing required env vars: {missing}")
        exit(1)

    logger.info("Starting authentication server...")
    server.run(host='0.0.0.0', port=5000, debug=False)