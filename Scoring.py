# type: ignore
# pylint: disable-all
# pyright: ignore

import cv2
import numpy as np
from ultralytics import YOLO

# -------------------------------
#  CONFIG
# -------------------------------
def score_video(video_path, trick):
    POSE_MODEL_PATH = "yolo11l-pose.pt"
    BOARD_MODEL_PATH = "Board_Model.pt"   # your trained skateboard detector
    VIDEO_PATH = video_path
    FPS = 30.0

    # Trick models (trained on 50 videos each)
    TRICK_MODELS = {
        "kickflip": "kickflip_model.pt",
        "ollie": "ollie_model.pt"
    }

    # Expected feature means from our training dataset
    EXPECTED_FEATURES = {
        "ollie": {
            "mean_dist": 79.0276641845703,
            "std_dist": 16.40071868896484,
            "std_board_angle": 10.663710594177246,
            "std_torso_angle": 10.90312957763672,
            "airtime": 0.23395061728395064
        },
        "kickflip": {
            "mean_dist": 82.902587890625,
            "std_dist": 87.01153564453125,
            "std_board_angle": 8.528315544128418,
            "std_torso_angle": 51.08692169189453,
            "airtime": 0.2009433962264151
        }
    }

    # -------------------------------
    #  INPUT TRICK NAME
    # -------------------------------
    TRICK_NAME = trick
    if TRICK_NAME not in TRICK_MODELS:
        raise ValueError(f"Invalid trick name '{TRICK_NAME}'. Must be one of: {list(TRICK_MODELS.keys())}")

    expected = EXPECTED_FEATURES[TRICK_NAME]

    # -------------------------------
    #  LOAD MODELS
    # -------------------------------
    pose_model = YOLO(POSE_MODEL_PATH)
    board_model = YOLO(BOARD_MODEL_PATH)

    cap = cv2.VideoCapture(VIDEO_PATH)

    distances = []
    board_angles = []
    torso_angles = []
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

        keypoints = pose_result.keypoints.xy[0].cpu().numpy()
        box = board_result.boxes.xyxy[0].cpu().numpy()

        dist = foot_board_distance(keypoints, box)
        ang_board = board_angle(box)
        ang_torso = torso_angle(keypoints)

        distances.append(dist)
        board_angles.append(ang_board)
        torso_angles.append(ang_torso)

        # Airtime detection
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

        # -------------------------------
        #  POST-PROCESSING & SCORING
        # -------------------------------
        if len(distances) > 0:
            mean_dist = np.mean(distances)
            std_dist = np.std(distances)
            std_board_angle = np.std(board_angles)
            std_torso_angle = np.std(torso_angles)
            airtime_seconds = airtime_frames_total / FPS

            actual_features = {
                "mean_dist": mean_dist,
                "std_dist": std_dist,
                "std_board_angle": std_board_angle,
                "std_torso_angle": std_torso_angle,
                "airtime": airtime_seconds
            }

            final_score = score_similarity(actual_features, expected)

            print("----------- RESULTS -----------")
            print(f"Trick: {TRICK_NAME.upper()}")
            for k, v in actual_features.items():
                print(f"{k:20s}: {v:.3f}")
            print(f"Final Trick Score: {final_score:.2f}/10")
        else:
            print("No skater/board detected for scoring.")


# -------------------------------
#  FEATURE FUNCTIONS
# -------------------------------
def foot_board_distance(keypoints, board_box):
    x1, y1, x2, y2 = board_box
    board_center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
    left_foot, right_foot = keypoints[15], keypoints[16]
    d_left = np.linalg.norm(left_foot - board_center)
    d_right = np.linalg.norm(right_foot - board_center)
    return (d_left + d_right) / 2

def board_angle(box):
    x1, y1, x2, y2 = box
    width, height = abs(x2 - x1), abs(y2 - y1)
    return np.degrees(np.arctan2(height, width))

def torso_angle(keypoints):
    left_shoulder, right_shoulder = keypoints[5], keypoints[6]
    left_hip, right_hip = keypoints[11], keypoints[12]
    mid_shoulder = (left_shoulder + right_shoulder) / 2
    mid_hip = (left_hip + right_hip) / 2
    dx, dy = mid_shoulder[0] - mid_hip[0], mid_shoulder[1] - mid_hip[1]
    return np.degrees(np.arctan2(dy, dx))

def is_airborne(dist, threshold=50):
    return dist > threshold

def score_similarity(actual, expected):
    """Compare feature vectors and return 0–10 score."""
    score = 0
    weights = {
        "mean_dist": 0.15,
        "std_dist": 0.15,
        "std_board_angle": 0.35,
        "std_torso_angle": 0.35,
        "airtime": 0.00
    }
    for key, weight in weights.items():
        if key in expected:
            diff = abs(actual[key] - expected[key])
            tol = expected[key] + 1e-5
            subscore = max(0, 1 / (1 + diff / tol))
            print(key, " --> ", subscore * weight * 10)
            score += subscore * weight * 10
    return score

# -------------------------------
#  PROCESS VIDEO
# -------------------------------
