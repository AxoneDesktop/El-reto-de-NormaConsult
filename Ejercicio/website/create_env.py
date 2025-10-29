import os

api_key = "test"

with open(".env", "w", encoding="utf-8") as f:
    f.write(f"OPENAI_API_KEY={api_key}\n")