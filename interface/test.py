import streamlit as st
import os
from pysqlcipher3 import dbapi2 as sqlite3
import time

def initialize_encrypted_db(db_name, encryption_key):
    start_time = time.time()
    try:
        # Connect to the database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        st.write("Connection established.")
        
        # Set the encryption key
        cursor.execute(f"PRAGMA key = '{encryption_key}';")
        st.write("Encryption key set.")
        
        if not os.path.exists(db_name):
            st.write(f"Database {db_name} does not exist. Creating a new one.")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS example_table (
                id INTEGER PRIMARY KEY,
                data TEXT
            );
            """)
            st.write("Table created.")
            conn.commit()
        else:
            # Try querying an existing table to verify the key
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            st.write(f"Existing tables: {tables}")
    except sqlite3.DatabaseError as e:
        st.error("Failed to open database. The provided encryption key might be incorrect.")
    finally:
        conn.close()
        st.write("Connection closed.")
        st.session_state.database = True
    st.write(f"Operation completed in {time.time() - start_time:.2f} seconds.")

# Streamlit UI
db_name = "encrypted_database.sqlite"

if 'database' not in st.session_state:
    encryption_key = st.text_input("Database encryption key", "password", type="password")
    if st.button("Submit"):
        # Prevent re-initialization and add feedback
            with st.spinner("Initializing database..."):
                initialize_encrypted_db(db_name, encryption_key)
