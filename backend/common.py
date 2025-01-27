import base64
from typing import List
import cv2
import numpy as np
from pydantic import BaseModel

class Score(BaseModel):
    id: str
    image: str
    name: str
    score: float

class Leaderboard(BaseModel):
    nice: List[Score]
    threat: List[Score]


class Detection(BaseModel):
    image: str
    score: float


annotation_queue: list[Detection] = list()


def encode(frame: np.ndarray) -> str:
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode("utf-8") # type: ignore
