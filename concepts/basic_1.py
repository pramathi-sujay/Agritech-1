import os
from dotenv import load_dotenv
from openai import OpenAI

ENV_PATH=os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(ENV_PATH)

OPENAI_API_kEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

if not OPENAI_API_kEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
if not OPENAI_BASE_URL:
    raise ValueError("OPENAI_BASE_URL is not set in the environment variables.")
if not OPENAI_MODEL:
    raise ValueError("OPENAI_MODEL is not set in the environment variables.")

client=OpenAI(
    api_key=OPENAI_API_kEY,
    base_url=OPENAI_BASE_URL,
)

completion=client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=[
        {"role":"system","content":"You are a helpful assistant for farmers."},
        {"role":"user","content":"Explain what is Tomato late blight and how to prevent it? with less than 100 characters."}
    ],
    temperature=0.7,
)
print(completion.choices[0].message.content)
