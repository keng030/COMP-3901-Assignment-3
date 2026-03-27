from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob
from utils.formatting import *
import numpy as np
import random 

def analyze_sentiment(text):
    """
    Uses TextBlob to calculate the sentiment polarity of a given text.
    Returns a float between -1.0 (highly negative/dark) and 1.0 (highly positive/upbeat).
    """
    if not text or not isinstance(text, str):
        return 0.0  # Neutral if no text is available
    
    # TextBlob uses a pre-trained lexicon to determine sentiment
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def search_by_vibe(user_query, movie_pool, top_n=5):
    """
    Matches a user's natural language query to movie plot descriptions using 
    both TF-IDF vectorization and sentiment polarity matching.
    """
    # 1. Handle edge cases: Filter out movies with no plot summary
    valid_movies = [m for m in movie_pool if m.get('overview')]
    if not valid_movies:
        return []

    overviews = [m.get('overview') for m in valid_movies]
    
    # 2. Analyze sentiment of the user's query
    query_sentiment = analyze_sentiment(user_query)
    
    # 3. Analyze sentiment of all movie plots
    movie_sentiments = [analyze_sentiment(plot) for plot in overviews]
    
    # 4. TF-IDF Vectorization for semantic matching
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(overviews)
    query_vector = tfidf.transform([user_query])
    cosine_sim = cosine_similarity(query_vector, tfidf_matrix).flatten()
    
    # 5. Combine TF-IDF similarity with Sentiment alignment
    recommendations = []
    for idx, movie in enumerate(valid_movies):
        semantic_score = cosine_sim[idx]
        sentiment_diff = abs(query_sentiment - movie_sentiments[idx])
        sentiment_score = (2.0 - sentiment_diff) / 2.0
        final_score = (semantic_score * 0.7) + (sentiment_score * 0.3)
        
        recommendations.append((final_score, semantic_score, sentiment_score, movie))
        
    # Sort by the final combined score in descending order
    recommendations = sorted(recommendations, key=lambda x: x[0], reverse=True)
    
    # --- 6. NEW CODE: The Top-N Pool Shuffle ---
    # Grab the top 20 best matches (or fewer if the pool is small)
    pool_size = min(20, len(recommendations))
    top_candidates = recommendations[:pool_size]
    
    # Randomly select 'top_n' from that top 20 pool
    sample_size = min(top_n, len(top_candidates))
    sampled_recommendations = random.sample(top_candidates, sample_size)
    
    # Optional but recommended: Re-sort the random 5 so the best score still shows at the top of the UI
    sampled_recommendations = sorted(sampled_recommendations, key=lambda x: x[0], reverse=True)
    # -------------------------------------------
    
    # 7. Format the top N results with an explanation
    top_matches = []
    for rank in range(len(sampled_recommendations)):
        final_score, sem_score, sent_score, movie = sampled_recommendations[rank]
        
        # Create a user-friendly explanation based on the underlying data
        sentiment_label = "Positive/Upbeat" if analyze_sentiment(movie.get('overview')) > 0.1 else "Dark/Serious" if analyze_sentiment(movie.get('overview')) < -0.1 else "Neutral/Balanced"
        
        explanation = (f"{make_bold(f'Vibe Match Score: {final_score:.2f} | ')}"
                       f"Plot Sentiment: {sentiment_label}. "
                       f"Matched based on plot keywords and emotional tone.")
        
        top_matches.append((movie, explanation))
        
    return top_matches