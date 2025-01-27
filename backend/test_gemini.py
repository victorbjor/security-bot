from pprint import pprint
from typing_extensions import TypedDict
import google.generativeai as genai
from pydantic import BaseModel, Field

from just_get_an_image import get_cam_image

with open("./backend/.env", "r") as f:
    api_key = f.read().strip()

genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name = "gemini-1.5-flash")

image = get_cam_image()

class Greeting(BaseModel):
    description_of_person: str
    age: int
    gender: str
    my_greeting: str

class ImageDescription(BaseModel):
    general_description: str
    nice_greeating_to_person: list[Greeting]


prompt = "Please describe and great any people in this image."
response = model.generate_content([
    {'mime_type':'image/jpeg', 'data': image},
    prompt
    ],     
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json", response_schema=list[ImageDescription]
    ))

pprint(response.text)
