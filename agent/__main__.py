from openai import OpenAI
import os
client = OpenAI(
    api_key=os.environ.get("OPENAI_BASE_URL"),
    base_url=os.environ.get("BASE_URL"),
)

# TODO: Implement actual agent logic
