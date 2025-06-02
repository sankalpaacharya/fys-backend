from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    GROQ_API_KEY : str
    OPENAI_API_KEY : str
    
    class Config:
        env_file = ".env"
        
        
settings = Setting()