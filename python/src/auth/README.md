# Authentication Service

This service handles user authentication for the Video-to-Audio Conversion System. It provides JWT-based authentication, user registration with verification, token validation, and rate limiting.

## Features

- User registration with email and password
- Secure password hashing using bcrypt
- JWT-based authentication
- Email verification with token
- Password strength validation
- Health check endpoint
- Rate limiting to prevent brute-force attacks
- Comprehensive test coverage

## API Endpoints

### Authentication

- `POST /register`
  Register a new user.
  **Fields:** `email`, `password`
  **Password policy:** At least 6 characters, 1 uppercase, 1 lowercase, 1 number, 1 special character

  **Example request:**

  ```json
  {
    "email": "test2@email.com",
    "password": "SecurePass123!"
  }
  ```

  **Example response:**

  ```json
  {
    "data": {
      "verification_token": "XRlE3S4clvp_wJ0yz56kJy86a8740JMX5xLcnHbY7MQ"
    },
    "message": "User registered successfully. Check logs for verification token.",
    "status": "success"
  }
  ```

- `POST /verify`
  Verify account with token.

  ```json
  {
    "token": "Lh86-kUdimBCRM4nsAdJyPQPNg5ytuzwmSgs0o8JDrk"
  }
  ```

  **Response:**

  ```json
  {
    "message": "Account verified successfully",
    "status": "success"
  }
  ```

- `POST /resend-verification`
  Resend verification token.

  ```json
  {
    "email": "test4@email.com"
  }
  ```

  **Response:**

  ```json
  {
    "data": {
      "verification_token": "lSRmiwOpOjhvDHe31bY0sgPpRDbn8O0S1MhvY6INEvI"
    },
    "message": "New verification email sent. Check logs for token.",
    "status": "success"
  }
  ```

- `POST /login`
  Login using Basic Auth (`Authorization: Basic <base64(email:password)>`).

  **Response:**

  ```json
  {
    "data": {
      "token": "<JWT_TOKEN>"
    },
    "status": "success"
  }
  ```

- `POST /validate`
  Validate JWT with `Authorization: Bearer <token>`.

  **Response:**

  ```json
  {
    "data": {
      "admin": true,
      "exp": 1758208180,
      "iat": 1758121780,
      "username": "test2@email.com"
    },
    "status": "success"
  }
  ```

- `GET /health`
  Health check.

  **Response:**

  ```json
  {
    "data": {
      "status": "healthy"
    },
    "status": "success"
  }
  ```

  With rate limit exceeded:

  ```json
  {
    "status": "error",
    "message": "Rate limit exceeded. Try again later."
  }
  ```

## Database Schema

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    verification_token TEXT,
    verified BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Environment Variables

Create a `.env` file in the `auth` directory:

```
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=auth_db
MYSQL_PORT=3306
JWT_SECRET=your_jwt_secret_key
DEV_MODE=true
```

If `DEV_MODE=true`, verification tokens are logged instead of sending emails.

## Development Setup

1. Create and activate virtual environment:

   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database:

   ```bash
   Get-Content .\init.sql | mysql -u root -p
   mysql -u root -p
   SHOW DATABASES;
   ```

4. Run the server:

   ```bash
   python server.py
   ```

## Testing

Run unit tests:

```bash
pytest -v
```

Coverage report:

```bash
coverage run -m pytest
coverage report -m
```

## API Documentation

When running in development, API docs are available at:

```
http://localhost:5000/apidocs/
```

## Security

- Passwords hashed with bcrypt
- JWT for stateless authentication
- Password strength enforced
- SQL injection protection with parameterized queries
- Input validation for all endpoints
- Rate limiting enabled

## Dependencies

- Flask
- PyJWT
- bcrypt
- python-dotenv
- Flask-MySQLdb
- Flasgger
- pytest

## Deployment

Using Docker:

```bash
docker build -t auth-service .
docker run -p 5000:5000 --env-file .env auth-service
```

## Example Rate Limit Test (PowerShell)

```powershell
1..20 | ForEach-Object {
    try {
        Invoke-RestMethod -Uri "http://localhost:5000/health" -Method GET
    } catch {
        $_.ErrorDetails | ConvertFrom-Json
    }
} | Select-Object status, message | Format-Table -AutoSize
```

**Sample output:**

```
status  message
------  -------------------------------
success
success
success
success
success
error   Rate limit exceeded. Try again later.
error   Rate limit exceeded. Try again later.
...
```
