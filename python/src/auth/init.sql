CREATE DATABASE IF NOT EXISTS auth_db
-- Ensures the database supports full Unicode characters
-- MySQL’s older utf8 only supports up to 3-byte characters, so it actually cannot store certain Unicode characters (like emoji, some Chinese/Japanese characters, etc.)
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Create a new MySQL user
CREATE USER IF NOT EXISTS 'auth_user'@'localhost' IDENTIFIED BY 'auth_password';

-- Grant privileges to the new user on the database
GRANT SELECT, INSERT, UPDATE, DELETE ON auth_db.* TO 'auth_user'@'localhost';

-- Flush privileges to ensure they take effect; Reloads the grant tables in MySQL
FLUSH PRIVILEGES;

USE auth_db;

-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert a test user with generated bcrypt hash password
INSERT INTO users (email, password)
VALUES ('test@email.com', '$2a$12$Va7BM3316O/LmyoL2H5gFOaY1tvgU8/xfrDq5dE4ZAcZoescg7Ds2');

-- Verify table creation
SHOW TABLES;
DESCRIBE users;
