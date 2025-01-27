import math
import time
from typing import List, Tuple

import clip
import cv2
import numpy as np
import torch
from torch import Tensor
from torchvision import transforms
from ultralytics import YOLO
from ultralytics.engine.results import Results

from leaderboard_manager import LeaderboardManager
from common import Detection, annotation_queue, encode
from constants import SIM_MEAN, SIM_VAR, Z_CUTOFF, debounce

device = "mps"

yolo_model = YOLO("yolo11n.pt")
clip_model, preprocess = clip.load("ViT-B/32", device=device)

# CLIP setup
clip_text = clip.tokenize(["threat", ""]).to(device)
text_features = clip_model.encode_text(clip_text)
text_features /= text_features.norm(dim=-1, keepdim=True)


# Clip transforms
normalize = transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
resize = transforms.Resize(224)
center_crop = transforms.CenterCrop(224)

# Color Guide
good_col = (0, 150, 0)
neutral_col = (0, 0, 150)
bad_col = (0, 0, 150)


def add_fps_count(frame, prev_time) -> float:
    # Calculate FPS
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    # Overlay FPS on the frame
    cv2.putText(
        frame,  # Image
        f"FPS: {fps:.0f}",  # Text
        (10, 30),  # Position (x, y)
        cv2.FONT_HERSHEY_SIMPLEX,  # Font
        1,  # Font scale
        (150, 255, 150),
        2,  # Thickness
        cv2.LINE_AA  # Line type
    )
    return current_time


def detect_people(img, classes=[], conf=0.5, rectangle_thickness=2, text_thickness=1):
    results: List[Results] = yolo_model.predict(img, classes=classes, conf=conf, device="mps", verbose=False)
    crops = []
    for result in results:
        if result.boxes is None: continue
        for box in result.boxes:
            # Crop people
            x1, y1 = int(box.xyxy[0][0]), int(box.xyxy[0][1])
            x2, y2 = int(box.xyxy[0][2]), int(box.xyxy[0][3])

            crop = img[y1:y2, x1:x2].copy()
            crops.append(crop)
    
    return crops, results


def custom_preprocess(img_in: np.ndarray) -> Tensor:
    #img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = torch.from_numpy(img_in).float() / 255.0
    img = img.permute(2, 0, 1)
    img = normalize(img)
    img = resize(img)
    img = center_crop(img)
    return img


def assess_people(people) -> Tuple[list[float], list[float]]:
    # Initialize running statistics if not already done
    if not hasattr(assess_people, 'running_mean'):
        assess_people.running_mean = SIM_MEAN # type: ignore
        assess_people.running_var = SIM_VAR # type: ignore
        assess_people.n = 0 # type: ignore
        assess_people.alpha = 0.0001 # type: ignore  # Exponential moving average factor
        assess_people.debounce = 0 # type: ignore

    #assess_people.debounce -= 1
    #if assess_people.debounce > 0:
    #    return []
    #assess_people.debounce = 10

    people = [custom_preprocess(person) for person in people if person.size != 0]

    if len(people) == 0:
        return [], []

    with torch.no_grad():
        people = torch.stack(people, dim=0).to(device)
        image_features = clip_model.encode_image(people)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        similarities: Tensor = (100.0 * image_features @ text_features.T).softmax(dim=-1)
    z_scores = []
    sim_list = []
    for similarity in similarities:
        similarity = similarity[0].item()
        # Update running mean using exponential moving average (EMA)
        assess_people.running_mean = (1 - assess_people.alpha) * assess_people.running_mean + assess_people.alpha * similarity # type: ignore
        assess_people.running_var = (1 - assess_people.alpha) * assess_people.running_var + assess_people.alpha * (similarity - assess_people.running_mean) ** 2 # type: ignore
        #Calculate z-score once we have enough samples

        std_dev = math.sqrt(assess_people.running_var) if assess_people.running_var > 0 else 1.0 # type: ignore
        z_score = (similarity - assess_people.running_mean) / std_dev # type: ignore
        z_scores.append(z_score)
        sim_list.append(similarity)
    return z_scores, sim_list


def get_color_for_zscore(z_score) -> tuple[int, int, int]:
    # Clamp z-score between -1 and 5
    z_score = max(-1, min(5, z_score))

    # Normalize to 0-1 range
    normalized = (z_score + 1) / 6
    
    # Create rainbow gradient: blue -> green -> yellow -> red
    if normalized < 0.33:
        # Blue to green
        r = 0
        g = int(255 * (normalized * 3))
        b = int(255 * (1 - normalized * 3))
    elif normalized < 0.66:
        # Green to yellow
        r = int(255 * ((normalized - 0.33) * 3))
        g = 255
        b = 0
    else:
        # Yellow to red
        r = 255
        g = int(255 * (1 - (normalized - 0.66) * 3))
        b = 0
    
    return (b, g, r)  # OpenCV uses BGR format


def draw_z_scores(frame, object_detection_results, z_scores):
    i = 0
    for result in object_detection_results:
        for box in result.boxes:
            x1, y1 = int(box.xyxy[0][0]), int(box.xyxy[0][1])
            x2, y2 = int(box.xyxy[0][2]), int(box.xyxy[0][3])
            
            threat_col = get_color_for_zscore(z_scores[i])
            cv2.rectangle(frame, (x1, y1), (x2, y2), threat_col, 2)
            cv2.putText(frame, f"Threat Level: {z_scores[i]:.0f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.5, threat_col, 2)
            i += 1


def to_annotation(image: np.ndarray, z: float, last_debounce_time: float) -> float:
    if z > Z_CUTOFF:
        annotation_queue.append(Detection(image=encode(image), score=z))
        return time.time()
    else:
        return last_debounce_time


def to_queues(people: list[np.ndarray], z_scores: list[float], similarities: list[float], last_debounce_time: float, leaderboard_mgr: LeaderboardManager) -> float:
    if (time.time() - last_debounce_time) > debounce:
        for i, z in enumerate(z_scores):
            last_debounce_time = to_annotation(people[i], z, last_debounce_time)
            last_debounce_time = leaderboard_mgr.new_score(people[i], similarities[i], last_debounce_time)
    return last_debounce_time


def generate_frames(leaderboard_manager):
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("Could not open webcam.")

    prev_time = time.time()

    last_debounce_time = time.time()

    while True:
        success, frame = camera.read()
        if not success:
            break

        # ML processing here
        people, results = detect_people(frame, classes=[0])
        z_scores, similarities = assess_people(people)
        last_debounce_time = to_queues(people, z_scores, similarities, last_debounce_time, leaderboard_manager)

        # Draw bounding boxes and z-scores on the frame
        draw_z_scores(frame, results, z_scores)
        prev_time = add_fps_count(frame, prev_time)

        # Encode and yield as part of the MJPEG stream
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

    camera.release()
