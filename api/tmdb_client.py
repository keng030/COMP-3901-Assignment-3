import os
import requests
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv(".env")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def get_headers():
    """Constructs the headers needed for the TMDB API requests."""
    if not TMDB_API_KEY:
        raise ValueError("TMDB API key not found. Please check your .env file.")
    
    # TMDB allows passing the API key as a query parameter or via Authorization header.
    # We will use the query parameter approach in our base requests, 
    # but setting up headers is good practice for future-proofing.
    return {
        "accept": "application/json"
    }

def get_trending_movies(time_window="week"):
    """
    Fetches trending movies to display on the app's landing page.
    Satisfies the 'Trending or popular content integration' enhanced feature.
    """
    url = f"{BASE_URL}/trending/movie/{time_window}"
    params = {"api_key": TMDB_API_KEY}
    
    response = requests.get(url, headers=get_headers(), params=params)
    
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        print(f"Error fetching trending movies: {response.status_code}")
        return []

def search_movies(query):
    """
    Searches for movies by title. Useful for the natural language search feature.
    """
    url = f"{BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "include_adult": "false" # Keep it safe for school projects!
    }
    
    response = requests.get(url, headers=get_headers(), params=params)
    
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        print(f"Error searching for movie '{query}': {response.status_code}")
        return []

@lru_cache(maxsize=128)
def get_movie_details(movie_id):
    """
    Fetches comprehensive details for a specific movie.
    Uses @lru_cache to store up to 128 recent API responses in memory.
    """
    url = f"{BASE_URL}/movie/{movie_id}"
    
    # 'append_to_response' is a massive performance saver. 
    # It fetches credits (cast/director) and keywords in the same single API call.
    params = {
        "api_key": TMDB_API_KEY,
        "append_to_response": "credits,keywords"
    }
    
    response = requests.get(url, headers=get_headers(), params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching details for ID {movie_id}: {response.status_code}")
        return None

def discover_filtered_movies(filters: dict, max_pages=3):
    """
    Fetches movies based on specific criteria (genres, years, ratings).
    Accommodates pagination to fetch more than just the top 20 results.
    """
    url = f"{BASE_URL}/discover/movie"
    
    # Base parameters that should always be applied
    params = {
        "api_key": TMDB_API_KEY,
        "include_adult": "false",
        "sort_by": "vote_average.desc" 
    }
    
    # Merge the base params with any specific filters passed in from the UI
    params.update(filters)
    
    all_movies = []
    
    # Loop through multiple pages to gather a larger pool of movies (3 pages = 60 movies)
    for page in range(1, max_pages + 1):
        params["page"] = page  # Tell the API exactly which page to fetch
        
        response = requests.get(url, headers=get_headers(), params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Add this page's movies to our master list
            all_movies.extend(data.get("results", []))
            
            # Safety check: If TMDB says there are no more pages left, stop looping early
            if page >= data.get("total_pages", 1):
                break
        else:
            print(f"Error discovering movies on page {page}: {response.status_code}")
            break # Stop looping if the API throws an error
            
    return all_movies

def get_person_id(name: str):
    """Searches TMDB for an actor/director and returns their unique integer ID."""
# We added 'not isinstance(name, str)' to prevent list crashes!
    if not isinstance(name, str) or not name.strip():
        return None
        
    url = f"{BASE_URL}/search/person"
    params = {
        "api_key": TMDB_API_KEY,
        "query": name.strip()
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                return results[0].get("id") # Return the ID of the top match
    except Exception as e:
        print(f"Error finding person: {e}")
        
    return None