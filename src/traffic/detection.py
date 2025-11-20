import cv2
import torch
import numpy as np
from ultralytics import YOLO
import threading
import time
from queue import Queue
import json
from datetime import datetime, timedelta

class TrafficDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.processing = False
        
        # Datos en tiempo real (por frame) para cada cámara
        self.realtime_data = {
            'camera_0': {'total': 0, 'carro': 0, 'camion': 0, 'bus': 0, 'ambulancia': 0, 'mototaxi': 0, 'weighted_total': 0},
            'camera_1': {'total': 0, 'carro': 0, 'camion': 0, 'bus': 0, 'ambulancia': 0, 'mototaxi': 0, 'weighted_total': 0},
            'camera_2': {'total': 0, 'carro': 0, 'camion': 0, 'bus': 0, 'ambulancia': 0, 'mototaxi': 0, 'weighted_total': 0},
            'camera_3': {'total': 0, 'carro': 0, 'camion': 0, 'bus': 0, 'ambulancia': 0, 'mototaxi': 0, 'weighted_total': 0}
        }
        
        # Pesos para cada tipo de vehículo
        self.vehicle_weights = {
            'carro': 1,
            'mototaxi': 0.7,  # Las motos ocupan menos espacio
            'camion': 5,      # Camiones ocupan mucho espacio
            'bus': 4,         # Buses ocupan espacio similar a camiones
            'ambulancia': 10  # Alta prioridad por ser vehículo de emergencia
        }
        
        # Configuración de semáforos
        self.semaphore_states = {
            'group_1': {  # Cámaras 0 y 2 (calles que se cruzan)
                'current_color': 'red',
                'next_color': 'green',
                'change_time': None,
                'cameras': [0, 2]
            },
            'group_2': {  # Cámaras 1 y 3 (calles que se cruzan)
                'current_color': 'green',
                'next_color': 'red', 
                'change_time': None,
                'cameras': [1, 3]
            }
        }
        
        # Tiempos de semáforo (en segundos)
        self.semaphore_times = {
            'green_min': 10,
            'green_max': 60,
            'yellow_time': 5,
            'red_time': 3
        }
        
        # Estado de emergencia (cuando se detecta ambulancia)
        self.emergency_mode = {
            'active': False,
            'emergency_camera': None,
            'end_time': None
        }
        
        self.frame_queues = [Queue(maxsize=1) for _ in range(4)]
        self.threads = []
        
        # Mapeo de variaciones de nombres a nuestros nombres estandarizados
        self.class_mapping = {
            'carro': 'carro',
            'car': 'carro',
            'auto': 'carro',
            'coche': 'carro',
            'camion': 'camion',
            'truck': 'camion',
            'bus': 'bus',
            'autobus': 'bus',
            'omnibus': 'bus',
            'ambulancia': 'ambulancia',
            'ambulance': 'ambulancia',
            'mototaxi': 'mototaxi',
            'moto': 'mototaxi',
            'motorcycle': 'mototaxi'
        }
        
        # Verificar las clases que detecta el modelo
        print("Clases del modelo YOLO:")
        if hasattr(self.model, 'names'):
            for i, class_name in self.model.names.items():
                normalized = class_name.lower().strip()
                mapped = self.class_mapping.get(normalized, 'desconocido')
                print(f"  Clase {i}: '{class_name}' -> normalizada: '{normalized}' -> mapeada: '{mapped}'")
        
    def start_processing(self, video_paths):
        self.processing = True
        # Reiniciar datos cuando se inicia el procesamiento
        for i in range(4):
            self.realtime_data[f'camera_{i}'] = {
                'total': 0, 'carro': 0, 'camion': 0, 'bus': 0, 
                'ambulancia': 0, 'mototaxi': 0, 'weighted_total': 0
            }
        
        # Inicializar tiempos de semáforo
        current_time = datetime.now()
        self.semaphore_states['group_1']['change_time'] = current_time + timedelta(seconds=30)
        self.semaphore_states['group_2']['change_time'] = current_time + timedelta(seconds=5)
        
        for i, video_path in enumerate(video_paths):
            thread = threading.Thread(target=self.process_video, args=(i, video_path))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
        
        # Iniciar hilo para control de semáforos
        semaphore_thread = threading.Thread(target=self.control_semaphores)
        semaphore_thread.daemon = True
        semaphore_thread.start()
    
    def stop_processing(self):
        self.processing = False
        for thread in self.threads:
            thread.join()
        self.threads = []
    
    def calculate_weighted_total(self, counts):
        """Calcular total ponderado basado en los pesos de los vehículos"""
        weighted_total = 0
        for vehicle_type, count in counts.items():
            weighted_total += count * self.vehicle_weights.get(vehicle_type, 1)
        return weighted_total
    
    def get_congestion_level(self, weighted_total):
        """Determinar nivel de congestión basado en total ponderado"""
        if weighted_total < 8:
            return 'low'
        elif weighted_total < 25:
            return 'medium'
        else:
            return 'high'
    
    def control_semaphores(self):
        """Control inteligente de semáforos"""
        while self.processing:
            try:
                current_time = datetime.now()
                
                # Verificar modo de emergencia (ambulancia detectada)
                self.check_emergency_mode()
                
                if not self.emergency_mode['active']:
                    # Lógica normal de semáforos
                    self.normal_semaphore_control(current_time)
                else:
                    # Lógica de emergencia
                    self.emergency_semaphore_control(current_time)
                
                time.sleep(1)  # Revisar cada segundo
            except Exception as e:
                print(f"Error en control de semáforos: {e}")
                time.sleep(5)
    
    def check_emergency_mode(self):
        """Verificar si hay ambulancias detectadas"""
        for camera_id in range(4):
            if self.realtime_data[f'camera_{camera_id}']['ambulancia'] > 0:
                if not self.emergency_mode['active']:
                    self.emergency_mode['active'] = True
                    self.emergency_mode['emergency_camera'] = camera_id
                    self.emergency_mode['end_time'] = datetime.now() + timedelta(seconds=15)
                    print(f"🚑 MODO EMERGENCIA ACTIVADO - Cámara {camera_id}")
                return
        
        # Si no hay ambulancias y el tiempo de emergencia expiró, desactivar modo emergencia
        if (self.emergency_mode['active'] and 
            self.emergency_mode['end_time'] and 
            datetime.now() > self.emergency_mode['end_time']):
            self.emergency_mode['active'] = False
            self.emergency_mode['emergency_camera'] = None
            print("🚑 MODO EMERGENCIA DESACTIVADO")
    
    def normal_semaphore_control(self, current_time):
        """Control normal de semáforos basado en congestión"""
        for group_name, group_data in self.semaphore_states.items():
            # Si es tiempo de cambiar el semáforo
            if group_data['change_time'] and current_time >= group_data['change_time']:
                self.change_semaphore(group_name, current_time)
    
    def emergency_semaphore_control(self, current_time):
        """Control de semáforos en modo emergencia"""
        emergency_camera = self.emergency_mode['emergency_camera']
        
        # Determinar a qué grupo pertenece la cámara con ambulancia
        target_group = None
        for group_name, group_data in self.semaphore_states.items():
            if emergency_camera in group_data['cameras']:
                target_group = group_name
                break
        
        if target_group:
            # Si el semáforo del grupo de emergencia no está en verde, cambiarlo
            if self.semaphore_states[target_group]['current_color'] != 'green':
                print(f"🚑 Cambiando semáforo del grupo {target_group} a VERDE por emergencia")
                self.semaphore_states[target_group]['current_color'] = 'green'
                self.semaphore_states[target_group]['change_time'] = datetime.now() + timedelta(
                    seconds=self.semaphore_times['green_min']
                )
                
                # Cambiar el otro grupo a rojo
                other_group = 'group_2' if target_group == 'group_1' else 'group_1'
                self.semaphore_states[other_group]['current_color'] = 'red'
                self.semaphore_states[other_group]['change_time'] = datetime.now() + timedelta(
                    seconds=self.semaphore_times['green_min'] + self.semaphore_times['yellow_time']
                )
    
    def change_semaphore(self, group_name, current_time):
        group = self.semaphore_states[group_name]
        other_group = 'group_2' if group_name == 'group_1' else 'group_1'
        
        print(f"🔴 Cambiando semáforo {group_name} de {group['current_color']}")
        
        if group['current_color'] == 'green':
            # Cambiar a amarillo primero
            group['current_color'] = 'yellow'
            group['change_time'] = current_time + timedelta(
                seconds=self.semaphore_times['yellow_time']
            )
            print(f"🟡 Semáforo {group_name} cambiando a AMARILLO por {self.semaphore_times['yellow_time']}s")
        
        elif group['current_color'] == 'yellow':
            # Cambiar a rojo
            group['current_color'] = 'red'
            
            # Calcular tiempo de verde para el otro grupo basado en congestión
            green_time = self.calculate_green_time(other_group)
            group['change_time'] = current_time + timedelta(seconds=green_time + self.semaphore_times['yellow_time'])
            
            # El otro grupo cambia a verde
            self.semaphore_states[other_group]['current_color'] = 'green'
            self.semaphore_states[other_group]['change_time'] = current_time + timedelta(
                seconds=green_time
            )
            print(f"🔴 Semáforo {group_name} cambiando a ROJO")
            print(f"🟢 Semáforo {other_group} cambiando a VERDE por {green_time}s")
        
        elif group['current_color'] == 'red':
            # Cambiar a verde
            green_time = self.calculate_green_time(group_name)
            group['current_color'] = 'green'
            group['change_time'] = current_time + timedelta(seconds=green_time)
            print(f"🟢 Semáforo {group_name} cambiando a VERDE por {green_time}s")
    
    def calculate_green_time(self, group_name):
        """Calcular tiempo de verde basado en congestión"""
        group = self.semaphore_states[group_name]
        other_group = 'group_2' if group_name == 'group_1' else 'group_1'
        
        # Calcular congestión de ambos grupos
        group_congestion = self.get_group_congestion(group_name)
        other_congestion = self.get_group_congestion(other_group)
        
        # Lógica de tiempos basada en congestión
        if group_congestion == 'high' and other_congestion == 'low':
            return self.semaphore_times['green_max']  # Máximo tiempo para grupo congestionado
        elif group_congestion == 'high' and other_congestion == 'high':
            return self.semaphore_times['green_min'] + 20  # Tiempo intermedio
        elif group_congestion == 'low' and other_congestion == 'high':
            return self.semaphore_times['green_min']  # Mínimo tiempo para grupo no congestionado
        else:
            return self.semaphore_times['green_min'] + 10  # Tiempo base
    
    def get_group_congestion(self, group_name):
        """Obtener nivel de congestión de un grupo de cámaras"""
        group = self.semaphore_states[group_name]
        total_weighted = 0
        
        for camera_id in group['cameras']:
            total_weighted += self.realtime_data[f'camera_{camera_id}']['weighted_total']
        
        return self.get_congestion_level(total_weighted)
    
    def process_video(self, camera_id, video_path):
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        
        while self.processing and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_count = 0
                continue
            
            frame_count += 1
            
            # Realizar detección
            results = self.model(frame, conf=0.5, verbose=False)
            
            # Contadores del frame actual
            current_frame_counts = {
                'carro': 0, 'camion': 0, 'bus': 0, 
                'ambulancia': 0, 'mototaxi': 0
            }
            
            # Procesar detecciones
            if results and len(results) > 0:
                for result in results:
                    if result.boxes is not None and len(result.boxes) > 0:
                        boxes = result.boxes
                        for box in boxes:
                            class_id = int(box.cls[0])
                            original_class_name = self.model.names[class_id]
                            
                            # Normalizar y mapear el nombre de la clase
                            normalized_name = original_class_name.lower().strip()
                            mapped_class = self.class_mapping.get(normalized_name)
                            
                            if mapped_class and mapped_class in current_frame_counts:
                                current_frame_counts[mapped_class] += 1
            
            # Calcular total del frame actual y total ponderado
            total_current = sum(current_frame_counts.values())
            weighted_total = self.calculate_weighted_total(current_frame_counts)
            
            # Actualizar datos en tiempo real
            self.realtime_data[f'camera_{camera_id}'] = {
                'total': total_current,
                'carro': current_frame_counts['carro'],
                'camion': current_frame_counts['camion'],
                'bus': current_frame_counts['bus'],
                'ambulancia': current_frame_counts['ambulancia'],
                'mototaxi': current_frame_counts['mototaxi'],
                'weighted_total': weighted_total
            }
            
            # Dibujar bounding boxes y etiquetas
            annotated_frame = results[0].plot()
            
            # Añadir contadores en el frame
            self.add_counters_to_frame(annotated_frame, current_frame_counts, total_current, weighted_total, camera_id, frame_count)
            
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
    
    def add_counters_to_frame(self, frame, frame_counts, total_current, weighted_total, camera_id, frame_count):
        """Añadir contadores de vehículos al frame"""
        height, width = frame.shape[:2]
        
        # Crear fondo semitransparente para los contadores
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Configurar texto
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        # Mostrar contadores
        y_offset = 40
        cv2.putText(frame, f"Camara {camera_id + 1}", (20, y_offset), font, 0.6, (0, 255, 255), thickness)
        
        # Contadores del frame actual
        texts_frame = [
            f"Carros: {frame_counts['carro']}",
            f"Camiones: {frame_counts['camion']}",
            f"Buses: {frame_counts['bus']}",
            f"Ambulancias: {frame_counts['ambulancia']}",
            f"Mototaxis: {frame_counts['mototaxi']}",
            f"TOTAL: {total_current}",
            f"Ponderado: {weighted_total:.1f}"
        ]
        
        for i, text in enumerate(texts_frame):
            y_offset += 20
            color = (0, 255, 0) if "TOTAL" in text else (255, 255, 255)
            color = (255, 255, 0) if "Ponderado" in text else color
            cv2.putText(frame, text, (20, y_offset), font, 0.5, color, thickness)
    
    def get_frame(self, camera_id):
        try:
            return self.frame_queues[camera_id].get(timeout=1)
        except:
            return None
    
    def get_realtime_data(self, camera_id=None):
        """Obtener datos en tiempo real (del frame actual)"""
        if camera_id is not None:
            return self.realtime_data.get(f'camera_{camera_id}')
        return self.realtime_data
    
    def get_semaphore_states(self):
        """Obtener estado actual de los semáforos"""
        return self.semaphore_states
    
    def get_emergency_mode(self):
        """Obtener estado del modo emergencia"""
        return self.emergency_mode
    
    def get_dashboard_totals(self):
        """Obtener totales para el dashboard (suma de las 4 cámaras)"""
        realtime_data = self.get_realtime_data()
        total_vehicles = sum(data['total'] for data in realtime_data.values())
        total_weighted = sum(data['weighted_total'] for data in realtime_data.values())
        
        # Calcular totales por tipo para el dashboard
        type_totals = {
            'carro': sum(data['carro'] for data in realtime_data.values()),
            'camion': sum(data['camion'] for data in realtime_data.values()),
            'bus': sum(data['bus'] for data in realtime_data.values()),
            'ambulancia': sum(data['ambulancia'] for data in realtime_data.values()),
            'mototaxi': sum(data['mototaxi'] for data in realtime_data.values())
        }
        
        return {
            'total_vehicles': total_vehicles,
            'total_weighted': total_weighted,
            'type_totals': type_totals,
            'congestion_level': self.get_congestion_level(total_weighted)
        }

# Instancia global del detector
traffic_detector = TrafficDetector('pytorch/best.pt')