import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'traffic_db')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    # Video Configuration - ACTUALIZA ESTAS RUTAS
    VIDEO_PATHS = [
        os.getenv('VIDEO_PATH_0', 'videos/camera1.mp4'),
        os.getenv('VIDEO_PATH_1', 'videos/camera2.mp4'),
        os.getenv('VIDEO_PATH_2', 'videos/camera3.mp4'),
        os.getenv('VIDEO_PATH_3', 'videos/camera4.mp4')
    ]
    
    # YOLO Configuration
    YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', 'models/best.pt')
    USE_YOLO = os.getenv('USE_YOLO', 'True').lower() == 'true'
    
    # Debug
    DEBUG = True

# Verificar configuración
print("🔧 Configuración cargada:")
print(f"   - Videos: {Config.VIDEO_PATHS}")
print(f"   - YOLO: {Config.USE_YOLO}")
print(f"   - Modelo: {Config.YOLO_MODEL_PATH}")