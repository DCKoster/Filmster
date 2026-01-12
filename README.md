# Filmster
Creating Hitster for movie posters - a game where you guess movies from their posters with titles removed!

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get TMDb API Key
1. Create a free account at [The Movie Database (TMDb)](https://www.themoviedb.org/)
2. Go to your [API settings](https://www.themoviedb.org/settings/api)
3. Request an API key (it's free and instant)
4. Copy your API key

### 3. Configure API Key
Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
TMDB_API_KEY=your_actual_api_key_here
```

### 4. Download EAST Model (for text detection)
```bash
python download_east_model.py
```

## Game Workflow

### Step 1: Scrape Movie List
Get movie names and years from IMDB Top 250:

```bash
python scrape_movie_names.py --auto-save
```

This creates `movie_list.txt` with 250 movies. Results are cached in `movie_cache.json`.

**Options:**
- `--force-refresh` or `-f`: Force fresh scrape (ignore cache)
- `--auto-save` or `-a`: Automatically save without prompting
- Pass a URL as argument to scrape custom IMDB lists

### Step 2: Download Movie Posters
Get posters for all movies in the list:

```bash
python get_movie_poster.py "The Matrix"
```

Or use in Python:
```python
from get_movie_poster import MoviePosterFetcher

fetcher = MoviePosterFetcher()
fetcher.download_poster("The Matrix", "the_matrix.jpg", size="w500")
```

### Step 3: Detect Title in Poster
Find where the title text is located:

```bash
python detect_title.py poster.jpg "The Matrix"
```

This will:
- Use EAST text detector to find text regions
- Score regions by size, position, and aspect ratio
- Save visualization to `poster_detected.jpg`

**In Python:**
```python
from detect_title import detect_title_in_poster

title_box = detect_title_in_poster("poster.jpg", "The Matrix")
# Returns: (x, y, width, height)
```

### Step 4: Remove/Blur Title
Create game-ready poster with title hidden:

```bash
python remove_title.py poster.jpg poster_blurred.jpg blur "The Matrix"
```

**Methods:**
- `blur`: Gaussian blur (default, looks natural)
- `black`: Black rectangle (guaranteed to hide)
- `inpaint`: Smart fill based on surrounding pixels

**Batch Processing:**
```python
from remove_title import TitleRemover

remover = TitleRemover()
remover.batch_process_posters('posters/', 'blurred_posters/', method='blur')
```

## Usage Examples

### Get Movie Poster URL
```python
from get_movie_poster import get_movie_poster

poster_url = get_movie_poster("The Matrix")
print(poster_url)
```

### Complete Pipeline
```python
from scrape_movie_names import get_top_250_movies
from get_movie_poster import MoviePosterFetcher
from remove_title import TitleRemover

# 1. Get movie list
movies = get_top_250_movies()

# 2. Download posters
fetcher = MoviePosterFetcher()
for movie in movies[:10]:  # First 10 movies
    filename = f"{movie['name'].replace(' ', '_')}.jpg"
    fetcher.download_poster(movie['name'], filename)

# 3. Blur titles
remover = TitleRemover()
remover.batch_process_posters('./', 'blurred/')
```

## Features

### Movie Scraping
- ✅ Scrapes IMDB Top 250 and other charts
- ✅ Gets accurate release years via TMDb API
- ✅ Handles foreign language titles correctly
- ✅ Uses English titles for non-Latin scripts (Japanese, Korean, etc.)
- ✅ Keeps original titles for European languages (Italian, French, etc.)
- ✅ Caches results to avoid repeated API calls
- ✅ Uses IMDB IDs for exact TMDb matching

### Poster Fetching
- ✅ Fetches **poster images only** (no backdrops)
- ✅ Multiple size options (w92 to original)
- ✅ High-quality poster URLs
- ✅ Download functionality

### Title Detection
- ✅ EAST deep learning text detector
- ✅ Fallback detection using edge detection
- ✅ Smart scoring based on size, position, aspect ratio
- ✅ Visualization of detected regions

### Title Removal
- ✅ Three removal methods: blur, black, inpaint
- ✅ Batch processing support
- ✅ Preserves image quality
- ✅ Automatic title detection

## Poster Sizes
Available sizes: `w92`, `w154`, `w185`, `w342`, `w500`, `w780`, `original`

## Requirements
- Python 3.8+
- TMDb API key (free)
- OpenCV for text detection
- EAST model file (~100MB, auto-downloaded)