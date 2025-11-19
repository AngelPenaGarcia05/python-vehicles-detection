from flask import Blueprint, render_template, Response, jsonify, request
from src.auth.decorators import login_required
from src.traffic.detection import traffic_detector
from config import Config
import cv2
import time

traffic_bp = Blueprint('traffic', __name__)

def generate_frames(camera_id):
    while True:
        if traffic_detector.processing:
            frame_bytes = traffic_detector.get_frame(camera_id)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Si no hay frame procesado, mostrar video normal
                yield from generate_normal_video(camera_id)
        else:
            # Si no hay procesamiento, mostrar video normal
            yield from generate_normal_video(camera_id)

def generate_normal_video(camera_id):
    cap = cv2.VideoCapture(Config.VIDEO_PATHS[camera_id])
    while traffic_detector.processing is False and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        # Añadir texto indicando que el procesamiento está desactivado
        cv2.putText(frame, "PROCESAMIENTO DESACTIVADO", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03)
    cap.release()

@traffic_bp.route('/')
@traffic_bp.route('/dashboard')
@login_required
def dashboard():
    # Obtener datos para el dashboard
    dashboard_totals = traffic_detector.get_dashboard_totals()
    total_vehicles = dashboard_totals['total_vehicles']
    total_weighted = dashboard_totals['total_weighted']
    type_totals = dashboard_totals['type_totals']
    total_congestion = dashboard_totals['congestion_level']
    
    # Obtener datos individuales de cada cámara
    cameras_data = traffic_detector.get_realtime_data()
    
    # Obtener estados de semáforos
    semaphore_states = traffic_detector.get_semaphore_states()
    emergency_mode = traffic_detector.get_emergency_mode()
    
    # Calcular congestión de grupos para la plantilla
    group_congestion = {
        'group_1': traffic_detector.get_group_congestion('group_1'),
        'group_2': traffic_detector.get_group_congestion('group_2')
    }
    
    return render_template('traffic/dashboard.html', 
                         cameras_data=cameras_data,
                         total_vehicles=total_vehicles,
                         total_weighted=total_weighted,
                         type_totals=type_totals,
                         total_congestion=total_congestion,
                         semaphore_states=semaphore_states,
                         emergency_mode=emergency_mode,
                         group_congestion=group_congestion,
                         processing=traffic_detector.processing)

@traffic_bp.route('/video_feed/<int:camera_id>')
@login_required
def video_feed(camera_id):
    return Response(generate_frames(camera_id),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@traffic_bp.route('/camera/<int:camera_id>')
@login_required
def camera_detail(camera_id):
    # Usar datos en tiempo real (no acumulados)
    detection_data = traffic_detector.get_realtime_data(camera_id) or {
        'total': 0, 'carro': 0, 'camion': 0, 'bus': 0, 'ambulancia': 0, 'mototaxi': 0, 'weighted_total': 0
    }
    congestion_level = traffic_detector.get_congestion_level(detection_data['weighted_total'])
    
    return render_template('traffic/camera_detail.html',
                         camera_id=camera_id,
                         detection_data=detection_data,
                         congestion_level=congestion_level,
                         processing=traffic_detector.processing)

@traffic_bp.route('/toggle_processing', methods=['POST'])
@login_required
def toggle_processing():
    if traffic_detector.processing:
        traffic_detector.stop_processing()
    else:
        traffic_detector.start_processing(Config.VIDEO_PATHS)
    
    return jsonify({'processing': traffic_detector.processing})

@traffic_bp.route('/reset_accumulated', methods=['POST'])
@login_required
def reset_accumulated():
    camera_id = request.json.get('camera_id') if request.json else None
    traffic_detector.reset_accumulated_data(camera_id)
    
    if camera_id is not None:
        return jsonify({'message': f'Datos acumulados de cámara {camera_id} reiniciados'})
    else:
        return jsonify({'message': 'Todos los datos acumulados reiniciados'})

@traffic_bp.route('/api/detection_data')
@login_required
def api_detection_data():
    # Datos para el dashboard (suma de todas las cámaras)
    dashboard_totals = traffic_detector.get_dashboard_totals()
    total_vehicles = dashboard_totals['total_vehicles']
    type_totals = dashboard_totals['type_totals']
    total_congestion = dashboard_totals['congestion_level']
    
    # Datos individuales de cada cámara
    cameras_data = traffic_detector.get_realtime_data()
    
    # Congestión de grupos
    group_congestion = {
        'group_1': traffic_detector.get_group_congestion('group_1'),
        'group_2': traffic_detector.get_group_congestion('group_2')
    }
    
    return jsonify({
        'dashboard_totals': {
            'total_vehicles': total_vehicles,
            'type_totals': type_totals,
            'congestion_level': total_congestion
        },
        'cameras_data': cameras_data,
        'group_congestion': group_congestion,
        'processing': traffic_detector.processing
    })

@traffic_bp.route('/api/camera_data/<int:camera_id>')
@login_required
def api_camera_data(camera_id):
    # Usar datos en tiempo real (no acumulados)
    detection_data = traffic_detector.get_realtime_data(camera_id) or {
        'total': 0, 'carro': 0, 'camion': 0, 'bus': 0, 'ambulancia': 0, 'mototaxi': 0, 'weighted_total': 0
    }
    congestion_level = traffic_detector.get_congestion_level(detection_data['weighted_total'])
    
    return jsonify({
        'camera_id': camera_id,
        'detection_data': detection_data,
        'congestion_level': congestion_level
    })

@traffic_bp.route('/api/semaphore_data')
@login_required
def api_semaphore_data():
    """API para obtener datos de semáforos"""
    semaphore_states = traffic_detector.get_semaphore_states()
    emergency_mode = traffic_detector.get_emergency_mode()
    
    # Calcular congestión de grupos
    group_congestion = {
        'group_1': traffic_detector.get_group_congestion('group_1'),
        'group_2': traffic_detector.get_group_congestion('group_2')
    }
    
    return jsonify({
        'semaphore_states': semaphore_states,
        'emergency_mode': emergency_mode,
        'group_congestion': group_congestion
    })