import base64
from enum import Enum
from pydantic import BaseModel, Field
import tempfile

import instructor
from ollama import AsyncClient
from openai import AsyncOpenAI

USE_GOOGLE = True

if USE_GOOGLE:
    MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    VISION_MODEL = "gemini-1.5-flash"
    DECISION_MODEL = "gemini-1.5-flash"
    
    with open("./.env", "r") as f:
        API_KEY = f.read().strip()
else:
    VISION_MODEL = "llama3.2-vision:11b"
    DECISION_MODEL = "gemma2:9b"
    MODEL_URL = "http://localhost:11434/v1"
    API_KEY = "ollama"


client = instructor.from_openai(
    AsyncOpenAI(
        base_url= MODEL_URL,
        api_key=API_KEY
    ),
    mode=instructor.Mode.JSON, 
)

vision_client = AsyncOpenAI(
    base_url= MODEL_URL,
    api_key=API_KEY
)

class EscalationLevel(Enum):
    NOT_READABLE = 'Not Readable'
    FALSE_POSITIVE = 'False Positive'
    LOG = 'Log'
    CALL_SECURITY = 'Call Security'
    ALARM = 'Alarm'

class DecisionAnswer(BaseModel):
    higher_level_reasoning: str = Field(description="One sentence summary of the description of the image and any threats therein")
    escalation_level: EscalationLevel = Field(description="The level of escalation required")
    escalation_reason: str = Field(description="The reason for escalation. You should always write something here. Up to 18 words.")


describer_prompt = """
You are an observational analyst designed to assist with image interpretation for safety and situational awareness systems. Your task is to analyze images provided by a basic image detection system.
Carefully describe the details of the person or people in the image, focusing on observable features such as facial expressions, body posture, and visible objects. Highlight any elements that might indicate emotions, actions, or context but avoid making assumptions beyond the visible details.
The lower-level system may occasionally flag individuals for review, even when no concerning elements are present. Your role is not to determine intent but to provide a thorough and neutral description to inform further evaluation. Stick strictly to the visual details and avoid adding speculative interpretations.
"""

decision_prompt = """
You are a safety and security assistant responsible for assessing descriptions of images provided by a lower-level observational system. Your task is to decide on the appropriate response level based on the detailed description provided.

You are not responsible for interpreting intent beyond the description but should categorize the situation using the following guidelines:

1. **Log Level Escalation:** For situations where the description indicates unusual or suspicious behavior that does not pose an immediate threat. Use this to document concerns without taking immediate action.

2. **Call Security Level Escalation:** For situations where the description suggests a potential threat that might require immediate attention. It is acceptable to escalate at this level if there is uncertainty but the possibility of a threat exists.

3. **Alarm Level Escalation:** For situations where the description clearly indicates an immediate and significant threat that requires triggering the general alarm.

Always base your decision on the details explicitly provided in the description. Do not infer or assume additional context that is not present in the information given. If the description lacks sufficient detail, opt for a false positive and choose 'INSUFFICIENT DETAIL' as escalation reason.
"""

external_prompt = """
You are a safety and security assistant responsible for assessing images provided by a surveillance camera. Your task is to decide on the appropriate response level based on the detailed description provided.
Carefully describe the details of the person or people in the image, focusing on observable features such as facial expressions, body posture, and visible objects. Highlight any elements that might indicate emotions, actions, or context but avoid making assumptions beyond the visible details.

The security team is currently roaming the area idly, so you may call them whenever the image suggests that immediate threat "might" happen. This is the level to choose when a person is displaying aggravated or aggressive behavior, or when a person appears to be ready to produce a concealed weapon, or when a person appears to be preparing for a violent act. It is better to call security preemptively than too late.
Too separate the "Call Security" and "Alarm" levels, think of it as that the guards will run to the scene on Alarm, but walk to the scene on Call Security. Typical scenarios for alarm is ongoing violence, or a drawn weapon, or similar.
The back office security team will be looking through the logs the day after the event. So this category is not for any response teams, but should be used to store images that may aid an "after the fact" investigation. This may include images where there is some indication the person may be concealing a weapon, or when someone is displaying non-aggresive disagreement (aggrsive disagreement should be notified to security).
The back office security team may sometimes need a good laugh, so if you encounter an image that you may make a joke about, you can use this category to store it, but only if it is not related to a potential threat. Feel free to be quite sassy in your escalation reason if logging the image for a humorous purpose.

Always base your decision on the details explicitly provided in the image. If someone seems to be interacting with someone or something that is not visible in the image, you may try to infer what it might be. 
If the image is not readable due to poor lighting or blur, or if the image generally lacks sufficient detail, opt for a the Not Readable escalation level and state why it is hard to read the image as escalation reason.

"""


async def call_decision_layer(image_buffer: str) -> DecisionAnswer | None:
    if USE_GOOGLE:
        return await call_external_service(image_buffer)
    else:
        return await call_internal_service(image_buffer)


async def call_dummy_service(image_path: str) -> str | None:
    return DecisionAnswer(
        higher_level_reasoning="There is no reasoning",
        escalation_level=EscalationLevel.LOG,
        escalation_reason="No reason, just testing."
        )


async def call_external_service(image_buffer: str) -> str | None:
    try:
        return await client.chat.completions.create(
            model=DECISION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": external_prompt,
                },
                {
                    "role": "user",
                    "content": [
                        {
                           "type": "text",
                            "text": "What is in this image?",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url":  f"data:image/jpeg;base64,{image_buffer}"
                            },
                        },
                    ],
                }
            ],
            response_model=DecisionAnswer,
        )
    except Exception as e:
        print(f"Error calling decision layer: {e}")
        return None


async def call_internal_service(image_buffer: str) -> DecisionAnswer | None:
    image_description = await get_image_description(image_buffer)
    print('-------------\n' + image_description + '\n-------------')
    try:
        return await client.chat.completions.create(
            model=DECISION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": decision_prompt,
                },
                {
                    "role": "user",
                    "content": image_description
                }
            ],
            response_model=DecisionAnswer,
        )
    except Exception as e:
        print(f"Error calling decision layer: {e}")
        return None


async def get_image_description(image_buffer: str) -> str:
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=True) as temp_file:
        temp_file.write(base64.b64decode(image_buffer))
        temp_file.flush()
        
        response = await AsyncClient().chat(
            model=VISION_MODEL,
            messages=[{
                'role': 'user',
                'content': describer_prompt,
                'images': [temp_file.name] #[f"data:image/jpeg;base64,{base64_image}"]
            }]
        )
    return response.message.content
