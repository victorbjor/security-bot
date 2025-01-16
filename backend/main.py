import asyncio
import base64
from collections import deque
import json
import time
import tempfile

import cv2
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse
import numpy as np

from constants import Z_CUTOFF
from decision_layer import call_decision_layer
from detection_layer import add_fps_count, assess_people, detect_people, draw_z_scores

app = FastAPI()

annotation_queue = deque(maxlen=10)

def sift_people(people: list[np.ndarray], z_scores: list[float]):
    for i, z in enumerate(z_scores):
        if z > Z_CUTOFF:
            annotation_queue.append(people[i])


@app.websocket("/ws/verdicts")
async def verdicts_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            if not annotation_queue:
                await asyncio.sleep(0.1)
                continue

            suspect = annotation_queue.popleft()

            _, buffer = cv2.imencode('.jpg', suspect)
            cropped_base64 = base64.b64encode(buffer).decode("utf-8")
            # Save cropped image to temp file
            
            # Create temp file that gets automatically deleted when closed
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=True) as temp_file:
                temp_file.write(base64.b64decode(cropped_base64))
                print(temp_file.name)
                temp_file.flush()
                decision = await call_decision_layer(temp_file.name)
            
            if decision is None:
                continue

            message = {
                "image": f"data:image/jpeg;base64,{cropped_base64}",
                "decision": decision.model_dump_json()
            }
            await websocket.send_text(json.dumps(message))
    
    except Exception as e:
        print(f"Socket Error: {e}")
    finally:
        await websocket.close()


@app.get("/video_feed")
async def video_feed():
    # Generate an MJPEG stream
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

def generate_frames():
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("Could not open webcam.")

    prev_time = time.time()

    while True:
        success, frame = camera.read()
        if not success:
            break

        prev_time = add_fps_count(frame, prev_time)
        people, results = detect_people(frame, classes=[0])
        z_scores = assess_people(people)
        draw_z_scores(frame, results, z_scores)
        sift_people(people, z_scores)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # Yield as part of the MJPEG stream
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

    camera.release()

if __name__ == "__main__":
    for e in generate_frames():
        pass
