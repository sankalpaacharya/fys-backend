from app.config.settings import settings
from supabase import AsyncClient, create_async_client

url: str = settings.SUPABASE_URL
key: str = settings.SUPABASE_KEY

async def create_supabase() -> AsyncClient:
    return await create_async_client(url, key)

async def get_finance(user_id: str):
    supabase = await create_supabase()
    response = await supabase.table("finance").select("data").eq("user_id", user_id).execute()
    return response.data[0] if response.data else None
