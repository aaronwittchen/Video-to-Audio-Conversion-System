# fix_test_database_users.py - Fix test database to use 'users' (plural) table
import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

def fix_test_database_to_users():
    """Fix test database to use 'users' table (plural) to match Flask app"""
    
    # Load test environment
    load_dotenv('.env.test')
    
    try:
        # Connect to test database
        conn = mysql.connector.connect(
            host=os.environ.get('TEST_MYSQL_HOST', 'localhost'),
            user=os.environ.get('TEST_MYSQL_USER', 'auth_user'),
            password=os.environ.get('TEST_MYSQL_PASSWORD', 'auth_password'),
            database=os.environ.get('TEST_MYSQL_DB', 'test_auth_db')
        )
        cursor = conn.cursor()
        
        print("Fixing test database to use 'users' table (plural)...")
        
        # Check if 'user' table exists and drop it
        cursor.execute("SHOW TABLES LIKE 'users'")
        if cursor.fetchone():
            print("Dropping 'users' table (singular)...")
            cursor.execute("DROP TABLE users")
        
        # Check if 'users' table exists and drop it to recreate fresh
        cursor.execute("SHOW TABLES LIKE 'users'")
        if cursor.fetchone():
            print("Dropping existing 'users' table to recreate...")
            cursor.execute("DROP TABLE users")
        
        # Create 'users' table (plural) to match Flask code
        print("Creating 'users' table (plural)...")
        cursor.execute("""
            CREATE TABLE users (
                id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Create index
        cursor.execute("CREATE INDEX idx_users_email ON users(email)")
        
        # Generate test user hash
        test_email = 'test@example.com'
        test_password = 'testpassword123'
        salt = bcrypt.gensalt()
        password = bcrypt.hashpw(test_password.encode('utf-8'), salt).decode('utf-8')
        
        # Insert test user
        print(f"Inserting test user: {test_email}")
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (test_email, password)
        )
        
        # Also create a few more test users
        test_users = [
            ('admin@test.com', 'admin123'),
            ('user@test.com', 'user456'),
        ]
        
        for email, password in test_users:
            salt = bcrypt.gensalt()
            hash_val = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (email, password) VALUES (%s, %s)",
                (email, hash_val)
            )
            print(f"Inserted test user: {email} / {password}")
        
        conn.commit()
        
        # Verify the fix
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")
        
        cursor.execute("SELECT email FROM users")
        users = cursor.fetchall()
        print(f"Users in 'users' table: {[user[0] for user in users]}")
        
        print("✅ Test database fixed successfully!")
        print("\nTest users created:")
        print("- test@example.com / testpassword123")
        print("- admin@test.com / admin123")  
        print("- user@test.com / user456")
        
    except mysql.connector.Error as e:
        print(f"❌ Error fixing test database: {e}")
        return False
    
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()
    
    return True

def verify_table_structure():
    """Verify the users table structure"""
    load_dotenv('.env.test')
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('TEST_MYSQL_HOST', 'localhost'),
            user=os.environ.get('TEST_MYSQL_USER', 'auth_user'),
            password=os.environ.get('TEST_MYSQL_PASSWORD', 'auth_password'),
            database=os.environ.get('TEST_MYSQL_DB', 'test_auth_db')
        )
        cursor = conn.cursor()
        
        print("\n" + "="*50)
        print("VERIFYING DATABASE STRUCTURE")
        print("="*50)
        
        # Show table structure
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        print("Table 'users' structure:")
        for col in columns:
            print(f"  {col[0]} - {col[1]}")
        
        # Show indexes
        cursor.execute("SHOW INDEX FROM users")
        indexes = cursor.fetchall()
        print("\nIndexes:")
        for idx in indexes:
            print(f"  {idx[2]} on {idx[4]}")
        
        # Show sample data
        cursor.execute("SELECT id, email, LEFT(password, 20) as password_preview FROM users LIMIT 3")
        sample_data = cursor.fetchall()
        print("\nSample data:")
        for row in sample_data:
            print(f"  ID: {row[0]}, Email: {row[1]}, Hash: {row[2]}...")
        
    except mysql.connector.Error as e:
        print(f"❌ Error verifying database: {e}")
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    print("Fixing test database to use 'users' table...")
    if fix_test_database_to_users():
        verify_table_structure()
        print("\n✅ Ready to test! Run: pytest test_auth_endpoints.py -v -s")
    else:
        print("❌ Fix failed!")