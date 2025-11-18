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
            # Si no hay procesamiento, mostrar video normal
            cap = cv2.VideoCapture(Config.VIDEO_PATHS[camera_id])
            while traffic_detector.processing is False and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
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
    detection_data = traffic_detector.get_detection_data()
    
    # Calcular totales
    total_vehicles = sum(data['total'] for data in detection_data.values())
    total_congestion = traffic_detector.get_congestion_level(total_vehicles)
    
    # Determinar estado de semáforos basado en congestión
    semaphore_1_state = total_congestion
    semaphore_2_state = 'low' if total_congestion == 'high' else 'high' if total_congestion == 'low' else 'medium'
    
    return render_template('traffic/dashboard.html', 
                         detection_data=detection_data,
                         total_vehicles=total_vehicles,
                         total_congestion=total_congestion,
                         semaphore_1_state=semaphore_1_state,
                         semaphore_2_state=semaphore_2_state,
                         processing=traffic_detector.processing)

@traffic_bp.route('/video_feed/<int:camera_id>')
@login_required
def video_feed(camera_id):
    return Response(generate_frames(camera_id),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@traffic_bp.route('/camera/<int:camera_id>')
@login_required
def camera_detail(camera_id):
    detection_data = traffic_detector.get_detection_data(camera_id)
    congestion_level = traffic_detector.get_congestion_level(detection_data['total'])
    
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

@traffic_bp.route('/api/detection_data')
@login_required
def api_detection_data():
    detection_data = traffic_detector.get_detection_data()
    total_vehicles = sum(data['total'] for data in detection_data.values())
    total_congestion = traffic_detector.get_congestion_level(total_vehicles)
    
    return jsonify({
        'detection_data': detection_data,
        'total_vehicles': total_vehicles,
        'total_congestion': total_congestion,
        'processing': traffic_detector.processing
    })