import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import numpy as np
import logging
import requests

DB_NAME = "buddy-chat-db"
DB_USER = "myuser"
DB_PASSWORD = "mypassword"
DB_HOST = "localhost"
DB_PORT = "5432"
TABLE_NAME = "student_vectors"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def ingest_students():
    # Load students data
    with open("students.json", "r", encoding="utf-8") as f:
        students = json.load(f)
    logger.info("Loaded students data from students.json")

    # Connect to default db to create students db if not exists
    conn = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'")
    exists = cur.fetchone()
    if not exists:
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        logger.info(f"Created database: {DB_NAME}")
    else:
        logger.info(f"Database {DB_NAME} already exists")
    cur.close()
    conn.close()

    # Connect to students db
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    cur = conn.cursor()
    logger.info(f"Connected to database: {DB_NAME}")

    # Enable pgvector extension
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    logger.info("Ensured pgvector extension is enabled")

    # Create table if not exists
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id SERIAL PRIMARY KEY,
        name TEXT,
        hobbies TEXT[],
        visited_places TEXT[],
        interested_food TEXT[],
        embedding VECTOR(5120)
    )
    """)
    conn.commit()
    logger.info(f"Ensured table {TABLE_NAME} exists")

    logger.info("Using LLM deepseek-r1:14b for embeddings")

    # Insert student records
    for student in students:
        text = f"{student['name']} {', '.join(student['hobbies'])} {', '.join(student['visited_places'])} {', '.join(student['interested_food'])}"
        payload = {
            "model": "deepseek-r1:14b",
            "prompt": text
        }
        try:
            # Check if student already exists by name
            cur.execute(f"SELECT 1 FROM {TABLE_NAME} WHERE name = %s", (student['name'],))
            if cur.fetchone():
                logger.info(f"Student already exists, skipping: {student['name']}")
                continue
            resp = requests.post("http://localhost:11434/api/embeddings", json=payload)
            resp.raise_for_status()
            emb = resp.json().get("embedding")
            if not emb:
                logger.error(f"No embedding returned for student: {student['name']}")
                continue
            cur.execute(f"""
                INSERT INTO {TABLE_NAME} (name, hobbies, visited_places, interested_food, embedding)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                student['name'],
                student['hobbies'],
                student['visited_places'],
                student['interested_food'],
                emb
            ))
            conn.commit()
            logger.info(f"Inserted and committed student: {student['name']}")
        except Exception as e:
            logger.error(f"Error inserting student {student['name']}: {e}")
            conn.rollback()
    logger.info("Closed database connection")
    print("Student data ingested into vector database.")

if __name__ == "__main__":
    ingest_students()
