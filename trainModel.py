# type: ignore
# pylint: disable-all
# pyright: ignore

from ultralytics import YOLO

def main(): 
    model = YOLO("yolov8l.pt")

    results = model.train(
        data=r"wheelsTraining\data.yaml",
        epochs=50,
        imgsz=640,
        batch=16,
        project="runs/detect/skateboards_train",
        name="train1",
        exist_ok=True
    )

if __name__ == "__main__":
    main()
