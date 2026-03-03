import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not set. LLM disabled.")


def think(prompt: str) -> str:
    if not client:
        return "LLM_DISABLED"

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        return response.text if hasattr(response, "text") else str(response)

    except Exception as e:
        return f"LLM_ERROR: {str(e)}"
