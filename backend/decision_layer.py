from enum import Enum
import aiohttp
from pydantic import BaseModel, Field

import instructor
from openai import AsyncOpenAI


VISION_MODEL = "llama3.2-vision:11b"
DECISION_MODEL = "gemma2:9b"

ollama_url = "http://localhost:11434/v1"
client = instructor.from_openai(
    AsyncOpenAI(
        base_url= ollama_url,
        api_key="ollama",  # required, but unused
    ),
    mode=instructor.Mode.JSON,
)

class EscalationLevel(Enum):
    FALSE_POSITIVE = 'THE PERSON IS NOT A THREAT'
    LOG = 'THE PERSON IS NOT AN IMMEDIATE THREAT, BUT SHOULD BE LOGGED'
    CALL_SECURITY = 'THE PERSON IS AN IMMEDIATE THREAT, AND SECURITY SHOULD BE CALLED'
    ALARM = 'THE PERSON IS AN IMMEDIATE THREAT, AND THE GENERAL ALARM SHOULD BE TRIGGERED'


class DecisionAnswer(BaseModel):
    higher_level_reasoning: str = Field(description="One sentence summary of the description of the image and any threats therein")
    escalation_level: EscalationLevel = Field(description="The level of escalation required")
    escalation_reason: str = Field(description="The reason for escalation. You should always write something here. Max one sentence.")


describer_prompt = """
You are a security guard. You're job is to receive images of people from a lower level autonomous security system.
You are responsible for determining if the person in the image is indeed a threat.
The lower level systems have very low intelligence. They only have access to the image and have no context or ability to reason.
Make sure to make a detailed description of the facial expressions and possible emotions of the person in the image.
Do not make any assumptions about the the reasoning of the lower level system. Just look at the image, describe what you see, and make sure to include all details that may, or may not, warrant escalation.
The lower level system may often mark people as threats when they are really not.
"""

decision_prompt = """
You are a security guard. You will receive a description of an image and any threats therein from a lower level system.
You should make a decision based on the description and the image, whether threat escalation is warranted.

Log level escalation is for when the person does not pose an immediate threat, but is acting suspiciously.
Call security level escalation is for when the person may be posing an immediate threat. Calling security is ok even when immediate threat is not fully confirmed, but possible.
Alarm level escalation is for when the person is posing an immediate threat and the general alarm should be triggered.
"""

async def call_decision_layer(base64_image: str) -> DecisionAnswer | None:
    image_description = await get_image_description(base64_image)
    print(image_description)
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


async def get_image_description(base64_image: str) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": VISION_MODEL,
                    "prompt": describer_prompt,
                    "stream": False,
                    "images": [base64_image]
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['response']
                else:
                    print(f"Error from Ollama API: {response.status}")
                    return None
    except Exception as e:
        print(f"Error getting image description: {e}")
        return None