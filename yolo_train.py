from ultralytics import YOLO
model = YOLO("yolo11s.pt")
data_path = r"C:\Users\USUARIO\Documents\UTP\Innovacion y transformación digital\proyecto\Ambulancia-2\data.yaml"
results = model.train(data=data_path, epochs=15, imgsz=640)

