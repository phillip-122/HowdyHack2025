import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO
import json
import os

# -------------------------------
#  CONFIG
# -------------------------------
POSE_MODEL_PATH = "yolo11l-pose.pt"
BOARD_MODEL_PATH = "Board_Model.pt"   # your trained skateboard model
TRAINING_DIR = r"C:\Users\varai\Documents\Github Vrain\HowdyHack2025\Tricks\Kickflip"   # folder with your 50 videos
OUTPUT_JSON = "kickflip_features.json"
FPS = 30.0

# -------------------------------
#  LOAD MODELS
# -------------------------------
pose_model = YOLO(POSE_MODEL_PATH)
board_model = YOLO(BOARD_MODEL_PATH)
box_annotator = sv.BoxAnnotator()

# -------------------------------
#  FEATURE FUNCTIONS
# -------------------------------
def foot_board_distance(keypoints, board_box):
    """Average distance between both feet and skateboard center."""
    x1, y1, x2, y2 = board_box
    board_center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
    left_foot = keypoints[15]
    right_foot = keypoints[16]
    d_left = np.linalg.norm(left_foot - board_center)
    d_right = np.linalg.norm(right_foot - board_center)
    return (d_left + d_right) / 2

def board_angle(box):
    """Rough horizontal orientation of the board box."""
    x1, y1, x2, y2 = box
    return np.degrees(np.arctan2(y2 - y1, x2 - x1))

def torso_angle(keypoints):
    """Torso tilt relative to vertical."""
    shoulder = keypoints[5]
    hip = keypoints[11]
    dx, dy = shoulder - hip
    return np.degrees(np.arctan2(dx, dy))

def is_airborne(dist, threshold=50):
    return dist > threshold

def compute_video_features(video_path):
    """Run pose+board models on a video and extract summary stats."""
    cap = cv2.VideoCapture(video_path)
    distances, board_angles, torso_angles = [], [], []
    airtime_frames_total = 0
    airborne = False
    airtime_frames_current = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        pose_result = pose_model(frame, verbose=False)[0]
        board_result = board_model(frame, verbose=False)[0]

        if pose_result.keypoints is None or len(board_result.boxes) == 0:
            continue
        if (len(pose_result.keypoints.xy) == 0):
            continue
        if (len(board_result.boxes.xyxy) == 0):
            continue
        keypoints = pose_result.keypoints.xy[0].cpu().numpy()
        box = board_result.boxes.xyxy[0].cpu().numpy()

        dist = foot_board_distance(keypoints, box)
        ang_b = board_angle(box)
        ang_t = torso_angle(keypoints)

        distances.append(dist)
        board_angles.append(ang_b)
        torso_angles.append(ang_t)

        if is_airborne(dist):
            if not airborne:
                airborne = True
                airtime_frames_current = 0
            airtime_frames_current += 1
        else:
            if airborne:
                airborne = False
                airtime_frames_total += airtime_frames_current

    cap.release()

    if len(distances) == 0:
        return None

    mean_distance = np.mean(distances)
    std_distance = np.std(distances)
    std_board_angle = np.std(board_angles)
    std_torso_angle = np.std(torso_angles)
    airtime_seconds = airtime_frames_total / FPS

    return {
        "mean_distance": mean_distance,
        "std_distance": std_distance,
        "std_board_angle": std_board_angle,
        "std_torso_angle": std_torso_angle,
        "airtime": airtime_seconds
    }

# -------------------------------
#  RUN ON ALL VIDEOS
# -------------------------------
all_features = []

for filename in os.listdir(TRAINING_DIR):
    if not filename.lower().endswith((".mp4", ".mov", ".avi")):
        continue

    path = os.path.join(TRAINING_DIR, filename)
    print(f"Processing {path} ...")
    feats = compute_video_features(path)
    if feats:
        all_features.append(feats)
    else:
        print(f"⚠️ Skipped {filename} (no detections)")

# -------------------------------
#  COMPUTE AVERAGES
# -------------------------------
if len(all_features) > 0:
    keys = all_features[0].keys()
    avg_features = {k: np.mean([f[k] for f in all_features]) for k in keys}
    std_features = {k: np.std([f[k] for f in all_features]) for k in keys}

    result = {
        "videos": len(all_features),
        "mean": avg_features,
        "std": std_features
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(result, f, indent=2)

    print("\n✅ Saved averaged kickflip features to:", OUTPUT_JSON)
    print(json.dumps(result, indent=2))
else:
    print("No valid videos processed.")
