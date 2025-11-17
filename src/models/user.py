from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db_connection
import psycopg2
from psycopg2.extras import RealDictCursor  # ¡Falta esta importación!

class User:
    def __init__(self, username, email, id=None):
        self.id = id
        self.username = username
        self.email = email
    
    @staticmethod
    def create(username, email, password):
        conn = get_db_connection()
        cur = conn.cursor()
        password_hash = generate_password_hash(password)
        
        try:
            cur.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id',
                (username, email, password_hash)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return User(username, email, user_id)
        except psycopg2.IntegrityError:
            return None
        finally:
            cur.close()
            conn.close()
    
    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user_data = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if user_data:
            return User(
                username=user_data['username'],
                email=user_data['email'],
                id=user_data['id']
            )
        return None
    
    @staticmethod
    def check_password(username, password):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user_data = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            return User(
                username=user_data['username'],
                email=user_data['email'],
                id=user_data['id']
            )
        return None