from html import escape
from pathlib import Path

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

st.markdown(
    """
    <style>
    .movie-art {
        box-sizing: border-box;
        aspect-ratio: 3 / 4;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 0.75rem;
        padding: 1.2rem;
        overflow: hidden;
        border-radius: 4px;
        color: #f5f0e4;
        background:
            radial-gradient(circle at 76% 24%, hsla(var(--poster-hue), 80%, 70%, 0.42), transparent 27%),
            linear-gradient(155deg, hsl(var(--poster-hue), 38%, 28%), hsl(calc(var(--poster-hue) + 48), 44%, 12%) 75%, #13151a);
    }

    .movie-art__eyebrow,
    .movie-art__genre {
        font-size: 0.7rem;
        font-weight: 600;
    }

    .movie-art__title {
        display: -webkit-box;
        overflow: hidden;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 5;
        overflow-wrap: anywhere;
        font-family: Georgia, serif;
        font-size: 1.45rem;
        line-height: 1.08;
        text-shadow: 0 2px 12px rgba(0, 0, 0, 0.45);
    }

    div[class*="st-key-movie_card_"] {
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
    }

    div[class*="st-key-movie_card_"]:hover {
        transform: scale(1.025);
        border-color: rgba(255, 193, 7, 0.75);
        box-shadow: 0 8px 24px rgba(255, 193, 7, 0.22);
    }

    @media (prefers-reduced-motion: reduce) {
        div[class*="st-key-movie_card_"] {
            transition: none;
        }

        div[class*="st-key-movie_card_"]:hover {
            transform: none;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎬 OTT Movie Recommendation Prototype")
st.write("Pick a mood, then narrow down movies by title, director, or rating.")

MOOD_GENRES = {
    "In the mood for a good cry": {"Dramas", "Romantic Movies"},
    "Need something intense": {"Action & Adventure", "Horror Movies", "Thrillers"},
    "Light & fun": {
        "Children & Family Movies",
        "Comedies",
        "Music & Musicals",
        "Stand-Up Comedy",
    },
}

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

POSTER_DIRECTORY = Path(__file__).resolve().parent / "posters"
POSTER_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def find_poster(show_id):
    poster_id = str(show_id).strip()
    if not poster_id or Path(poster_id).name != poster_id:
        return None

    for extension in POSTER_EXTENSIONS:
        poster_path = POSTER_DIRECTORY / f"{poster_id}{extension}"
        if poster_path.is_file():
            return poster_path
    return None

if "favorite_indices" not in st.session_state:
    st.session_state.favorite_indices = set()
if "shuffle_seed" not in st.session_state:
    st.session_state.shuffle_seed = 0

# ---------------------------------------------------------
# 3. Sidebar UI - User Controls
# ---------------------------------------------------------
st.sidebar.header("🔍 Filter Preferences")

selected_mood = st.sidebar.selectbox(
    "How are you feeling?", ["Any mood", *MOOD_GENRES]
)
st.sidebar.caption("Mood matches are based on the movie's genre tags.")

# Extract unique ratings
all_ratings = sorted(df_movies['rating'].dropna().unique().tolist())
all_ratings.insert(0, "All Ratings")

selected_rating = st.sidebar.selectbox("Select Content Rating", all_ratings)

# Director text search input
director_query = st.sidebar.text_input("Director Name (optional)", value="")

# Number of recommendations slider
num_results = st.sidebar.slider("Number of Recommendations", min_value=1, max_value=20, value=6)
show_favorites = st.sidebar.checkbox("Show saved movies only", value=False)

# ---------------------------------------------------------
# 4. Recommendation / Filtering Logic
# ---------------------------------------------------------
filtered_df = df_movies.copy()

# Filter by Title Search
if search_query.strip():
    filtered_df = filtered_df[
        filtered_df['title'].str.contains(search_query, case=False, na=False)
    ]

# Filter by mood using exact genre tag matches
if selected_mood != "Any mood":
    mood_genres = MOOD_GENRES[selected_mood]
    filtered_df = filtered_df[
        filtered_df["listed_in"].str.split(",").map(
            lambda genres: bool(
                {genre.strip() for genre in genres} & mood_genres
            )
        )
    ]

# Filter by Rating
if selected_rating != "All Ratings":
    filtered_df = filtered_df[filtered_df['rating'] == selected_rating]

# Filter by Director
if director_query.strip():
    filtered_df = filtered_df[
        filtered_df['director'].str.contains(director_query, case=False, na=False)
    ]

# Filter to saved movies when requested
if show_favorites:
    filtered_df = filtered_df[
        filtered_df.index.isin(st.session_state.favorite_indices)
    ]

# ---------------------------------------------------------
# 5. Display Recommendations
# ---------------------------------------------------------
if st.button("Shuffle results"):
    st.session_state.shuffle_seed += 1

if st.session_state.shuffle_seed:
    filtered_df = filtered_df.sample(
        frac=1, random_state=st.session_state.shuffle_seed
    )

st.subheader("Recommended Movies")

# Metrics Display
col1, col2, col3 = st.columns(3)
col1.metric("Total Movies", len(df_movies))
col2.metric("Matching Results", len(filtered_df))
col3.metric("Current Mood", selected_mood)
st.divider()

if not filtered_df.empty:
    top_movies = filtered_df.head(num_results)
    
    # Grid layout with 3 cards per row
    cols = st.columns(3)
    for index, (movie_index, row) in enumerate(top_movies.iterrows()):
        with cols[index % 3]:
            with st.container(border=True, key=f"movie_card_{movie_index}"):
                movie_title = str(row["title"])
                poster_path = find_poster(row.get("show_id", movie_index))
                if poster_path:
                    st.image(str(poster_path), width="stretch")
                else:
                    poster_hue = sum(ord(character) for character in movie_title) % 360
                    st.markdown(
                        f'<div class="movie-art" style="--poster-hue: {poster_hue}">'
                        '<span class="movie-art__eyebrow">FEATURE PRESENTATION</span>'
                        f'<span class="movie-art__title">{escape(movie_title)}</span>'
                        f'<span class="movie-art__genre">{escape(str(row["listed_in"]))}</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                st.subheader(row['title'])
                is_favorite = movie_index in st.session_state.favorite_indices
                if st.button(
                    "Remove from favorites" if is_favorite else "Add to favorites",
                    key=f"favorite_{movie_index}",
                ):
                    favorite_indices = set(st.session_state.favorite_indices)
                    if is_favorite:
                        favorite_indices.remove(movie_index)
                    else:
                        favorite_indices.add(movie_index)
                    st.session_state.favorite_indices = favorite_indices
                st.caption(f"⭐ **Rating:** {row['rating']} | 📅 **Year:** {row['release_year']}")
                st.markdown(f"**Genres:** {row['listed_in']}")
                st.markdown(f"**Director:** {row['director']}")
            
    st.success(f"Found {len(filtered_df)} total matching title(s). Displaying top {len(top_movies)}.")
else:
    st.warning("No movies found matching your selected criteria. Try broadening your filter parameters.")
