from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    GROQ_API_KEY : str
    OPENAI_API_KEY : str
    SUPABASE_URL : str
    SUPABASE_KEY : str
    FAST_API_KEY : str
    ENVIRONMENT : str = "development"
    SITE_URL : str
    NEXT_PUBLIC_SUPABASE_URL : str
    NEXT_PUBLIC_SUPABASE_ANON_KEY : str
    
    class Config:
        env_file = ".env"
        
settings = Setting()