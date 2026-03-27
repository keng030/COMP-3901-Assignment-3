from utils.formatting import *

# TMDB uses specific integer IDs for genres. 
# This dictionary maps the string names from your Gradio UI to the API IDs.
GENRE_MAP = {
    "Action": 28,
    "Adventure": 12,
    "Animation": 16,
    "Comedy": 35,
    "Crime": 80,
    "Documentary": 99,
    "Drama": 18,
    "Family": 10751,
    "Fantasy": 14,
    "History": 36,
    "Horror": 27,
    "Music": 10402,
    "Mystery": 9648,
    "Romance": 10749,
    "Sci-Fi": 878,
    "TV Movie": 10770,
    "Thriller": 53,
    "War": 10752,
    "Western": 37
}

def build_discover_params(
    year_range=None, 
    min_rating=None, 
    genres=None, 
    min_votes=100, 
    runtime_range=None,
    language=None,
    certification=None,
    personnel_id=None 
):
    params = {}
    
    if year_range and len(year_range) == 2:
        params["primary_release_date.gte"] = f"{year_range[0]}-01-01"
        params["primary_release_date.lte"] = f"{year_range[1]}-12-31"
        
    if min_rating is not None:
        params["vote_average.gte"] = min_rating
    if min_votes is not None:
        params["vote_count.gte"] = min_votes
        
    if genres:
        if isinstance(genres, list):
            genre_ids = [str(GENRE_MAP[g]) for g in genres if g in GENRE_MAP]
            params["with_genres"] = "|".join(genre_ids) # The pipe acts as an OR operator
        elif isinstance(genres, str) and genres in GENRE_MAP:
            params["with_genres"] = str(GENRE_MAP[genres])
            
    if runtime_range and len(runtime_range) == 2:
        params["with_runtime.gte"] = runtime_range[0]
        params["with_runtime.lte"] = runtime_range[1]
        
    if language:
        params["with_original_language"] = language
        
    if certification:
        params["certification_country"] = "US"
        params["certification"] = certification
        
    if personnel_id:
        params["with_people"] = personnel_id

    return params

def format_filter_results(movie_list):
    """
    A helper function to clean up the raw JSON list returned by the API 
    into a readable string for the Gradio UI.
    """
    if not movie_list:
        return "No movies found matching those exact filters. Try broadening your search!"
        
    formatted_results = []
    # Only show top 10 results to avoid crowding the UI
    for idx, movie in enumerate(movie_list[:10], 1):
        title = movie.get('title', 'Unknown Title')
        year = movie.get('release_date', 'YYYY')[:4]
        rating = movie.get('vote_average', 0)
        votes = movie.get('vote_count', 0)
        
        formatted_results.append(f"{idx}. {make_bold(title)} ({make_bold(year)}) - ⭐ {make_bold(f'{rating}/10')} ({votes} votes)")        
    
    return "\n".join(formatted_results)