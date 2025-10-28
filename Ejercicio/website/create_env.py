import os

api_key = "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"

with open(".env", "w", encoding="utf-8") as f:
    f.write(f"OPENAI_API_KEY={api_key}\n")