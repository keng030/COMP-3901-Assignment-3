from recommender.content_based import get_content_recommendations
from recommender.sentiment_nlp import search_by_vibe

def get_hybrid_recommendations(target_movie, movie_pool, top_n=5):
    """
    Combines Content-Based (metadata) and Sentiment-Based (NLP plot) recommendations
    using a positional scoring system.
    
    Args:
        target_movie (dict): The TMDB movie object the user likes.
        movie_pool (list of dicts): TMDB movie objects to search through.
        top_n (int): Number of matches to return.
        
    Returns:
        list of tuples: [(movie_dict, explanation_string), ...]
    """
    # We pull a larger sample from both engines so we have a better chance of finding overlaps
    sample_size = min(50, len(movie_pool))
    
    # 1. Get Content-Based Recommendations (Metadata)
    content_results = get_content_recommendations(target_movie, movie_pool, top_n=sample_size)
    
    # 2. Get NLP/Sentiment Recommendations (Using the target movie's plot as the "vibe" query)
    target_plot = target_movie.get('overview', '')
    
    # If the movie doesn't have a plot, we gracefully fallback to just content-based
    if not target_plot:
        return content_results[:top_n]
        
    nlp_results = search_by_vibe(target_plot, movie_pool, top_n=sample_size)
    
    # 3. Combine scores using a weighted point system
    combined_scores = {}
    explanations = {}
    
    # Process Content Results (Weight: 60%)
    for rank, (movie, exp) in enumerate(content_results):
        m_id = movie.get('id')
        # Movies at rank 0 get maximum points, movies at rank 49 get 1 point
        points = sample_size - rank 
        combined_scores[m_id] = {'movie': movie, 'score': points * 0.6}
        explanations[m_id] = [exp] # Store the original content explanation
        
    # Process NLP Results (Weight: 40%)
    for rank, (movie, exp) in enumerate(nlp_results):
        m_id = movie.get('id')
        points = sample_size - rank
        
        if m_id in combined_scores:
            # If the movie is already in the dictionary, it's a true hybrid match! Add the scores.
            combined_scores[m_id]['score'] += (points * 0.4)
            explanations[m_id].append("Also matched plot tone and vocabulary.")
        else:
            # If it only showed up in the NLP search
            combined_scores[m_id] = {'movie': movie, 'score': points * 0.4}
            explanations[m_id] = ["Matched based on plot and emotional tone."]
            
    # 4. Sort the dictionary by the final combined score in descending order
    sorted_movies = sorted(combined_scores.values(), key=lambda x: x['score'], reverse=True)
    
    # 5. Format the top N results
    final_recommendations = []
    for item in sorted_movies[:top_n]:
        movie = item['movie']
        m_id = movie.get('id')
        
        # Combine the explanation strings so the user knows exactly why it was recommended
        exp_text = " | ".join(explanations[m_id])
        final_recommendations.append((movie, f"Hybrid Match: {exp_text}"))
        
    return final_recommendations