from enum import Enum
from pydantic import BaseModel, Field

import instructor
from ollama import AsyncClient
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

vision_client = AsyncOpenAI(
    base_url= ollama_url,
    api_key="ollama",  # required, but unused
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

async def call_decision_layer(image_path: str) -> DecisionAnswer | None:
    image_description = await get_image_description(image_path)
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


async def get_image_description(image_path: str) -> str:
    response = await AsyncClient().chat(
        model=VISION_MODEL,
        messages=[{
            'role': 'user',
            'content': describer_prompt,
            'images': [image_path] #[f"data:image/jpeg;base64,{base64_image}"]
        }]
    )
    return response.message.content
