import os
from pysqlcipher3 import dbapi2 as sqlite3
import time

def initialize_encrypted_db(db_name, encryption_key):
    start_time = time.time()
    
    if not os.path.exists(db_name):
        print(f"Database {db_name} does not exist. Creating a new one.")
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            print("Connection established.")
            
            cursor.execute(f"PRAGMA key = '{encryption_key}';")
            print("Encryption key set.")
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS example_table (
                id INTEGER PRIMARY KEY,
                data TEXT
            );
            """)
            print("Table created.")
            
            conn.commit()
        finally:
            conn.close()
            print("Connection closed.")
    else:
        print(f"Database {db_name} already exists.")
    
    print(f"Operation completed in {time.time() - start_time:.2f} seconds.")

# Replace with your database name and encryption key
db_name = "encrypted_database.sqlite"
encryption_key = "your_secure_key"

initialize_encrypted_db(db_name, encryption_key)
