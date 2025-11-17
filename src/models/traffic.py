from .database import get_db_connection

class TrafficLog:
    @staticmethod
    def create(camera_id, vehicle_count, congestion_level):
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            'INSERT INTO traffic_logs (camera_id, vehicle_count, congestion_level) VALUES (%s, %s, %s)',
            (camera_id, vehicle_count, congestion_level)
        )
        
        conn.commit()
        cur.close()
        conn.close()
    
    @staticmethod
    def get_recent_logs(limit=100):
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(
            'SELECT * FROM traffic_logs ORDER BY timestamp DESC LIMIT %s',
            (limit,)
        )
        
        logs = cur.fetchall()
        cur.close()
        conn.close()
        
        return logs