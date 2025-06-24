import os
from app.config.settings import settings

url: str = settings.SUPABASE_URL
key: str = settings.SUPABASE_KEY
from supabase import AsyncClient,create_async_client

async def create_supabase() -> AsyncClient:
    return await create_async_client(url,key)

async def get_finance():
    supabase = await create_supabase()
    response = await supabase.table("finance").select("data").eq("user_id","9468f9b3-5d78-44b4-b714-e1aaff0195ef").execute()
    return response.data[0]


async def get_categories():
    supabase = await create_supabase() 
    response = await supabase.table("category_groups").select("name, categories(id,name)").eq("user_id", "9468f9b3-5d78-44b4-b714-e1aaff0195ef").execute()
    return response.data

