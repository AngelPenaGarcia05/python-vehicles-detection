def get_congestion_level(vehicle_count):
    """Determina el nivel de congestión basado en el conteo"""
    if vehicle_count <= 2:
        return "Bajo", "success"
    elif vehicle_count <= 5:
        return "Moderado", "warning"
    else:
        return "Alto", "danger"