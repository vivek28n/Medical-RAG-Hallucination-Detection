import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    VECTOR_DB_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "vector_db")
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"

settings = Settings()
