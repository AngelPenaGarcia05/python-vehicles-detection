import cv2
import numpy as np
import threading
import time
from collections import Counter
from config import Config

print("🚀 Inicializando sistema de detección...")

# Modelo YOLO
model = None
if Config.USE_YOLO and Config.YOLO_MODEL_PATH:
    try:
        from ultralytics import YOLO
        model = YOLO(Config.YOLO_MODEL_PATH)
        print("✅ YOLO cargado correctamente")
    except Exception as e:
        print(f"❌ Error cargando YOLO: {e}")
        model = None
else:
    print("ℹ️  Modo simulación activado (sin YOLO)")

class VideoProcessor:
    def __init__(self):
        self.video_caps = {}
        self.current_frames = {}
        self.vehicle_counts = {}
        self.vehicle_classes = {}
        self.processing = True
        
        print(f"📹 Cargando {len(Config.VIDEO_PATHS)} videos...")
        self._load_videos()
        
        # Iniciar procesamiento
        self._start_processing()
    
    def _load_videos(self):
        """Carga todos los videos"""
        for cam_id, video_path in enumerate(Config.VIDEO_PATHS):
            try:
                cap = cv2.VideoCapture(video_path)
                if cap.isOpened():
                    self.video_caps[cam_id] = cap
                    self.vehicle_counts[cam_id] = 0
                    self.vehicle_classes[cam_id] = {}
                    print(f"✅ Video {cam_id}: {video_path}")
                else:
                    print(f"❌ No se pudo abrir: {video_path}")
                    # Crear video simulado como fallback
                    self._create_simulated_video(cam_id)
            except Exception as e:
                print(f"❌ Error cargando video {video_path}: {e}")
                self._create_simulated_video(cam_id)
    
    def _create_simulated_video(self, cam_id):
        """Crea un video simulado cuando no hay video real"""
        print(f"🎬 Creando video simulado para cámara {cam_id}")
        # En una implementación real, aquí crearías un video con OpenCV
        # Por ahora, simplemente inicializamos los contadores
        self.vehicle_counts[cam_id] = 0
        self.vehicle_classes[cam_id] = {}
    
    def _start_processing(self):
        """Inicia el procesamiento de todos los videos"""
        for cam_id in self.video_caps.keys():
            thread = threading.Thread(target=self._process_camera, args=(cam_id,), daemon=True)
            thread.start()
            print(f"🔄 Iniciando procesamiento cámara {cam_id}")
    
    def _process_camera(self, cam_id):
        """Procesa una cámara específica"""
        cap = self.video_caps.get(cam_id)
        if not cap:
            print(f"❌ No hay captura para cámara {cam_id}")
            return
        
        frame_count = 0
        while self.processing:
            try:
                ret, frame = cap.read()
                frame_count += 1
                
                if not ret:
                    # Reiniciar video
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # Procesar cada 10 frames para mejor performance
                if frame_count % 10 == 0:
                    vehicles, classes = self._detect_vehicles(frame, cam_id)
                    
                    # Actualizar contadores
                    self.vehicle_counts[cam_id] = vehicles
                    self.vehicle_classes[cam_id] = classes
                    self.current_frames[cam_id] = frame
                    
                    if vehicles > 0:
                        print(f"🎯 Cámara {cam_id}: {vehicles} vehículos - {classes}")
                
                time.sleep(0.01)  # Controlar FPS
                
            except Exception as e:
                print(f"❌ Error procesando cámara {cam_id}: {e}")
                time.sleep(1)
    
    def _detect_vehicles(self, frame, cam_id):
        """Detecta vehículos en un frame"""
        if model:
            return self._detect_with_yolo(frame)
        else:
            return self._simulate_detection(cam_id)
    
    def _detect_with_yolo(self, frame):
        """Detección usando YOLO"""
        try:
            # Reducir resolución para mejor performance
            small_frame = cv2.resize(frame, (640, 480))
            
            # Ejecutar detección
            results = model(small_frame, verbose=False, conf=0.4)
            
            vehicles = 0
            classes_dict = {}
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        class_name = model.names[class_id]
                        
                        # Filtrar solo vehículos
                        if class_name.lower() in ['carro', 'camion', 'bus', 'motitaxi', 'ambulancia']:
                            vehicles += 1
                            classes_dict[class_name] = classes_dict.get(class_name, 0) + 1
            
            return vehicles, classes_dict
            
        except Exception as e:
            print(f"❌ Error en detección YOLO: {e}")
            return self._simulate_detection(0)  # Usar simulación como fallback
    
    def _simulate_detection(self, cam_id):
        """Simulación de detección cuando YOLO no está disponible"""
        # Simular tráfico variable por cámara
        base_traffic = [3, 2, 4, 1]  # Tráfico base por cámara
        variation = np.random.randint(-2, 3)
        
        vehicles = max(0, base_traffic[cam_id % 4] + variation)
        classes_dict = {'car': vehicles}  # Simular que todos son autos
        
        return vehicles, classes_dict
    
    def get_frame(self, cam_id):
        """Obtiene frame para streaming"""
        frame = self.current_frames.get(cam_id)
        
        if frame is not None:
            # Anotar frame con información
            vehicles = self.vehicle_counts.get(cam_id, 0)
            frame = self._annotate_frame(frame, cam_id, vehicles)
        else:
            # Frame por defecto
            frame = self._create_default_frame(cam_id)
        
        # Codificar como JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return buffer.tobytes()
    
    def _annotate_frame(self, frame, cam_id, vehicles):
        """Añade información al frame"""
        # Redimensionar si es muy grande
        if frame.shape[0] > 480 or frame.shape[1] > 640:
            frame = cv2.resize(frame, (640, 480))
        
        # Añadir overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Texto informativo
        cv2.putText(frame, f"Camara {cam_id + 1}", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Vehiculos: {vehicles}", (20, 65), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
    def _create_default_frame(self, cam_id):
        """Crea un frame por defecto"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame.fill(50)  # Fondo oscuro
        
        cv2.putText(frame, f"CAMARA {cam_id + 1}", (200, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "SIN SEÑAL", (250, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
    def get_metrics(self, cam_id):
        """Obtiene métricas de una cámara"""
        vehicles = self.vehicle_counts.get(cam_id, 0)
        classes = self.vehicle_classes.get(cam_id, {})
        
        return vehicles, classes
    
    def stop(self):
        """Detiene el procesamiento"""
        self.processing = False
        for cap in self.video_caps.values():
            cap.release()
        print("🛑 Procesamiento detenido")

# Instancia global
video_processor = VideoProcessor()

def generate_frames(camera_id):
    """Generador de frames para streaming"""
    print(f"📡 Iniciando stream para cámara {camera_id}")
    
    while True:
        try:
            frame_bytes = video_processor.get_frame(camera_id)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.033)  # ~30 FPS
        except Exception as e:
            print(f"❌ Error en stream cámara {camera_id}: {e}")
            time.sleep(1)