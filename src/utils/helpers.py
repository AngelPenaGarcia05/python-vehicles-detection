def get_congestion_color(level):
    colors = {
        'low': 'success',
        'medium': 'warning', 
        'high': 'danger'
    }
    return colors.get(level, 'secondary')

def get_congestion_text(level):
    texts = {
        'low': 'Baja',
        'medium': 'Media',
        'high': 'Alta'
    }
    return texts.get(level, 'Desconocida')