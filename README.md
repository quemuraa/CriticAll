# CriticAll

CriticAll is an open-source personal library created to be a unified place where you can organize, rate, and review different types of media.

Currently, users can rate and track movies, TV shows, anime, and video games.

Developed with Python and Streamlit, CriticAll integrates multiple APIs to bring different types of media together in one library.

## Features

- Search for movies, TV shows, anime, and video games.
- Select one or multiple media types before searching.
- Save media to a personal library.
- Rate media on a scale from 0 to 10.
- Write and edit personal reviews.
- Track the month and year of completion.
- Browse previously saved media in a visual library.

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Main programming language |
| Streamlit | Application interface |
| SQLite | Local database |
| Requests | HTTP requests to external APIs |
| RapidFuzz | Title similarity calculation |
| Git & GitHub | Version control and source code hosting |

### API Integrations

CriticAll currently integrates three external APIs:

- **AniList:** Anime data.
- **IGDB:** Video game data.
- **TMDB:** Movie and TV show data.

Each API provides information such as titles, descriptions, cover images, release dates, and popularity metrics.

## How It Works

### API Integration

CriticAll retrieves media information from multiple external APIs.

Since each API returns data in a different format, the application uses adapters to convert the responses into a common internal structure.

This allows different types of media to be processed and displayed together through the same search and library system.

### Media Type Selection

Before searching, users must select at least one media type.

Multiple types can be selected simultaneously.

Only the APIs corresponding to the selected media types are queried, avoiding unnecessary requests to unrelated sources.

For example, selecting Anime and Video Games will query AniList and IGDB without making requests to TMDB.

### Search & Ranking

CriticAll uses a custom ranking algorithm to organize search results based on their relevance to the user's query.

The algorithm considers two main factors: title similarity and popularity.

#### Title Similarity

Title similarity is calculated using RapidFuzz, comparing the user's search query with the titles and alternative titles of each work.

This allows the application to identify relevant results even when the search query does not exactly match the original title.

#### Popularity Normalization

Since AniList, IGDB, and TMDB use different popularity metrics and scales, their raw popularity values cannot be directly compared.

For example, a popularity value of 1,000 from AniList does not necessarily represent the same level of popularity as a value of 1,000 from IGDB.

To address this, CriticAll applies source-specific normalization factors:

```python
FATORES_NORMALIZACAO = {
    "anime": 20000,
    "jogo": 100,
    "filme": 5000,
    "serie": 5000,
}
```

These factors were empirically chosen to bring popularity values from different APIs into more comparable ranges.

The normalized popularity is calculated by dividing the original popularity value by the corresponding factor:

```python
pop_calibrada = popularidade / fator
```

A logarithmic transformation is then applied to reduce the influence of extremely popular works:

```python
score_pop = min(100, math.log(pop_calibrada + 1) * 25)
```

This prevents popularity differences from disproportionately affecting the ranking.

The current normalization factors are heuristic and may require further calibration as additional media sources are integrated.

#### Final Ranking

The final score combines textual similarity and normalized popularity:

```python
final_score = (text_similarity * 0.7) + (popularity_score * 0.3)
```

The current algorithm assigns:

- **70% weight to title similarity.**
- **30% weight to normalized popularity.**

This approach prioritizes how closely a result matches the user's search while also considering its popularity.

Results are then sorted by their final score, with the highest-scoring works appearing first.

### Local Database

CriticAll uses SQLite to store the user's personal library locally.

Saved records include information such as the media title, source, rating, review, and completion date.

The database allows users to access their previously saved media and update their ratings and reviews.

The database is created automatically when the application starts.

## Installation

### Prerequisites

- Python 3.10 or newer
- Git
- API credentials for IGDB/Twitch and TMDB

### 1. Clone the repository

```bash
git clone https://github.com/quemuraa/CriticAll.git

cd CriticAll
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate the environment.

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure API credentials

Create a folder named `.streamlit` in the project directory.

Inside this folder, create a file named `secrets.toml`.

Add your API credentials using the following structure:

```toml
IGDB_CLIENT_ID = "your_igdb_client_id"
IGDB_CLIENT_SECRET = "your_igdb_client_secret"

TMDB_API_KEY = "your_tmdb_api_key"
```

IGDB authentication requires a Twitch Developer application.

**Never commit your actual API credentials to GitHub.**

The `.streamlit/secrets.toml` file is excluded from version control through `.gitignore`.

### 5. Run the application

```bash
streamlit run app.py
```

Streamlit will start a local server and provide an address to access the application through your browser.

## Project Structure

```text
CriticAll/
│
├── app.py
├── anilist.py
├── igdb.py
├── tmdb.py
├── db.py
├── requirements.txt
├── .gitignore
└── README.md
```

**app.py:** Main application, including the Streamlit interface, media search, ranking algorithm, and personal library.

**anilist.py:** AniList API integration for anime.

**igdb.py:** IGDB API integration and authentication for video games.

**tmdb.py:** TMDB API integration for movies and TV shows.

**db.py:** SQLite database initialization, storage, and retrieval operations.

**requirements.txt:** Python dependencies required to run the project.

## Roadmap

CriticAll is still under development. Some features planned for future versions include:

- Support for additional media types, such as books and manga.
- More filtering and sorting options for the personal library.
- Media tracking statuses: watchlist, watching, and watched.
- User accounts and individual libraries.
- Social features for sharing reviews and discovering new media.
- Personalized media recommendations.
- Migration from Streamlit to a dedicated frontend and backend architecture.

## Author

Developed by [quemuraa](https://github.com/quemuraa).