import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu-clave-secreta-aqui'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://usuario:password@localhost/trafico_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de videos
    VIDEO_PATHS = [
        'videos/videoplayback.mp4',
        'videos/videoplayback.mp4', 
        'videos/videoplayback2.mp4',
        'videos/videoplayback3.mp4'
    ]
    
    # Modelo YOLO
    MODEL_PATH = 'pytorch/best.pt'
    
    # Configuración de detección
    CONFIDENCE_THRESHOLD = 0.5
    CLASS_NAMES = ['carro', 'camion', 'bus', 'ambulancia', 'mototaxi']