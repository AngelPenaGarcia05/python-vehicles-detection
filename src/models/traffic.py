from src.models.database import db
from datetime import datetime

class TrafficData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, nullable=False)
    total_vehicles = db.Column(db.Integer, nullable=False)
    cars = db.Column(db.Integer, default=0)
    trucks = db.Column(db.Integer, default=0)
    buses = db.Column(db.Integer, default=0)
    ambulances = db.Column(db.Integer, default=0)
    mototaxis = db.Column(db.Integer, default=0)
    congestion_level = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'total_vehicles': self.total_vehicles,
            'cars': self.cars,
            'trucks': self.trucks,
            'buses': self.buses,
            'ambulances': self.ambulances,
            'mototaxis': self.mototaxis,
            'congestion_level': self.congestion_level,
            'timestamp': self.timestamp.isoformat()
        }