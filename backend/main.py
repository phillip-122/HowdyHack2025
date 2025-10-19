from fastapi import FastAPI, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Any

import backend.database as db

app = FastAPI()

# Initialize database
db.init_db()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def score_video(file: UploadFile) -> float:
    # Placeholder for AI model scoring logic
    # In a real implementation, this would call the AI model & return its score
    return 7.5  # Example fixed score for demonstration

@app.get("/leaderboard")
def get_leaderboard()-> Any:
    return {"leaderboard": db.get_top_scores()}


@app.post("/submit_run")
async def submit_run(
    name: str = Form(...), 
    trick_name: str = Form(...), 
    video_file: UploadFile = Form(...))-> Any:
    # validate inputs
    if not video_file.filename or not video_file.filename.endswith(('.mov')):
        raise HTTPException(400, "Invalid file type. Please upload a video file.")
    if not name or name.strip() == "":
        raise HTTPException(400, "Skate Alias (name) must be a non-empty string.")
    if not trick_name or trick_name.strip() == "":
        raise HTTPException(400, "Trick name must be a non-empty string.")

    score = score_video(video_file) or 0.0
    
    # upload_submission will handle adding/updating user and their trick score
    success, msg = db.upload_submission(name, trick_name, score)
    if not success:
        raise HTTPException(400, msg)
    
    return [
    "success",
    {
        "name": name,
        "trick_name": trick_name,
        "score": score,
        "message": f"Run for {name}, {trick_name} submitted successfully!"
    }
]

    
#@app.get("/user/{username}") # get specific user's score