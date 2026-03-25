from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_features(movie):
    """
    Helper function to extract and format metadata into a single string.
    This creates the "metadata soup" we use for content-based comparison.
    """
    # 1. Extract Genres
    genres = [g.get('name', '') for g in movie.get('genres', [])]
    
    # 2. Extract Keywords (If available from the append_to_response API call)
    keywords = [k.get('name', '') for k in movie.get('keywords', {}).get('keywords', [])]
    
    # 3. Extract Cast & Crew (If available)
    cast = []
    director = []
    credits = movie.get('credits', {})
    
    if credits:
        # Get top 3 cast members
        cast = [c.get('name', '').replace(" ", "") for c in credits.get('cast', [])[:3]]
        # Get director
        director = [c.get('name', '').replace(" ", "") for c in credits.get('crew', []) if c.get('job') == 'Director']

    # Combine all features into a single space-separated string
    # We remove spaces from names (e.g., "Tom Cruise" -> "TomCruise") so 
    # the algorithm treats the full name as a single distinct token.
    features = genres + keywords + cast + director
    return " ".join(features).lower()

def get_content_recommendations(target_movie, movie_pool, top_n=5):
    """
    Calculates cosine similarity between a target movie and a pool of movies.
    
    Args:
        target_movie (dict): The TMDB movie object the user likes.
        movie_pool (list of dicts): A list of TMDB movie objects to search through.
        top_n (int): Number of recommendations to return.
        
    Returns:
        list of tuples: [(movie_dict, explanation_string), ...]
    """
    # If the target movie isn't in our pool, add it temporarily so we can vectorize it
    pool_ids = [m.get('id') for m in movie_pool]
    if target_movie.get('id') not in pool_ids:
        movie_pool = [target_movie] + movie_pool

    # Step 1: Create the "soup" for every movie in the pool
    soups = [extract_features(m) for m in movie_pool]
    
    # Step 2: Convert the text soup into a mathematical matrix
    # We use CountVectorizer instead of TF-IDF here because we want exact matches 
    # of actors/directors to carry heavy weight, rather than penalizing them if they appear often.
    count = CountVectorizer(stop_words='english')
    count_matrix = count.fit_transform(soups)
    
    # Step 3: Calculate the Cosine Similarity matrix
    # This mathematically finds the "distance" between the movies based on their metadata words.
    cosine_sim = cosine_similarity(count_matrix, count_matrix)
    
    # Find the index of our target movie in the pool
    target_idx = [i for i, m in enumerate(movie_pool) if m.get('id') == target_movie.get('id')][0]
    
    # Get the similarity scores for the target movie compared to all others
    sim_scores = list(enumerate(cosine_sim[target_idx]))
    
    # Sort the movies based on the similarity scores (descending order)
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    # Get the scores of the top N most similar movies (ignoring index 0, which is the movie itself)
    top_indices = [i[0] for i in sim_scores[1:top_n+1]]
    
    recommendations = []
    for idx in top_indices:
        match = movie_pool[idx]
        
        # --- Enhanced Feature: Similarity Explanation ---
        # Find exactly which words overlapped to explain the recommendation to the user
        target_soup = set(soups[target_idx].split())
        match_soup = set(soups[idx].split())
        shared_traits = list(target_soup.intersection(match_soup))
        
        explanation = f"Recommended because it shares features like: {', '.join(shared_traits[:3])}"
        
        recommendations.append((match, explanation))
        
    return recommendations