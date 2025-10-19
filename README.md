# Howdy Hack 2025 Skating Skill Scoring App

> AI-powered skating trick analysis using computer vision

![FastAPI](https://img.shields.io/badge/api-FastAPI-teal) ![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![YOLOv8](https://img.shields.io/badge/detection-YOLO11-orange) ![License](https://img.shields.io/badge/license-MIT-green)

---

<h2>Description</h2>
This project analyzes skating trick videos using computer vision to automatically score tricks based on factors such as distance from board after jumping, skateboard angle, torso angle, and airtime. Skaters upload clips of their tricks, and recieve a score based on how well they performed the trick.
<br><br>
Skaters can compare their results to other skaters that performed the same trick, trying to get on a global leaderboard. As a skater improves their skills, they can retry a trick to see an improved score, competing against friends for a better score.
<br />

<h2>Features </h2>

- <b>Person Pose Detection:</b> Uses YOLO11 for real-time person pose detection
- <b>Skateboard Detection:</b> Trained a custom YOLO model to detect skateboards
- <b>Trick Scoring System:</b> Determines score of a skating trick using computer vision
- <b>Leaderboard:</b> Stores and displays the top scoring skater scores
- <b>Video Uploads:</b> Upload your skating trick video and get scored

<h2>Tech Stack</h2>

- <b>Python</b>
- <b>FastAPI</b> 
- <b>Ultralytics YOLO11</b>
- <b>Supervision</b> (Roboflow's tracking & annotation toolkit)
- <b>Javascript</b>
- <b>HTML</b>
- <b>Tailwind CSS</b>
- <b>SQLite3</b>
