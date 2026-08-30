from functools import lru_cache
from supabase import Client, create_client
from app.config import SUPABASE_SECRET_KEY, SUPABASE_URL


@lru_cache
def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SECRET_KEY must be configured."
        )

    return create_client(
        SUPABASE_URL,
        SUPABASE_SECRET_KEY,
    )