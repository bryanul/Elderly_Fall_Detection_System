# app/database/db_manager.py
import sqlite3
import numpy as np
import pickle
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class DatabaseManager:
    def __init__(self, db_path: str = "people_database.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS people
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               name
                               TEXT
                               UNIQUE
                               NOT
                               NULL,
                               embedding
                               BLOB
                               NOT
                               NULL,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               updated_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           """)
            conn.commit()

    def add_person(self, name: str, embedding: np.ndarray) -> bool:
        """Add or update a person's face embedding."""
        try:
            embedding_blob = pickle.dumps(embedding)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO people (name, embedding, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (name, embedding_blob))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error adding person {name}: {e}")
            return False

    def get_person_embedding(self, name: str) -> Optional[np.ndarray]:
        """Get a person's face embedding by name."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT embedding FROM people WHERE name = ?", (name,))
                result = cursor.fetchone()
                if result:
                    return pickle.loads(result[0])
            return None
        except Exception as e:
            print(f"Error getting embedding for {name}: {e}")
            return None

    def get_all_people(self) -> Dict[str, np.ndarray]:
        """Get all people and their embeddings."""
        people = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, embedding FROM people")
                results = cursor.fetchall()
                for name, embedding_blob in results:
                    people[name] = pickle.loads(embedding_blob)
        except Exception as e:
            print(f"Error getting all people: {e}")
        return people

    def delete_person(self, name: str) -> bool:
        """Delete a person from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM people WHERE name = ?", (name,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting person {name}: {e}")
            return False

    def get_people_list(self) -> List[str]:
        """Get list of all registered people names."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM people ORDER BY name")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting people list: {e}")
            return []
