import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    NEO4J_URI = os.getenv("NEO4J_URI", "")
    NEO4J_USER = os.getenv("NEO4J_USER", "")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
    # how many episodic items to retrieve
    EPISODIC_K = int(os.getenv("EPISODIC_K", "5"))
    # working memory capacity (recent turns)
    WORKING_CAPACITY = int(os.getenv("WORKING_CAPACITY", "6"))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))


settings = Settings()
