import time
import threading
from config import Config
from src.utils.helpers import get_congestion_level
from src.traffic.detection import video_processor

class TrafficSimulation:
    def __init__(self):
        self.traffic_state = {
            "cameras": {},
            "traffic_lights": {
                "north_south": "green",
                "east_west": "red"
            },
            "last_light_change": time.time(),
            "light_cycle": Config.LIGHT_CYCLE,
            "ai_enabled": True
        }
        
        # Inicializar cámaras con datos reales
        for i in range(len(Config.VIDEO_PATHS)):
            self.traffic_state["cameras"][i] = {
                "count": 0,
                "classes": {},
                "congestion": "Bajo",
                "congestion_badge": "success",
                "detections": [],
                "last_update": time.time()
            }
        
        print("✅ Sistema de tráfico inicializado")
        
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def _update_loop(self):
        """Bucle principal de actualización"""
        update_counter = 0
        
        while self.running:
            try:
                self._update_camera_metrics()
                self._update_traffic_lights()
                
                update_counter += 1
                # Log cada 15 actualizaciones (≈30 segundos)
                if update_counter % 15 == 0:
                    total_vehicles = sum(cam["count"] for cam in self.traffic_state["cameras"].values())
                    print(f"📊 Sistema activo - Total vehículos: {total_vehicles}")
                
                time.sleep(2)  # Actualizar cada 2 segundos
                
            except Exception as e:
                print(f"❌ Error en bucle de actualización: {e}")
                time.sleep(5)
    
    def _update_camera_metrics(self):
        """Actualiza las métricas de todas las cámaras con datos reales"""
        total_vehicles = 0
        
        for cam_id in range(len(Config.VIDEO_PATHS)):
            # Obtener datos REALES del procesador de video
            count, classes, detections = video_processor.get_metrics(cam_id)
            level, badge = get_congestion_level(count)
            
            # Actualizar con datos reales
            self.traffic_state["cameras"][cam_id] = {
                "count": count,
                "classes": classes,
                "congestion": level,
                "congestion_badge": badge,
                "detections": detections,
                "last_update": time.time()
            }
            
            total_vehicles += count
            
            # Debug: mostrar cambios significativos
            if count > 0 and len(detections) > 0:
                print(f"📷 Cámara {cam_id}: {count} vehículos - {classes}")
        
        # Debug general periódico
        if int(time.time()) % 30 == 0:  # Cada 30 segundos
            print(f"🚗 Resumen - Total: {total_vehicles} vehículos")
            for cam_id, data in self.traffic_state["cameras"].items():
                print(f"   Cam {cam_id + 1}: {data['count']} vehículos")
    
    def _update_traffic_lights(self):
        """Actualiza semáforos basado en tráfico REAL"""
        current_time = time.time()
        time_since_change = current_time - self.traffic_state["last_light_change"]
        
        # Calcular tráfico REAL por dirección
        ns_traffic = (self.traffic_state["cameras"][0]["count"] + 
                     self.traffic_state["cameras"][2]["count"])
        ew_traffic = (self.traffic_state["cameras"][1]["count"] + 
                     self.traffic_state["cameras"][3]["count"])
        
        current_green = "north_south" if self.traffic_state["traffic_lights"]["north_south"] == "green" else "east_west"
        
        print(f"🚦 Tráfico - N-S: {ns_traffic}, E-W: {ew_traffic}, Verde: {current_green}")
        
        # Lógica de cambio mejorada
        if time_since_change > Config.MIN_CYCLE_TIME:
            imbalance = abs(ns_traffic - ew_traffic)
            
            if current_green == "north_south" and ew_traffic > ns_traffic + 3 and imbalance > 4:
                print("🔄 Cambiando a E-W (más tráfico)")
                self._change_lights()
            elif current_green == "east_west" and ns_traffic > ew_traffic + 3 and imbalance > 4:
                print("🔄 Cambiando a N-S (más tráfico)")
                self._change_lights()
            elif time_since_change > self.traffic_state["light_cycle"]:
                print("⏰ Cambio por tiempo")
                self._change_lights()
    
    def _change_lights(self):
        """Cambia los semáforos"""
        try:
            # Fase amarilla
            if self.traffic_state["traffic_lights"]["north_south"] == "green":
                self.traffic_state["traffic_lights"]["north_south"] = "yellow"
                print("🟡 N-S amarillo, E-W rojo")
            else:
                self.traffic_state["traffic_lights"]["east_west"] = "yellow"
                print("🟡 E-W amarillo, N-S rojo")
            
            time.sleep(2)  # 2 segundos en amarillo
            
            # Cambio completo
            if self.traffic_state["traffic_lights"]["north_south"] == "yellow":
                self.traffic_state["traffic_lights"]["north_south"] = "red"
                self.traffic_state["traffic_lights"]["east_west"] = "green"
                print("🔴 N-S rojo, 🟢 E-W verde")
            else:
                self.traffic_state["traffic_lights"]["north_south"] = "green"
                self.traffic_state["traffic_lights"]["east_west"] = "red"
                print("🟢 N-S verde, 🔴 E-W rojo")
            
            self.traffic_state["last_light_change"] = time.time()
            
        except Exception as e:
            print(f"❌ Error cambiando semáforos: {e}")
    
    def get_metrics(self):
        """Obtiene todas las métricas ACTUALES"""
        try:
            metrics = {
                "cameras": {},
                "traffic_lights": self.traffic_state["traffic_lights"].copy(),
                "total_vehicles": 0,
                "overall_congestion": "Bajo",
                "overall_congestion_badge": "success",
                "ai_enabled": self.traffic_state["ai_enabled"],
                "timestamp": time.time()
            }
            
            total_vehicles = 0
            camera_counts = []
            
            # Recolectar datos REALES de todas las cámaras
            for cam_id, cam_data in self.traffic_state["cameras"].items():
                metrics["cameras"][cam_id] = cam_data
                total_vehicles += cam_data["count"]
                camera_counts.append(cam_data["count"])
            
            metrics["total_vehicles"] = total_vehicles
            
            # Calcular congestión general basada en datos REALES
            if camera_counts:
                avg_vehicles = total_vehicles / len(camera_counts)
                overall_level, overall_badge = get_congestion_level(avg_vehicles)
                metrics["overall_congestion"] = overall_level
                metrics["overall_congestion_badge"] = overall_badge
            
            print(f"📈 Métricas enviadas: {total_vehicles} vehículos totales")
            return metrics
            
        except Exception as e:
            print(f"❌ Error obteniendo métricas: {e}")
            return self._get_fallback_metrics()
    
    def _get_fallback_metrics(self):
        """Métricas de fallback"""
        return {
            "cameras": {i: {"count": 0, "classes": {}, "congestion": "Bajo", "congestion_badge": "success", "detections": []} 
                       for i in range(4)},
            "traffic_lights": {"north_south": "green", "east_west": "red"},
            "total_vehicles": 0,
            "overall_congestion": "Bajo",
            "overall_congestion_badge": "success",
            "ai_enabled": True
        }
    
    def get_camera_metrics(self, camera_id):
        """Obtiene métricas específicas de una cámara"""
        if camera_id in self.traffic_state["cameras"]:
            return self.traffic_state["cameras"][camera_id]
        return None
    
    def toggle_ai_analysis(self):
        """Activa/desactiva el análisis de IA"""
        new_status = video_processor.toggle_ai_analysis()
        self.traffic_state["ai_enabled"] = new_status
        return new_status
    
    def get_ai_status(self):
        """Obtiene estado del análisis de IA"""
        return self.traffic_state["ai_enabled"]
    
    def stop(self):
        """Detiene el sistema"""
        self.running = False
        video_processor.stop()

# Instancia global
traffic_simulation = TrafficSimulation()