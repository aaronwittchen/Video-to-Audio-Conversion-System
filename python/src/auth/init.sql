-- Create the database
CREATE DATABASE IF NOT EXISTS auth_db
    CHARACTER SET utf8mb4              -- Set character set for Unicode compatibility
    COLLATE utf8mb4_unicode_ci;        -- Use a collation that supports a wide range of characters

-- Create a new MySQL user
CREATE USER IF NOT EXISTS 'auth_user'@'localhost' IDENTIFIED BY 'auth_password';  -- Create user with password

-- Grant privileges to the new user on the database
GRANT SELECT, INSERT, UPDATE, DELETE ON auth_db.* TO 'auth_user'@'localhost';     -- Grant CRUD permissions

-- Flush privileges to ensure they take effect
FLUSH PRIVILEGES;                                                                 -- Apply privilege changes

-- Select the database to use
USE auth_db;                                                                      -- Switch to auth_db

-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,                                   -- Primary key, auto-incremented
    email VARCHAR(255) NOT NULL UNIQUE,                                           -- User email (must be unique)
    password VARCHAR(255) NOT NULL,                                               -- Hashed password
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                               -- Timestamp when user was created
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP    -- Timestamp when user was last updated
);

-- Insert a test user with properly generated bcrypt hash
-- Password is 'testpassword123' - you should change this!
-- INSERT INTO users (email, password)
-- VALUES ('test@email.com', '$2a$12$Va7BM3316O/LmyoL2H5gFOaY1tvgU8/xfrDq5dE4ZAcZoescg7Ds2');

-- Verify table creation
SHOW TABLES;         -- Show all tables in the database
DESCRIBE users;      -- Show the structure of the users table
