-- test_init_users.sql - Create test database with 'users' table (plural)
-- Run this with: mysql -u root -p < test_init_users.sql

-- Create test database
CREATE DATABASE IF NOT EXISTS test_auth_db
CHARACTER SET utf8mb4
COLLATION utf8mb4_unicode_ci;

-- Grant specific privileges to existing auth_user on test database
GRANT SELECT, INSERT, UPDATE, DELETE ON test_auth_db.* TO 'auth_user'@'localhost';

-- Flush privileges to ensure they take effect
FLUSH PRIVILEGES;

-- Use test database
USE test_auth_db;

-- Drop existing users table to start fresh
DROP TABLE IF EXISTS users;

-- Create users table (plural) to match Flask app expectations
CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Insert a test user for initial testing
-- Password is 'testpassword123' hashed with bcrypt
-- Generated with: bcrypt.hashpw("testpassword123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
-- INSERT INTO users (email, password) VALUES 
-- ('test@example.com', '$2b$12$X9kQ7y6Z8vJ3wL4mN5pO2eK8hI9jG0aF1bC2dE3fA4gB5hC6iD7jK');

-- Verify table creation
SHOW TABLES;
DESCRIBE users;