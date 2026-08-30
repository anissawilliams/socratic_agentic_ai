import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")


print("URL:", SUPABASE_URL)
print("KEY PREFIX:", SUPABASE_SECRET_KEY[:10] if SUPABASE_SECRET_KEY else None)
print("KEY LENGTH:", len(SUPABASE_SECRET_KEY) if SUPABASE_SECRET_KEY else None)