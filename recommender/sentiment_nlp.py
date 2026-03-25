from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob
from utils.formatting import *
import numpy as np

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
    
    Args:
        user_query (str): The user's typed input (e.g., "A happy movie about a dog").
        movie_pool (list of dicts): TMDB movie objects to search through.
        top_n (int): Number of matches to return.
        
    Returns:
        list of tuples: [(movie_dict, explanation_string), ...]
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
    # TF-IDF penalizes common words (like 'the', 'a') and highlights unique identifiers.
    tfidf = TfidfVectorizer(stop_words='english')
    
    # Fit the vectorizer on the movie plots, then transform both plots and the query
    tfidf_matrix = tfidf.fit_transform(overviews)
    query_vector = tfidf.transform([user_query])
    
    # Calculate cosine similarity between the query and all plots
    cosine_sim = cosine_similarity(query_vector, tfidf_matrix).flatten()
    
    # 5. Combine TF-IDF similarity with Sentiment alignment
    recommendations = []
    for idx, movie in enumerate(valid_movies):
        # TF-IDF score represents how closely the vocabularies match (0.0 to 1.0)
        semantic_score = cosine_sim[idx]
        
        # Sentiment penalty represents how far apart the "vibes" are. 
        # We take the absolute difference. Lower is better, meaning closer in tone.
        sentiment_diff = abs(query_sentiment - movie_sentiments[idx])
        
        # Invert the difference so higher is better (max difference is 2.0, so 2.0 - diff)
        # We normalize it so it scales well with the semantic score.
        sentiment_score = (2.0 - sentiment_diff) / 2.0
        
        # Final Score: 70% vocab match, 30% sentiment match 
        # (You can adjust these weights for your Business Rationale!)
        final_score = (semantic_score * 0.7) + (sentiment_score * 0.3)
        
        recommendations.append((final_score, semantic_score, sentiment_score, movie))
        
    # Sort by the final combined score in descending order
    recommendations = sorted(recommendations, key=lambda x: x[0], reverse=True)
    
    # 6. Format the top N results with an explanation
    top_matches = []
    for rank in range(min(top_n, len(recommendations))):
        final_score, sem_score, sent_score, movie = recommendations[rank]
        
        # Create a user-friendly explanation based on the underlying data
        sentiment_label = "Positive/Upbeat" if analyze_sentiment(movie.get('overview')) > 0.1 else "Dark/Serious" if analyze_sentiment(movie.get('overview')) < -0.1 else "Neutral/Balanced"
        
        explanation = (f"{make_bold(f'Vibe Match Score: {final_score:.2f} | ')}"
                       f"Plot Sentiment: {sentiment_label}. "
                       f"Matched based on plot keywords and emotional tone.")
        
        top_matches.append((movie, explanation))
        
    return top_matches