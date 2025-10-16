# =============================
# 1. Instalar dependencias
# =============================
# Ejecuta solo una vez en la terminal o entorno virtual:
# pip install ultralytics opencv-python tqdm

# =============================
# 2. Importar librerías
# =============================
from ultralytics import YOLO
import cv2
from collections import Counter
from tqdm import tqdm  # Barra de progreso

# =============================
# 3. Cargar modelo YOLO
# =============================
model = YOLO(r"C:\Users\USUARIO\Documents\UTP\Innovacion y transformación digital\proyecto\best.pt")

# =============================
# 4. Configurar rutas de video
# =============================
video_path = r"C:\Users\USUARIO\Documents\UTP\Innovacion y transformación digital\videoplayback3.mp4"
output_path = r"C:\Users\USUARIO\Documents\UTP\Innovacion y transformación digital\proyecto\resultado_video3.mp4"

# =============================
# 5. Abrir video
# =============================
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("❌ No se pudo abrir el video.")
    exit()

fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Configurar salida de video
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

# =============================
# 6. Procesamiento silencioso frame a frame
# =============================
total_counts = Counter()

with tqdm(total=frame_count, desc="Procesando video", unit="frame") as pbar:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detección con YOLO
        results = model(frame)
        result = results[0]
        annotated_frame = result.plot()

        # Contar objetos detectados
        if result.boxes is not None and len(result.boxes) > 0:
            class_ids = result.boxes.cls.tolist()
            class_names = [model.names[int(c)] for c in class_ids]
            frame_counts = Counter(class_names)
            total_counts.update(frame_counts)

        # Guardar frame procesado en el nuevo video
        out.write(annotated_frame)

        pbar.update(1)

# =============================
# 7. Cerrar recursos y mostrar resumen final
# =============================
cap.release()
out.release()

print("\n✅ Procesamiento terminado.")
print(f"🎥 Video guardado en: {output_path}")

if total_counts:
    print("\n=== Conteo total de objetos detectados ===")
    for cls_name, num in total_counts.items():
        print(f"{cls_name}: {num}")
else:
    print("No se detectaron objetos en el video.")

