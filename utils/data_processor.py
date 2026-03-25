from api.tmdb_client import get_movie_details
from utils.formatting import *

def build_detailed_movie_pool(shallow_movie_list, max_movies=20):
    """
    Takes a list of basic movie results (from search or discover) and 
    fetches their full details (cast, crew, keywords) to feed the recommendation engines.
    
    Args:
        shallow_movie_list (list): Raw list of movies from TMDB search/trending.
        max_movies (int): Cap the number of API calls to prevent slow load times.
        
    Returns:
        list: A list of detailed movie dictionaries.
    """
    if not shallow_movie_list:
        return []
        
    detailed_pool = []
    # We slice the list to max_movies so we don't accidentally make 100 API calls at once!
    for movie in shallow_movie_list[:max_movies]:
        movie_id = movie.get('id')
        if movie_id:
            # This uses our @lru_cache from tmdb_client, so it's super fast if we've seen it before
            details = get_movie_details(movie_id)
            if details:
                detailed_pool.append(details)
                
    return detailed_pool

def format_movie_for_ui(movie):
    """
    Cleans up a detailed movie dictionary into a beautiful, readable string 
    for the Gradio interface.
    """
    title = movie.get('title', 'Unknown Title')
    
    # Safely extract the year
    release_date = movie.get('release_date', '')
    year = release_date[:4] if release_date else 'N/A'
    
    # Get the director's name (if available)
    director = "Unknown Director"
    crew = movie.get('credits', {}).get('crew', [])
    for member in crew:
        if member.get('job') == 'Director':
            director = member.get('name')
            break
            
    # Get top 2 genres
    genres = [g.get('name') for g in movie.get('genres', [])][:2]
    genre_str = "/".join(genres) if genres else "Various"
    
    # Truncate the plot so it doesn't overwhelm the UI
    plot = movie.get('overview', 'No plot available.')
    if len(plot) > 150:
        plot = plot[:147] + "..."
        
    # Build the final string
    return f"🎬 {make_bold(title)} ({make_bold(year)})| Dir: {director} | {genre_str}\n{plot}\n"