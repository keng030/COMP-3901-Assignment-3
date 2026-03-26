import gradio as gr

# Importing our actual backend logic!
from api.tmdb_client import discover_filtered_movies, search_movies, get_movie_details, get_trending_movies, get_person_id
from utils.filters import build_discover_params, format_filter_results
from utils.data_processor import build_detailed_movie_pool, format_movie_for_ui
from recommender.content_based import get_content_recommendations
from recommender.sentiment_nlp import search_by_vibe
from recommender.hybrid_engine import get_hybrid_recommendations
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

# --- REAL BACKEND FUNCTIONS ---

def filter_movies(year_start, year_end, min_rating, min_votes, runtime_start, runtime_end, cert, lang, genres, personnel_name):
    """Handles Tab 1: Translates UI inputs into API calls and formats the results."""
    
    # 1. Translate the typed name into a TMDB ID
    person_id = get_person_id(personnel_name) if personnel_name else None
    
    # 2. Handle the optional certification. If the user selects "Any", we don't set a certification.
    final_cert = None if cert == "Any" else cert

    # 3. Handle the optional language. If the user selects "Any", we don't set a language.
    final_lang = None if lang == "Any" else lang

    # 3. Build the API parameters
    params = build_discover_params(
        year_range=[year_start, year_end],
        min_rating=min_rating,
        min_votes=min_votes,
        runtime_range=[runtime_start, runtime_end],
        certification=final_cert,
        language=final_lang,
        genres=genres,
        personnel_id=person_id # Add the translated ID here!
    )
    
    # 4. Fetch from TMDB
    raw_movies = discover_filtered_movies(params)
    
    # 5. Format for UI
    return format_filter_results(raw_movies)

def recommend_movies(movie_name, algorithm):
    """Handles Tab 2: Finds a target movie, builds a pool, and runs the selected algorithm."""
    if not movie_name.strip():
        return "Please enter a movie name.", "No movie entered."
        
    # 1. Search for the target movie to get its ID
    search_results = search_movies(movie_name)
    if not search_results:
        return f"Could not find a movie named '{movie_name}'. Try another title.", ""
        
    target_movie_basic = search_results[0]
    
    # 2. Fetch the deep details (Cast, Crew, Keywords) for the target movie
    target_movie = get_movie_details(target_movie_basic['id'])
    if not target_movie:
        return "Error fetching movie details.", ""

    # 3. Build a pool of movies to compare against (e.g., top 40 trending movies)
    trending_basic = get_trending_movies(time_window="week")
    movie_pool = build_detailed_movie_pool(trending_basic, max_movies=40)

    # 4. Route to the chosen algorithm
    if algorithm == "Content-Based (Metadata)":
        raw_recs = get_content_recommendations(target_movie, movie_pool, top_n=5)
    elif algorithm == "Sentiment-Based (Plot Analysis)":
        plot = target_movie.get('overview', '')
        if not plot:
            return "This movie has no plot summary to analyze.", ""
        raw_recs = search_by_vibe(plot, movie_pool, top_n=5)
    else: # Hybrid
        raw_recs = get_hybrid_recommendations(target_movie, movie_pool, top_n=5)

    # 5. Format the results
    if not raw_recs:
        return "No matches found.", "Try a different movie or algorithm."
        
    results_text = ""
    explanations_text = ""
    
    for idx, (movie, exp) in enumerate(raw_recs, 1):
        results_text += f"{idx}. {format_movie_for_ui(movie)}\n"
        explanations_text += f"{idx}. {movie.get('title')}: {exp}\n"
        
    return results_text, explanations_text

def vibe_search(user_query):
    """Handles Tab 3: NLP natural language search against movie plots."""
    if not user_query.strip():
        return "Please enter a vibe or plot description."
        
    # Build a pool of movies to search through
    trending_basic = get_trending_movies(time_window="week")
    movie_pool = build_detailed_movie_pool(trending_basic, max_movies=40)
    
    # Run the NLP engine
    raw_recs = search_by_vibe(user_query, movie_pool, top_n=5)
    
    if not raw_recs:
        return "No matches found for that vibe. Try different keywords!"
        
    # Format results
    results_text = ""
    for idx, (movie, exp) in enumerate(raw_recs, 1):
        results_text += f"{idx}. {format_movie_for_ui(movie)}\n   ↳ 💡 {exp}\n\n"
        
    return results_text

# Enhanced Feature: Trending Movie Ratings Comparison Plot
def generate_trend_plot():
    """
    Fetches the top 15 trending movies and plots a comparative 
    bar chart of their user ratings.
    """
    # 1. Fetch the hottest movies right now with at least 100 votes
    params = {
        "sort_by": "popularity.desc",
        "vote_count.gte": 100
    }
    movies = discover_filtered_movies(params)
    
    if not movies:
        return None
        
    # 2. Extract data for the top 15 movies
    top_movies = movies[:15]
    titles = [m.get("title", "Unknown") for m in top_movies]
    ratings = [m.get("vote_average", 0) for m in top_movies]
    
    # 3. Create a beautiful Matplotlib Bar Chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Draw horizontal bars (reversing lists so highest popularity is at the top)
    ax.barh(titles[::-1], ratings[::-1], color='lightblue', edgecolor='black')
    
    # Add a vertical dashed line for the "average" rating of this specific group
    avg_rating = sum(ratings) / len(ratings)
    ax.axvline(avg_rating, color='lime', linestyle='dashed', linewidth=2, label=f'Group Avg: {avg_rating:.1f}')
    
    # Formatting to make it look professional
    ax.set_title("Currently Trending: Movie Ratings Comparison", fontsize=14, fontweight='bold')
    ax.set_xlabel("TMDB User Rating (0-10)", fontsize=12)
    ax.set_xlim(0, 10)
    ax.legend()
    
    plt.tight_layout() # Keeps long movie titles from getting cut off
    
    return fig

# --- GRADIO UI LAYOUT ---

my_theme = gr.themes.Ocean(
    font=[gr.themes.GoogleFont("Inconsolata"), "Arial", "sans-serif"]
)

with gr.Blocks(title="Cinematchr: AI Movie Recommender") as demo:
    
    gr.Markdown("# 🎬 Cinematchr")
    gr.Markdown("Discover your next favorite film using metadata, collaborative signals, and natural language processing.")
    
    with gr.Tabs():
        
# TAB 1: Core Filtering
        with gr.TabItem("🔍 Advanced Filters"):
            gr.Markdown("### Advanced Filtering Capabilities")
            gr.Markdown("Adjust the filters to find movies that match your criteria.")
            with gr.Row():
                with gr.Column():
                    gr.Markdown("**Temporal & Quality**")
                    year_start = gr.Slider(minimum=1920, maximum=2026, value=1990, step=1, label="Start Year")
                    year_end = gr.Slider(minimum=1920, maximum=2026, value=2024, step=1, label="End Year")
                    rating_slider = gr.Slider(minimum=0, maximum=10, value=7.0, step=0.5, label="Minimum Rating")
                    vote_slider = gr.Slider(minimum=0, maximum=10000, value=100, step=50, label="Minimum Vote Count")
                    
                    gr.Markdown("**Content Specifications**")
                    runtime_start = gr.Slider(minimum=0, maximum=300, value=60, step=10, label="Min Runtime (mins)")
                    runtime_end = gr.Slider(minimum=0, maximum=300, value=180, step=10, label="Max Runtime (mins)")
                    cert_dropdown = gr.Dropdown(choices=["Any","G", "PG", "PG-13", "R", "NC-17"], label="Certification Level (US)")
                    lang_dropdown = gr.Dropdown(choices=["Any", "en", "es", "fr", "ja", "ko"], label="Language Code (e.g., en for English)")
                    
                    gr.Markdown("**Personnel**")
                    personnel_input = gr.Textbox(label="Actor or Director (e.g., Tom Hanks, Christopher Nolan)", placeholder="Type a name...")

                    gr.Markdown("**Genres**")
                    genre_dropdown = gr.Dropdown(
                        choices=[
                            "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", 
                            "Drama", "Family", "Fantasy", "History", "Horror", "Music", 
                            "Mystery", "Romance", "Sci-Fi", "TV Movie", "Thriller", "War", "Western"
                        ], 
                        label="Select Genres (Combines with OR)",
                        multiselect=True # This satisfies the "logical operators" requirement!
                    )
                    


                    filter_btn = gr.Button("Apply Filters", variant="primary")
                
                with gr.Column():
                    filter_results = gr.Textbox(label="Results", lines=20)
            
            # Wire up all the new inputs to the button
            filter_btn.click(
                fn=filter_movies, 
                inputs=[year_start, year_end, rating_slider, vote_slider, runtime_start, runtime_end, cert_dropdown, lang_dropdown, personnel_input, genre_dropdown], 
                outputs=filter_results
            )

        # TAB 2: Recommendations
        with gr.TabItem("🤝 Movie Matchmaker"):
            gr.Markdown("### Get recommendations based on a movie you love!")
            with gr.Row():
                with gr.Column():
                    target_movie = gr.Textbox(label="Enter a Movie Title (e.g., Inception)")
                    algo_choice = gr.Radio(
                        choices=["Content-Based (Metadata)", "Sentiment-Based (Plot Analysis)", "Hybrid (Combined)"],
                        value="Hybrid (Combined)",
                        label="Choose Recommendation Engine"
                    )
                    rec_btn = gr.Button("Find Matches", variant="primary")
                
                with gr.Column():
                    rec_results = gr.Textbox(label="Recommended Movies", lines=8)
                    rec_explanation = gr.Textbox(label="Why we recommended these (Explanation)", lines=4)
            
            rec_btn.click(fn=recommend_movies, inputs=[target_movie, algo_choice], outputs=[rec_results, rec_explanation])

        # TAB 3: NLP "Vibe" Search
        with gr.TabItem("✨ Vibe Search (NLP)"):
            gr.Markdown("### Natural Language Query Interface")
            gr.Markdown("Describe the *vibe* or plot you are looking for. Our NLP engine will analyze sentiment and plot descriptions to find a match.")
            with gr.Row():
                with gr.Column():
                    vibe_input = gr.Textbox(
                        label="What are you in the mood for?",
                        placeholder="e.g., A dark and gritty detective story set in a futuristic city..."
                    )
                    vibe_btn = gr.Button("Search by Vibe", variant="primary")
                with gr.Column():
                    vibe_results = gr.Textbox(label="NLP Matches", lines=12)

            vibe_btn.click(fn=vibe_search, inputs=vibe_input, outputs=vibe_results)
        
        # TAB 4: Data Visualizations
        with gr.TabItem("📊 Data Trends"):
            gr.Markdown("### Trending Content Analysis")
            gr.Markdown("This visualization dynamically fetches the most popular movies right now and compares their user ratings to highlight current cultural trends.")
            
            with gr.Row():
                trend_btn = gr.Button("Generate Live Trend Report", variant="primary")
            
            with gr.Row():
                # Gradio has a native Plot component for Matplotlib figures!
                trend_plot = gr.Plot(label="Live Data Visualization")
                
            # Wire it up!
            trend_btn.click(
                fn=generate_trend_plot,
                inputs=[],
                outputs=trend_plot
            )

# --- LAUNCH APP ---
if __name__ == "__main__":
    demo.launch(share=False, theme=my_theme)