import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# 1. Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="OTT Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 OTT Movie Recommendation Prototype")
st.write("Filter content by genre, director, or age/content rating.")

# Title Search Bar
search_query = st.text_input("🔍 Search by Movie Title", placeholder="Type a movie title...")

# ---------------------------------------------------------
# 2. Data Loading Function (Cached for Performance)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    file_path = "netflix_titles.csv"
    
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        # Fallback sample dataset if CSV path is not found
        data = {
            'type': ['Movie', 'Movie', 'Movie', 'Movie', 'Movie'],
            'title': ['Inception', 'Interstellar', 'The Dark Knight', 'Pulp Fiction', 'Spirited Away'],
            'director': ['Christopher Nolan', 'Christopher Nolan', 'Christopher Nolan', 'Quentin Tarantino', 'Hayao Miyazaki'],
            'listed_in': ['Action, Sci-Fi', 'Sci-Fi, Drama', 'Action, Crime', 'Crime, Drama', 'Animation, Fantasy'],
            'rating': ['PG-13', 'PG-13', 'PG-13', 'R', 'PG'],
            'release_year': [2010, 2014, 2008, 1994, 2001]
        }
        df = pd.DataFrame(data)

    # Clean missing values
    df['director'] = df['director'].fillna('Unknown')
    df['rating'] = df['rating'].fillna('Unknown')
    df['listed_in'] = df['listed_in'].fillna('Unknown')
    
    # Filter only movies
    movies_df = df[df['type'] == 'Movie'].copy()
    return movies_df

df_movies = load_data()

# ---------------------------------------------------------
# 3. Sidebar UI - User Controls
# ---------------------------------------------------------
st.sidebar.header("🔍 Filter Preferences")

# Extract unique genres from comma-separated 'listed_in' strings
all_genres = sorted(list(set(
    [g.strip() for sublist in df_movies['listed_in'].dropna().str.split(',') for g in sublist]
)))
all_genres.insert(0, "All Genres")

selected_genre = st.sidebar.selectbox("Select Genre", all_genres)

# Extract unique ratings
all_ratings = sorted(df_movies['rating'].dropna().unique().tolist())
all_ratings.insert(0, "All Ratings")

selected_rating = st.sidebar.selectbox("Select Content Rating", all_ratings)

# Director text search input
director_query = st.sidebar.text_input("Director Name (optional)", value="")

# Number of recommendations slider
num_results = st.sidebar.slider("Number of Recommendations", min_value=1, max_value=20, value=6)

# ---------------------------------------------------------
# 4. Recommendation / Filtering Logic
# ---------------------------------------------------------
filtered_df = df_movies.copy()

# Filter by Title Search
if search_query.strip():
    filtered_df = filtered_df[
        filtered_df['title'].str.contains(search_query, case=False, na=False)
    ]

# Filter by Genre
if selected_genre != "All Genres":
    filtered_df = filtered_df[
        filtered_df['listed_in'].str.contains(selected_genre, case=False, na=False)
    ]

# Filter by Rating
if selected_rating != "All Ratings":
    filtered_df = filtered_df[filtered_df['rating'] == selected_rating]

# Filter by Director
if director_query.strip():
    filtered_df = filtered_df[
        filtered_df['director'].str.contains(director_query, case=False, na=False)
    ]

# ---------------------------------------------------------
# 5. Display Recommendations
# ---------------------------------------------------------
st.subheader("Recommended Movies")

# Metrics Display
col1, col2, col3 = st.columns(3)
col1.metric("Total Movies", len(df_movies))
col2.metric("Matching Results", len(filtered_df))
col3.metric("Current Genre", selected_genre)
st.divider()

if not filtered_df.empty:
    top_movies = filtered_df.head(num_results)
    
    # Grid layout with 3 cards per row
    cols = st.columns(3)
    for index, (_, row) in enumerate(top_movies.iterrows()):
        with cols[index % 3]:
            st.image("https://via.placeholder.com/300x400?text=Movie+Poster", use_container_width=True)
            st.subheader(row['title'])
            st.caption(f"⭐ **Rating:** {row['rating']} | 📅 **Year:** {row['release_year']}")
            st.markdown(f"**Genres:** {row['listed_in']}")
            st.markdown(f"**Director:** {row['director']}")
            st.divider()
            
    st.success(f"Found {len(filtered_df)} total matching title(s). Displaying top {len(top_movies)}.")
else:
    st.warning("No movies found matching your selected criteria. Try broadening your filter parameters.")
