from ultralytics import YOLO
import cv2
from collections import Counter

model = YOLO(r"C:\Users\USUARIO\Documents\UTP\Innovacion y transformación digital\proyecto\best.pt")

source = 0

for result in model.track(source=source, show=False, stream=True, persist=True):
    frame = result.plot()

    if result.boxes is not None and len(result.boxes) > 0:
        class_ids = result.boxes.cls.tolist()
        class_names = [model.names[int(c)] for c in class_ids]

        counts = Counter(class_names)

        y_offset = 30
        for cls_name, num in counts.items():
            text = f"{cls_name}: {num}"
            cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            y_offset += 30
    else:
        cv2.putText(frame, "Sin detecciones", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imshow("YOLO - Conteo de objetos", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
