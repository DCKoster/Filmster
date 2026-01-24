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

### 4. Set up Github Pages
1. Make repository public
2. Deploy pages from main branch

### 5. Configure Environment
Copy the example environment file:
```powershell
Copy-Item .env.example .env
```

Edit `.env` and add your TMDb API key and Github username:
```
TMDB_API_KEY=your_actual_api_key_here
GITHUB_USERNAME=your_actual_github_username
```

### 6. Run the poster processing Complete Pipeline
```powershell
.\src\poster_preparation\run_full_pipeline.ps1
```

### 7. Run the card generation script
```powershell
.\src\card_generation\generate_cards.py
```

### 8. Post-process the resulting PDF for further purposes

---

## File Structure

```
Filmster/
├── .env                          # TMDb and Github API env (create from .env.example)
├── .env.example                  # Template for environment variables
├── requirements.txt              # Python dependencies
├── .gitignore                    # 
├── README.md                     # This file
│
├── src/
│   └── poster_preparation/      # Poster preparation pipeline
│       ├── run_full_pipeline.ps1    # Main automation script
│       ├── prepare_posters.py       # Main pipeline orchestrator
│       ├── scrape_movie_names.py    # IMDB scraping module
│       ├── get_movie_poster.py      # TMDb poster fetching
│       ├── detect_title.py          # CRAFT text detection
│       ├── remove_title.py          # Inpainting title removal
│       └── README.MD                # Explains the poster preparation    
│   └── card_generation/      
│       ├── generate_cards.py        # Creates card 
│       ├── template.pdf             # Template for the cards 
│       └── README.MD                # Explains the card generation    
│
├── list/                        # Holds the lists for the movies
│
├── output/
│   ├── posters/                # Original downloaded posters
│   └── blurred_posters/        # Processed (title removed)
│
└── game/
    └── posters/                # Posters ready for the game
```
---

## Hand-Picked Posters Workflow

Add specific posters to your game using the `add_posters.txt` file.

### Step 1: Add Movies to the List

Edit `list/add_posters.txt` and add the movies you want:

```
Avatar (2009)
Grease (1978)
Notting Hill (1999)
```

- Empty lines and lines starting with `#` are ignored
- Movie name should match IMDB title as closely as possible

### Step 2: Download and Process Posters

Run the prepare_posters.py script with the `--add-posters` flag:

```powershell
python src/poster_preparation/prepare_posters.py --add-posters
```

This will download all posters in the list, blur it and save it in output/posters/, output/blurred_posters/ and game/posters/

### Step 3: Generate Cards

Generate printable cards only for the hand-picked movies:

```powershell
python src/card_generation/generate_cards.py --add-posters
```

This will fill in the template PDF for only those posters

---

## Troubleshooting

### "TMDB_API_KEY not found"
Make sure `.env` file exists and contains:
```
TMDB_API_KEY=your_actual_api_key_here
```

### Poster download fails
- Verify TMDb API key is correct
- Some movies may not have posters on TMDb

### Title detection fails frequently
CRAFT detector has limitations with:
- Heavily stylized/artistic titles (e.g., "300")
- Graphic design titles (logos vs. text)
- Very small or very large text

**Solution:** The pipeline automatically replaces failed posters with alternatives from the same list.

### "GITHUB_USERNAME not found"
Make sure `.env` file contains:
```
GITHUB_USERNAME=your_github_username
```

### Font warning message
If you see "Could not load Eras fonts", the script will use Helvetica as fallback. To use Eras fonts:
1. Install Eras Medium ITC and Eras Bold ITC on Windows
2. Verify font files exist: `C:\Windows\Fonts\ERASMD.TTF` and `C:\Windows\Fonts\ERASBD.TTF`

### QR codes don't work
1. Check GitHub Pages is enabled: https://github.com/YOUR_USERNAME/Filmster/settings/pages
2. Verify posters are committed: `git status` should show clean
3. Test URL in browser: `https://YOUR_USERNAME.github.io/Filmster/game/posters/`
4. Try specific poster: `https://YOUR_USERNAME.github.io/Filmster/game/posters/The_Matrix_1999.jpg`

### "No posters found"
Make sure posters exist in `game/posters/` directory.

### Cards look misaligned
Use `--test-positioning` flag with 4 test posters to verify positioning matches template boxes.

### Text too small or cut off
The script automatically reduces font size (12pt → 7pt) if text is too long. If still cut off:
- Movie names wrap at 28 characters per line
- Maximum 4 lines supported
- Extremely long titles may need manual shortening

---

## License
This project is for educational and personal use. Movie data and posters are property of their respective owners (IMDB/TMDb).

## Credits
- **TMDb API** for movie metadata and poster images
- **IMDB** for movie lists
- **EasyOCR** for CRAFT text detection
- **OpenCV** for image processing