import math
import time

import clip
import cv2
import torch
from torchvision import transforms
from ultralytics import YOLO

from constants import SIM_MEAN, SIM_VAR, Z_CUTOFF

device = "mps"

yolo_model = YOLO("yolo11n.pt")
clip_model, preprocess = clip.load("ViT-B/32", device=device)


clip_text = clip.tokenize(["threat", ""]).to(device)
text_features = clip_model.encode_text(clip_text)
text_features /= text_features.norm(dim=-1, keepdim=True)


good_col = (0, 150, 0)
neutral_col = (0, 0, 150)
bad_col = (0, 0, 150)


def add_fps_count(frame, prev_time):
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
    results = yolo_model.predict(img, classes=classes, conf=conf, device="mps", verbose=False)
    crops = []
    for result in results:
        for box in result.boxes:
            # Crop people
            x1, y1 = int(box.xyxy[0][0]), int(box.xyxy[0][1])
            x2, y2 = int(box.xyxy[0][2]), int(box.xyxy[0][3])

            crop = img[y1:y2, x1:x2]
            crops.append(crop)
    
    return crops, results

# Clip transforms
normalize = transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
resize = transforms.Resize(224)
center_crop = transforms.CenterCrop(224)


def custom_preprocess(img):
    #img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = torch.from_numpy(img).float() / 255.0
    img = img.permute(2, 0, 1)
    img = normalize(img)
    img = resize(img)
    img = center_crop(img)
    return img


def assess_people(people):
    # Initialize running statistics if not already done
    if not hasattr(assess_people, 'running_mean'):
        assess_people.running_mean = SIM_MEAN
        assess_people.running_var = SIM_VAR
        assess_people.n = 0
        assess_people.alpha = 0.0001  # Exponential moving average factor
        assess_people.debounce = 0

    #assess_people.debounce -= 1
    #if assess_people.debounce > 0:
    #    return []
    #assess_people.debounce = 10

    people = [custom_preprocess(person) for person in people if person.size != 0]

    if len(people) == 0:
        return []

    with torch.no_grad():
        people = torch.stack(people, dim=0).to(device)
        image_features = clip_model.encode_image(people)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        similarities = (100.0 * image_features @ text_features.T).softmax(dim=-1)
    z_scores = []
    for similarity in similarities:
        similarity = similarity[0].item()
        # Update running mean using exponential moving average (EMA)
        assess_people.running_mean = (1 - assess_people.alpha) * assess_people.running_mean + assess_people.alpha * similarity
        assess_people.running_var = (1 - assess_people.alpha) * assess_people.running_var + assess_people.alpha * (similarity - assess_people.running_mean) ** 2
        #Calculate z-score once we have enough samples
        
        std_dev = math.sqrt(assess_people.running_var) if assess_people.running_var > 0 else 1.0
        z_score = (similarity - assess_people.running_mean) / std_dev
        z_scores.append(z_score)
    
    return z_scores


def draw_z_scores(frame, object_detection_results, z_scores):
    for result in object_detection_results:
        for box in result.boxes:
            x1, y1 = int(box.xyxy[0][0]), int(box.xyxy[0][1])
            x2, y2 = int(box.xyxy[0][2]), int(box.xyxy[0][3])
            
            for z_score in z_scores:
                if z_score <= Z_CUTOFF:
                    threat_col = good_col
                #elif z_score <= 1.5:
                #    threat_col = neutral_col
                else:
                    threat_col = bad_col
                cv2.rectangle(frame, (x1, y1), (x2, y2), threat_col, 2)
                cv2.putText(frame, f"Threat Sigma: {z_score:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.5, threat_col, 2)
