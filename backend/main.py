from fastapi import FastAPI, Form, UploadFile, HTTPException, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
import os
import tempfile

import backend.database as db
from Scoring import score_video as ai_score_video  # type: ignore

app = FastAPI()

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app.mount("/static", StaticFiles(directory=ROOT_DIR), name="static")

@app.get("/")
async def index():
    return FileResponse(os.path.join(ROOT_DIR, "upload.html"))

@app.get("/favicon.ico")
async def favicon():
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'>"
        "<rect width='100%' height='100%' fill='#500000'/>"
        "<text x='50%' y='55%' font-size='10' text-anchor='middle' fill='white' font-family='Inter, sans-serif'>A</text>"
        "</svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")

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

def score_video(file: UploadFile, trick_name: str) -> float:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mov") as temp_file:
        # Read and write file content
        content = file.file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Call AI scoring function
        score = ai_score_video(temp_file_path, trick_name)
        return float(score) if score is not None else 0.0
    except Exception as e:
        print(f"Error in AI scoring: {e}")
        return 7.5  # Fallback score if AI fails
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/leaderboard")
def get_leaderboard() -> Any:
    try:
        scores = db.get_top_scores()
        # Convert to format frontend expects
        leaderboard_data = []
        for row in scores:
            # Get user's best trick for display
            tricks = db.get_user_tricks(row['name'])
            best_trick = tricks[0]['trick_name'] if tricks else "N/A"

            leaderboard_data.append({
                "name": row['name'],
                "trick_name": best_trick,
                "score": row['total_score']
            })

        return ["success", leaderboard_data]  # Format frontend expects
    except Exception as e:
        return [f"error: {str(e)}", []]


@app.post("/submit_run")
async def submit_run(
    name: str = Form(...),
    trick_name: str = Form(...),
    video_file: UploadFile = File(...)
) -> Any:
    # validate inputs
    if not video_file.filename or not video_file.filename.lower().endswith('.mov'):
        raise HTTPException(400, "Invalid file type. Please upload a .mov video file.")
    if not name or name.strip() == "":
        raise HTTPException(400, "Skate Alias (name) must be a non-empty string.")
    if trick_name.lower() not in ["kickflip", "ollie"]:
        raise HTTPException(400, "Currently only 'kickflip' and 'ollie' tricks are supported.")
    if not trick_name or trick_name.strip() == "":
        raise HTTPException(400, "Trick name must be a non-empty string.")

    score = score_video(video_file, trick_name)

    # upload_submission will handle adding/updating user and their trick score
    success, msg = db.upload_submission(name, trick_name, score)
    if not success:
        raise HTTPException(status_code=400, detail=msg)

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