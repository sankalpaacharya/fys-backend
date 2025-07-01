import datetime
from app.config.settings import settings
import json

url: str = settings.SUPABASE_URL
key: str = settings.SUPABASE_KEY
from supabase import AsyncClient,create_async_client

USER_ID = "3606243d-0256-4f84-ba2c-72496badf883"

async def create_supabase() -> AsyncClient:
    return await create_async_client(url,key)

async def get_categories():
    supabase = await create_supabase() 
    response = await supabase.table("category_groups").select("name, categories(name), id").eq("user_id", USER_ID).execute()
    return response.data

async def store_finance(data:str):
    """store data from llm to supabase
    """
    data = json.loads(data)
    supabase = await create_supabase()
    response = await supabase.table("transactions") \
                  .insert({
                      "user_id": USER_ID,
                      "created_at": datetime.datetime.now().isoformat(),
                      "amount":data["amount"],
                      "category":data["category"],
                      "category_group":data["category_group"],
                      "description":data["description"]
                  }) \
                      .execute()
    return {"response":data["response"]}

async def get_full_user_info():
    supabase = await create_supabase()
    accounts = await supabase.table("accounts") \
        .select("name,amount,type")\
            .eq("user_id",USER_ID) \
                .execute()
    print(accounts.data)
    transactions = await supabase.table("transactions") \
        .select("amount,category_group,category,description") \
            .eq("user_id",USER_ID) \
                .execute()
    print(transactions.data)
    categories = await get_categories()
    print(categories)
    cat_grp_ids = categories[0]["id"]
    print(cat_grp_ids)
    cat_grps_ids_ls = []
    for cat_grp in categories:
        cat_grps_ids_ls.append(cat_grp["id"])
    print(cat_grps_ids_ls)
    target_ls = []
    for id in cat_grps_ids_ls:
        targets = await supabase.table("categories") \
            .select("name,category_months(activity,assign,available,month),category_targets(type,amount,yearly,monthly,weekly)")\
                .eq("category_group_id",id) \
                    .execute()   
        target_ls.extend(targets.data)
    print(target_ls)
    return {
        "accounts": accounts.data,
        "transactions": transactions.data,
        "categories": categories,
        "targets": target_ls
    }