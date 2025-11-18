import cv2
import torch
import numpy as np
from ultralytics import YOLO
import threading
import time
from queue import Queue
import json

class TrafficDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.processing = False
        self.detection_data = {
            'camera_0': {'total': 0, 'cars': 0, 'trucks': 0, 'buses': 0, 'ambulances': 0, 'mototaxis': 0},
            'camera_1': {'total': 0, 'cars': 0, 'trucks': 0, 'buses': 0, 'ambulances': 0, 'mototaxis': 0},
            'camera_2': {'total': 0, 'cars': 0, 'trucks': 0, 'buses': 0, 'ambulances': 0, 'mototaxis': 0},
            'camera_3': {'total': 0, 'cars': 0, 'trucks': 0, 'buses': 0, 'ambulances': 0, 'mototaxis': 0}
        }
        self.frame_queues = [Queue(maxsize=1) for _ in range(4)]
        self.threads = []
        
    def start_processing(self, video_paths):
        self.processing = True
        for i, video_path in enumerate(video_paths):
            thread = threading.Thread(target=self.process_video, args=(i, video_path))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
    
    def stop_processing(self):
        self.processing = False
        for thread in self.threads:
            thread.join()
        self.threads = []
    
    def process_video(self, camera_id, video_path):
        cap = cv2.VideoCapture(video_path)
        
        while self.processing and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            # Realizar detección
            results = self.model(frame, conf=0.5)
            
            # Contar vehículos por clase
            vehicle_counts = {
                'carro': 0, 'camion': 0, 'bus': 0, 
                'ambulancia': 0, 'mototaxi': 0
            }
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    if class_name in vehicle_counts:
                        vehicle_counts[class_name] += 1
            
            # Actualizar datos de detección
            total_vehicles = sum(vehicle_counts.values())
            self.detection_data[f'camera_{camera_id}'] = {
                'total': total_vehicles,
                'cars': vehicle_counts['carro'],
                'trucks': vehicle_counts['camion'],
                'buses': vehicle_counts['bus'],
                'ambulances': vehicle_counts['ambulancia'],
                'mototaxis': vehicle_counts['mototaxi']
            }
            
            # Dibujar bounding boxes
            annotated_frame = results[0].plot()
            
            # Codificar frame para streaming
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            if ret:
                frame_bytes = buffer.tobytes()
                if not self.frame_queues[camera_id].empty():
                    try:
                        self.frame_queues[camera_id].get_nowait()
                    except:
                        pass
                self.frame_queues[camera_id].put(frame_bytes)
            
            time.sleep(0.03)  # Controlar FPS
        
        cap.release()
    
    def get_frame(self, camera_id):
        try:
            return self.frame_queues[camera_id].get(timeout=1)
        except:
            return None
    
    def get_detection_data(self, camera_id=None):
        if camera_id is not None:
            return self.detection_data.get(f'camera_{camera_id}')
        return self.detection_data
    
    def get_congestion_level(self, total_vehicles):
        if total_vehicles < 5:
            return 'low'
        elif total_vehicles < 15:
            return 'medium'
        else:
            return 'high'

# Instancia global del detector
traffic_detector = TrafficDetector('pytorch/best.pt')