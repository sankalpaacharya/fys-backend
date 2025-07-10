from collections import defaultdict
import datetime
from app.config.settings import settings
import json
from supabase import AsyncClient,create_async_client

url: str = settings.SUPABASE_URL
key: str = settings.SUPABASE_KEY

USER_ID = "3606243d-0256-4f84-ba2c-72496badf883"

async def create_supabase() -> AsyncClient:
    return await create_async_client(url,key)

async def get_categories():
    supabase = await create_supabase() 
    response = await supabase.table("category_groups").select("name, categories(id,name), id").eq("user_id", USER_ID).execute()
    result = defaultdict(list) 
    for item in response.data:
        group_name = item["name"]
        for category in item["categories"]:
            result[group_name].append((category["name"],category["id"]))
    final_categories = {k:v for k,v in result.items()}
    return final_categories, response.data

async def store_finance(data:str):
    """store data from llm to supabase
    """
    try:
        data = json.loads(data)
        supabase = await create_supabase()
        response = await supabase.table("transactions") \
                    .insert({
                        "user_id": USER_ID,
                        "created_at": datetime.datetime.now().isoformat(),
                        "amount":data["amount"],
                        "category":data["category"],
                        "category_group":data["category_group"],
                        "description":data["description"],
                        "type":data["type"],
                        "category_id": data["category_id"],
                        "account_id":data["account_id"]
                    }) \
                        .execute()
        return {
            "success": True,
            "message": f"Successfully logged expense of ₹{data['amount']} for {data['description']} in {data['category']} category."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to log expense: {str(e)}"
        }

async def get_full_user_info():
    supabase = await create_supabase()
    accounts = await supabase.table("accounts") \
        .select("id,name,amount,type")\
            .eq("user_id",USER_ID) \
                .execute()
    transactions = await supabase.table("transactions") \
        .select("amount,category_group,category,description") \
            .eq("user_id",USER_ID) \
                .execute()
    _, categories = await get_categories()
    categories_without_id = []
    cat_grps_ids_ls = []
    for cat_grp in categories:
        cat_grps_ids_ls.append(cat_grp["id"])
        categories_without_id.append({
            "Category group": cat_grp["name"],
            "Categories" : cat_grp["categories"]
        })
    target_ls = []
    for id in cat_grps_ids_ls:
        targets = await supabase.table("categories") \
            .select("id,name,category_months(activity,assign,available,month),category_targets(type,amount,yearly,monthly,weekly)")\
                .eq("category_group_id",id) \
                    .execute()   
        target_ls.extend(targets.data)
    return {
        "accounts": accounts.data,
        "transactions": transactions.data,
        "categories": categories_without_id,
        "targets": target_ls
    }