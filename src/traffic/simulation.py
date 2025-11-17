import time
import threading
from config import Config
from src.utils.helpers import get_congestion_level
from src.traffic.detection import video_processor

class TrafficSimulation:
    def __init__(self):
        self.traffic_state = {
            "cameras": {},
            "traffic_lights": {"north_south": "green", "east_west": "red"},
            "last_light_change": time.time()
        }
        
        # Inicializar estado de cámaras
        for i in range(len(Config.VIDEO_PATHS)):
            self.traffic_state["cameras"][i] = {
                "count": 0,
                "classes": {},
                "congestion": "Bajo",
                "congestion_badge": "success"
            }
        
        print("✅ Sistema de tráfico inicializado")
        
        # Iniciar actualización
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def _update_loop(self):
        """Bucle principal de actualización"""
        update_count = 0
        
        while self.running:
            try:
                self._update_camera_metrics()
                self._update_traffic_lights()
                
                update_count += 1
                if update_count % 10 == 0:  # Log cada 20 segundos
                    total = sum(cam["count"] for cam in self.traffic_state["cameras"].values())
                    print(f"📊 Update {update_count}: {total} vehículos totales")
                
                time.sleep(2)  # Actualizar cada 2 segundos
                
            except Exception as e:
                print(f"❌ Error en bucle de actualización: {e}")
                time.sleep(5)
    
    def _update_camera_metrics(self):
        """Actualiza las métricas de todas las cámaras"""
        total_vehicles = 0
        
        for cam_id in range(len(Config.VIDEO_PATHS)):
            # Obtener datos reales del procesador de video
            count, classes = video_processor.get_metrics(cam_id)
            level, badge = get_congestion_level(count)
            
            self.traffic_state["cameras"][cam_id] = {
                "count": count,
                "classes": classes,
                "congestion": level,
                "congestion_badge": badge
            }
            
            total_vehicles += count
            
            # Debug individual
            if count > 0:
                print(f"📷 Cámara {cam_id}: {count} vehículos")
        
        # Debug general
        if total_vehicles > 0:
            print(f"🚗 TOTAL: {total_vehicles} vehículos detectados")
    
    def _update_traffic_lights(self):
        """Actualiza los semáforos basado en el tráfico"""
        current_time = time.time()
        time_since_change = current_time - self.traffic_state["last_light_change"]
        
        # Calcular tráfico por dirección
        ns_traffic = self.traffic_state["cameras"][0]["count"] + self.traffic_state["cameras"][2]["count"]
        ew_traffic = self.traffic_state["cameras"][1]["count"] + self.traffic_state["cameras"][3]["count"]
        
        current_green = "north_south" if self.traffic_state["traffic_lights"]["north_south"] == "green" else "east_west"
        
        # Lógica de cambio
        should_change = False
        
        if time_since_change > 20:  # Mínimo 20 segundos
            if current_green == "north_south" and ew_traffic > ns_traffic + 2:
                should_change = True
                print(f"🔄 Cambiando a E-W (N-S: {ns_traffic}, E-W: {ew_traffic})")
            elif current_green == "east_west" and ns_traffic > ew_traffic + 2:
                should_change = True
                print(f"🔄 Cambiando a N-S (N-S: {ns_traffic}, E-W: {ew_traffic})")
            elif time_since_change > 30:  # Máximo 30 segundos
                should_change = True
                print("⏰ Cambio por tiempo")
        
        if should_change:
            self._change_lights()
    
    def _change_lights(self):
        """Cambia los semáforos"""
        # Fase amarilla
        if self.traffic_state["traffic_lights"]["north_south"] == "green":
            self.traffic_state["traffic_lights"]["north_south"] = "yellow"
        else:
            self.traffic_state["traffic_lights"]["east_west"] = "yellow"
        
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
    
    def get_metrics(self):
        """Obtiene todas las métricas actuales"""
        try:
            metrics = {
                "cameras": {},
                "traffic_lights": self.traffic_state["traffic_lights"].copy(),
                "total_vehicles": 0,
                "overall_congestion": "Bajo",
                "overall_congestion_badge": "success"
            }
            
            total_vehicles = 0
            camera_counts = []
            
            # Recolectar datos de todas las cámaras
            for cam_id, cam_data in self.traffic_state["cameras"].items():
                metrics["cameras"][cam_id] = cam_data
                total_vehicles += cam_data["count"]
                camera_counts.append(cam_data["count"])
            
            metrics["total_vehicles"] = total_vehicles
            
            # Calcular congestión general
            if camera_counts:
                avg_vehicles = total_vehicles / len(camera_counts)
                overall_level, overall_badge = get_congestion_level(avg_vehicles)
                metrics["overall_congestion"] = overall_level
                metrics["overall_congestion_badge"] = overall_badge
            
            print(f"📈 Métricas enviadas: {total_vehicles} vehículos")
            return metrics
            
        except Exception as e:
            print(f"❌ Error obteniendo métricas: {e}")
            return self._get_fallback_metrics()
    
    def _get_fallback_metrics(self):
        """Métricas de fallback"""
        return {
            "cameras": {i: {"count": 0, "classes": {}, "congestion": "Bajo", "congestion_badge": "success"} 
                       for i in range(4)},
            "traffic_lights": {"north_south": "green", "east_west": "red"},
            "total_vehicles": 0,
            "overall_congestion": "Bajo",
            "overall_congestion_badge": "success"
        }
    
    def stop(self):
        """Detiene el sistema"""
        self.running = False
        video_processor.stop()

# Instancia global
traffic_simulation = TrafficSimulation()