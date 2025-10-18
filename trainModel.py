from ultralytics import YOLO

model = YOLO("yolo11l-pose.pt")  # load an official model
# model = YOLO("path/to/best.pt")  # load a custom model

# Predict with the model
results = model.predict(r"C:\Users\Phillip\Desktop\coding projects\HowdyHack2025\HowdyHack2025\Tricks_Ollie_Ollie0.mov", show=True, save=True)  # predict on an image
#model.predict or model.track

# Access the results
for result in results:
    xy = result.keypoints.xy  # x and y coordinates
    xyn = result.keypoints.xyn  # normalized
    kpts = result.keypoints.data  # x, y, visibility (if available)