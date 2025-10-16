from roboflow import Roboflow
rf = Roboflow(api_key="KuWodoCFkMJynQ99HkyM")
project = rf.workspace("detector-de-imagenes-ypu2y").project("ambulancia-wnf32-ua7ah")
version = project.version(2)
dataset = version.download("yolov11")
                