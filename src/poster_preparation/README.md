# Filmster
A movie poster guessing game inspired by Hitster. Players guess movies from posters with titles automatically removed using AI text detection and inpainting.

## Features
- Automated pipeline: scrape → download → process → sample → ready to play!
- CRAFT text detection detects titles and inpainting to remove titles
- Samples 100 movies from each IMDB list given for balance

---

## Quick Start

### 1. Setup Python Environment

**Create and activate virtual environment:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

**Required packages:**
- `requests` - API calls and web scraping
- `beautifulsoup4` - HTML parsing for IMDB scraping
- `python-dotenv` - Environment variable management
- `opencv-python` - Image processing
- `easyocr` - CRAFT text detection
- `torch` and `torchvision` - EasyOCR backend
- `Pillow` - Image handling
- `qrcode` - Creates QR codes

### 3. Get TMDb API Key
1. Create a free account at [The Movie Database (TMDb)](https://www.themoviedb.org/)
2. Go to [API settings](https://www.themoviedb.org/settings/api)
3. Request an API key 
4. Copy your API key

### 4. Configure Environment
Copy the example environment file:
```powershell
Copy-Item .env.example .env
```

Edit `.env` and add your API key:
```
TMDB_API_KEY=your_actual_api_key_here
```

### 5. Run the Complete Pipeline
```powershell
.\src\poster_preparation\run_full_pipeline.ps1
```

---

## How It Works

### The Pipeline (Automated via `run_full_pipeline.ps1`)

**STEP 1: Scrape Movie Lists**
- Fetches movies from IMDB charts and lists
- Default lists:
  - IMDB Top 250 (most popular movies)
  - Two curated classic/vintage lists for variety
- Extracts movie names and years
- Uses TMDb API to verify titles and get accurate release years
- Saves to `list/movie_list.txt` (organized by source list)

**STEP 2: Download Posters**
- Uses TMDb API to fetch official movie posters
- Downloads high-quality images (w500 size)
- Saves to `output/posters/` with format: `Movie_Name_Year.jpg`
- Tracks successful and failed downloads in `list/`

**STEP 3: Process Posters**
- Loads CRAFT text detector (via EasyOCR)
- For each poster:
  1. Detects text regions using character-level detection
  2. Merges nearby text boxes
  3. Scores regions by size, position, and aspect ratio
  4. Selects most likely title region
  5. Uses inpainting to naturally remove the title
- Successful: Saves to `output/blurred_posters/`
- Failed (no text detected): Adds to `list/failed_processing.txt`

**STEP 4: Replace Failed Posters**
- Reads failed posters from `list/failed_processing.txt`
- Uses `sampled_list_*.txt` files to track which list each failed movie came from
- Replaces each failed movie with a random unused movie from THE SAME list
- Maintains exactly 100 movies per list for balanced game difficulty
- Downloads and processes replacement posters
- If replacements also fail, repeats the process

**STEP 5: Sample for Game**
- Randomly samples 100 movies from each list
- Only includes successfully processed posters from `output/blurred_posters/`
- Copies sampled posters to `game/posters/`
- Saves sampling records to `list/sampled_list_1.txt`, `list/sampled_list_2.txt`, etc.

---

## Scripts Reference

### `run_full_pipeline.ps1` - Complete Automation
**The main script that runs everything automatically.**

```powershell
# Run with default IMDB lists
.\src\poster_preparation\run_full_pipeline.ps1

# Use custom IMDB URLs
.\src\poster_preparation\run_full_pipeline.ps1 -Urls "https://www.imdb.com/chart/top/", "https://www.imdb.com/list/ls000000000"

# Force refresh (ignore cached movie lists)
.\src\poster_preparation\run_full_pipeline.ps1 -ForceRefresh
```

**What it does:**
- Runs all 5 steps sequentially
- Pauses between steps for review
- Handles errors gracefully
- Shows progress and status messages
- Conditionally replaces failed posters

**Pipeline flow:**
```
Step 1: Scrape → 
Step 2: Download → 
Step 3: Process → 
Step 4: Replace Failed (if needed) → 
  Step 4a: Download Replacements → 
  Step 4b: Process Replacements → 
Step 5: Sample → 
Complete!
```

### `prepare_posters.py` - Individual Commands
**The main Python script with modular commands for each pipeline step.**

```powershell
# Activate virtual environment first
.\.venv\Scripts\Activate.ps1

# Scrape movie lists from IMDB
python src/poster_preparation/prepare_posters.py --urls "https://www.imdb.com/chart/top/" "https://www.imdb.com/list/ls098063263"

# Download all posters
python src/poster_preparation/prepare_posters.py --download

# Process all posters (detect & remove titles)
python src/poster_preparation/prepare_posters.py --process

# Replace failed posters with alternatives
python src/poster_preparation/prepare_posters.py --replace-failed

# Sample 100 per list for game
python src/poster_preparation/prepare_posters.py --sample
```

**Command Options:**
- `--urls URL [URL ...]` - IMDB chart/list URLs to scrape
- `--force-refresh` - Ignore cached movie data
- `--download` - Download posters for all movies
- `--process` - Detect and remove titles from posters
- `--replace-failed` - Replace failed posters with alternatives from same list
- `--sample` - Sample 100 movies per list for game

### `scrape_movie_names.py` - IMDB Scraping
**Scrapes movie names from IMDB charts and lists.**

Used internally by `prepare_posters.py`. Can also be used standalone:

```python
from src.poster_preparation.scrape_movie_names import IMDBScraper

scraper = IMDBScraper()
movies = scraper.scrape_imdb_page("https://www.imdb.com/chart/top/")
# Returns: [{'name': 'Movie Name', 'year': '2023', 'imdb_id': 'tt1234567'}, ...]
```

**Features:**
- Extracts IMDB IDs for accurate TMDb matching
- Gets release years from TMDb API
- Handles foreign language titles
- Caches results in `movie_cache.json`

### `get_movie_poster.py` - Poster Fetching
**Downloads movie posters from TMDb.**

Used internally by `prepare_posters.py`. Can also be used standalone:

```python
from src.poster_preparation.get_movie_poster import MoviePosterFetcher

fetcher = MoviePosterFetcher()
fetcher.download_poster("The Matrix", "matrix.jpg", size="w500")
```

**Available sizes:** `w92`, `w154`, `w185`, `w342`, `w500`, `w780`, `original`

### `detect_title.py` - Title Detection
**Detects title text regions in movie posters using CRAFT.**

Used internally by `prepare_posters.py`. Can also test individual posters:

```powershell
python src/poster_preparation/detect_title.py "output/posters/The_Matrix_1999.jpg" "The Matrix"
```

**How it works:**
1. Loads CRAFT detector via EasyOCR
2. Detects character-level text regions
3. Merges nearby boxes horizontally and vertically
4. Scores regions by:
   - Size (larger = more likely title)
   - Position (top 60% of poster)
   - Aspect ratio (wide boxes preferred)
5. Returns best match or None

### `remove_title.py` - Title Removal
**Removes detected title from poster using inpainting.**

Used internally by `prepare_posters.py`. Can also be used standalone:

```python
from src.poster_preparation.remove_title import TitleRemover

remover = TitleRemover()
remover.remove_title_from_poster(
    input_path="poster.jpg",
    output_path="poster_clean.jpg", 
    method='inpaint',
    title_box=(x, y, w, h)
)
```

**Methods:**
- `inpaint` (default): Smart fill using surrounding pixels
- `blur`: Gaussian blur
- `black`: Black rectangle

---

## File Structure

```
Filmster/
├── .env                          # Your TMDb API key (create from .env.example)
├── .env.example                  # Template for environment variables
├── requirements.txt              # Python dependencies
├── README.md                     # This file
│
├── src/
│   └── poster_preparation/      # Poster preparation pipeline
│       ├── run_full_pipeline.ps1    # Main automation script
│       ├── prepare_posters.py       # Main pipeline orchestrator
│       ├── scrape_movie_names.py    # IMDB scraping module
│       ├── get_movie_poster.py      # TMDb poster fetching
│       ├── detect_title.py          # CRAFT text detection
│       └── remove_title.py          # Inpainting title removal
│
├── list/                        # Tracking and logs
│   ├── movie_list.txt          # All movies organized by source list
│   ├── sampled_list_1.txt      # 100 movies sampled from List 1
│   ├── sampled_list_2.txt      # 100 movies sampled from List 2
│   ├── sampled_list_3.txt      # 100 movies sampled from List 3
│   ├── successful_processing.txt
│   ├── failed_processing.txt
│   ├── successful_downloads.txt
│   └── failed_downloads.txt
│
├── output/
│   ├── posters/                # Original downloaded posters
│   └── blurred_posters/        # Processed (title removed)
│
└── game/
    └── posters/                # Final 300 posters ready for game!
```

---

## Advanced Usage

### Custom Movie Lists
Edit `src/poster_preparation/run_full_pipeline.ps1` lines 13-17 to change default lists:
```powershell
$DefaultUrls = @(
    "https://www.imdb.com/chart/top/"
    "https://www.imdb.com/list/ls000000000"  # Your custom list
)
```

Or pass URLs when running:
```powershell
.\src\poster_preparation\run_full_pipeline.ps1 -Urls "https://www.imdb.com/chart/toptv/"
```

### Adjust Sample Size
Edit `src/poster_preparation/prepare_posters.py` line ~851:
```python
sample_size = min(100, len(available_movies))  # Change 100 to desired size
```


### Manual Commands for Debugging
```powershell
# Test single poster detection
python src/poster_preparation/detect_title.py "output/posters/The_Matrix_1999.jpg" "The Matrix"

# Check what failed
Get-Content "list/failed_processing.txt"

# See what was sampled
Get-Content "list/sampled_list_1.txt"

# Count processed posters
(Get-ChildItem "output/blurred_posters" -Filter *.jpg).Count

# Count game-ready posters
(Get-ChildItem "game/posters" -Filter *.jpg).Count
```

---

## Known Limitations

### Text Detection
- CRAFT works well on most posters (~90-95% success rate)
- Fails on heavily stylized titles with graphic design elements
- Cannot detect titles that are part of complex artwork
- May struggle with very small or very large text

### Inpainting
- Works best on simple backgrounds
- May leave artifacts on complex patterns
- Cannot perfectly reconstruct obscured background details

### TMDb API
- Rate limited (check TMDb documentation)
- Some old/obscure movies may not have posters
- Relies on TMDb's poster availability

### Game Balance
- Poster difficulty varies significantly by era and style
- Older movies (pre-1960) often have simpler, text-based posters
- Modern movies have more complex designs but harder text detection

---
