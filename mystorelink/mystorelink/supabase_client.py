from supabase import create_client, Client
from django.conf import settings

def get_supabase_client() -> Client:
    """Create and return a Supabase client instance"""
    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )
    return supabase

def get_supabase_admin_client() -> Client:
    """Create and return a Supabase admin client with service role key"""
    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )
    return supabase