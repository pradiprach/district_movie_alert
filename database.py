import logging
import os

from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def init_db():
    """
    Supabase does not support schema creation via SDK.
    This function is kept only for compatibility.
    """
    pass

def get_movies_list():
    """Get all movies from the database."""
    try:
        response = supabase.table("movies").select("*").order("name", desc=False).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching stocks: {e}")
        raise

def add_movie(name: str, cinemas: str, date: str):
    """Add a new movie to the database."""
    try:
        response = supabase.table("movies").insert({
            "name": name,
            "cinemas": cinemas,
            "date": date
        }).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error adding stock: {e}")
        raise

def update_movie_details(id: int, cinemas: str, date: str):
    """Update movie details."""
    try:
        supabase.table("movies").update({
            "cinemas": cinemas,
            "date": date
        }).eq("id", id).execute()
    except Exception as e:
        logger.error(f"Error updating stock status: {e}")
        raise

def delete_movie(id: int) -> bool:
    """
    Delete a movie record by id.
    """
    supabase.table("movies").delete().eq("id", id).execute()
    return True