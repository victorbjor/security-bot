import asyncio
from collections import deque
import json

from fastapi import FastAPI, Response, WebSocket, Request, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from leaderboard_manager import LeaderboardManager
from common import Detection, Leaderboard, annotation_queue
from detection_layer import generate_frames
from decision_layer import call_decision_layer

app = FastAPI()


class UpdateNameRequest(BaseModel):
    name: str
    id: str


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["*"] to allow all origins (for dev only)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

leaderboard_manager: LeaderboardManager = LeaderboardManager()

@app.websocket("/ws/verdicts")
async def verdicts_websocket(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        while True:
            if not annotation_queue:
                await asyncio.sleep(0.1)
                continue

            suspect: Detection = annotation_queue.pop(0)

            decision = await call_decision_layer(suspect.image)
            
            # Handle errors "gracefully"
            if decision is None:
                continue

            message = {
                "image": f"data:image/jpeg;base64,{suspect.image}",
                "decision": decision.model_dump_json()
            }
            await websocket.send_text(json.dumps(message))
    
    except Exception as e:
        print(f"Socket Error: {e}")
    finally:
        await websocket.close()


@app.get("/video_feed")
async def video_feed() -> StreamingResponse:
    # Generate an MJPEG stream
    return StreamingResponse(generate_frames(leaderboard_manager), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/leaderboard", response_model=Leaderboard)
async def leaderboard() -> Leaderboard:
    return Leaderboard(
        nice=leaderboard_manager.nice_leaderboard,
        threat=leaderboard_manager.threat_leaderboard
    )


@app.post("/update-name")
async def update_name(request: UpdateNameRequest) -> Response:
    # Assuming leaderboard_manager.update_name(id, name) updates the product name successfully.
    success = leaderboard_manager.update_name(request.id, request.name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update product name.")
    return Response(status_code=200)

if __name__ == "__main__":
    for e in generate_frames(leaderboard_manager):
        pass
