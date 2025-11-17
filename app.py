from flask import Flask, render_template, Response, jsonify
import cv2
import threading
from collections import Counter
from ultralytics import YOLO

model = YOLO(r"C:\Users\USUARIO\Documents\UTP\Innovacion y transformación digital\proyecto\best.pt")

source = 0 
cap = cv2.VideoCapture(source)

latest_metrics = {"status": "Iniciando...", "counts": {}}
lock = threading.Lock() 

def generate_frames():
    """Generador que procesa los frames de video con YOLO y los codifica."""
    global latest_metrics
    if not cap.isOpened():
        print("Error: No se puede abrir la fuente de video.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se puede leer el frame.")
            break

        results = model.predict(source=frame, show=False, stream=True) 
        
        for result in results:
            annotated_frame = result.plot()
            current_counts = {}

            if result.boxes is not None and len(result.boxes) > 0:
                class_ids = result.boxes.cls.tolist()
                class_names = [model.names[int(c)] for c in class_ids]
                current_counts = Counter(class_names)

                with lock:
                    latest_metrics = {"status": "Detectando", "counts": dict(current_counts)}
            else:
                with lock:
                    latest_metrics = {"status": "Sin detecciones", "counts": {}}
            
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

app = Flask(__name__)

@app.route('/')
def index():
    """Renderiza la página principal del dashboard."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Retorna la respuesta como un stream de imágenes JPEG (Motion JPEG)."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/metrics')
def get_metrics():
    """Retorna las métricas de conteo actuales como JSON."""
    with lock:
        return jsonify(latest_metrics)

if __name__ == '__main__':
    print("Servidor iniciado en http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port='5000', debug=False, threaded=True)