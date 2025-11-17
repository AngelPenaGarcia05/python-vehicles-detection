from time import time
from flask import Blueprint, render_template, Response, jsonify, session
from src.auth.decorators import login_required
from src.traffic.detection import generate_frames
from src.traffic.simulation import traffic_simulation

traffic_bp = Blueprint('traffic', __name__)

@traffic_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('traffic/dashboard.html', 
                         username=session.get('username'),
                         num_cameras=4)

@traffic_bp.route('/video_feed/<int:camera_id>')
@login_required
def video_feed(camera_id):
    if camera_id < 0 or camera_id >= 4:
        return "Cámara no válida", 404
    
    return Response(
        generate_frames(camera_id),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@traffic_bp.route('/metrics')
@login_required
def get_metrics():
    try:
        metrics = traffic_simulation.get_metrics()
        return jsonify(metrics)
    except Exception as e:
        print(f"❌ Error en endpoint /metrics: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@traffic_bp.route('/debug')
@login_required
def debug_info():
    """Endpoint de debug para verificar el estado"""
    debug_info = {
        "system_running": traffic_simulation.running,
        "cameras_configured": 4,
        "timestamp": time.time()
    }
    return jsonify(debug_info)