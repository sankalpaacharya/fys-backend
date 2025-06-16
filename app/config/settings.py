from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    GROQ_API_KEY : str
    OPENAI_API_KEY : str
    ENVIRONMENT : str = "development"
    SUPABASE_URL : str
    SUPABASE_KEY : str
    MILVUS_URL : str
    MILVUS_TOKEN :str
    
    class Config:
        env_file = ".env"
        
settings = Setting()