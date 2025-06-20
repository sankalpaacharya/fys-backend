import datetime
from app.config.settings import settings
import json

url: str = settings.SUPABASE_URL
key: str = settings.SUPABASE_KEY
from supabase import AsyncClient,create_async_client

async def create_supabase() -> AsyncClient:
    return await create_async_client(url,key)

async def get_finance():
    supabase = await create_supabase()
    response = await supabase.table("finance").select("data").eq("user_id","9468f9b3-5d78-44b4-b714-e1aaff0195ef").execute()
    return response.data[0]["data"]

async def get_categories():
    supabase = await create_supabase() 
    response = await supabase.table("category_groups").select("name, categories(name)").eq("user_id", "9468f9b3-5d78-44b4-b714-e1aaff0195ef").execute()
    return response.data

async def store_finance(data:str):
    """store data from llm to supabase
    """
    data = json.loads(data)
    supabase = await create_supabase()
    response = await supabase.table("expenses") \
                  .insert({
                      "user_id": "9468f9b3-5d78-44b4-b714-e1aaff0195ef",
                      "created_at": datetime.datetime.now().isoformat(),
                      "amount":data["amount"],
                      "category":data["category"],
                      "category_group":data["category_group"],
                      "description":data["description"]
                  }) \
                      .execute()
    return {"response":data["response"]}
                      
