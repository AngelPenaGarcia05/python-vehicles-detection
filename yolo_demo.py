import cv2
import time
from ultralytics import YOLO

# --- CONFIG ---
RTSP_URL = "rtsp://admin:admin123456@192.168.156.211:8554/profile0"
CONFIDENCE_THRESHOLD = 0.35  # umbral de confianza mínimo para mostrarse
MODEL_NAME = "yolo11n.pt"    # modelo ligero; cambia por yolov8m.pt si quieres más precisión
# ----------------

def main():
    # Carga del modelo (descarga automática si no existe)
    print("Cargando modelo YOLO...")
    model = YOLO(MODEL_NAME)

    # Abrir stream RTSP
    print(f"Abriendo stream: {RTSP_URL}")
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        print("ERROR: no se pudo abrir el stream RTSP. Revisa la URL y la conectividad.")
        return

    fps_time = time.time()
    frame_count = 0
    fps = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("No se recibió frame (stream detenido o pérdida de conexión).")
                break

            frame_count += 1
            # Ejecutar inferencia (devuelve lista de resultados; usamos el primero)
            results = model(frame, verbose=False, device='cpu')  # usa 'cuda' si tienes GPU configurada
            # results puede contener uno o más objetos; normalmente results[0] es lo que necesitamos
            if len(results) > 0:
                res = results[0]
                # cajas: res.boxes.xyxy, clases: res.boxes.cls, confidencias: res.boxes.conf
                boxes = res.boxes.xyxy.cpu().numpy()   # [[x1,y1,x2,y2], ...]
                classes = res.boxes.cls.cpu().numpy().astype(int)
                confidences = res.boxes.conf.cpu().numpy()

                for box, cls_idx, conf in zip(boxes, classes, confidences):
                    if conf < CONFIDENCE_THRESHOLD:
                        continue
                    class_name = model.names.get(cls_idx, str(cls_idx))
                    # Filtrar solo 'laptop'
                    if class_name.lower() == "mouse":
                        x1, y1, x2, y2 = map(int, box)
                        # Dibujar rectángulo y etiqueta
                        label = f"{class_name} {conf:.2f}"
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 0), 2)
                        cv2.putText(frame, label, (x1, y1 - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)

            # Calcular FPS cada segundo
            if (time.time() - fps_time) >= 1.0:
                fps = frame_count / (time.time() - fps_time)
                fps_time = time.time()
                frame_count = 0

            # Mostrar FPS en pantalla
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            cv2.imshow("Deteccion - laptop", frame)

            # Salir con 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Saliendo por solicitud del usuario.")
                break

    except KeyboardInterrupt:
        print("Interrupción por teclado.")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
