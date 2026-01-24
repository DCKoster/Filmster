# Card Generation

This module generates printable game cards with QR codes for the Filmster game using GitHub Pages and a custom template.

## Setup

### 1. Install Dependencies
```powershell
pip install qrcode[pil] Pillow reportlab python-dotenv PyPDF2
```

### 2. Font Installation
The cards use **Eras Medium ITC** and **Eras Bold ITC** fonts:
- These fonts should be installed in your Windows font directory
- Font files: `ERASMD.TTF` (Medium) and `ERASBD.TTF` (Bold)
- If not found, the system will fall back to Helvetica

### 3. Make Repository Public & Enable GitHub Pages

**Make repository public:**
1. Go to: https://github.com/YOUR_USERNAME/Filmster/settings
2. Scroll to "Danger Zone" at bottom
3. Click "Change visibility" → "Change to public"
4. Confirm the change

**Enable GitHub Pages:**
1. In repository settings, click "Pages" in left sidebar
2. Under "Source": Select **"Deploy from a branch"**
3. Under "Branch": Select **"main"** (or your default branch)
4. Folder: Select **"/ (root)"**
5. Click **"Save"**
6. Wait 2-3 minutes for deployment

- Your posters will be accessible at:
  ```
  https://YOUR_USERNAME.github.io/Filmster/game/posters/Movie_Name_Year.jpg
  ```

### 4. Configure Environment
Add your GitHub username to `.env`:
```env
GITHUB_USERNAME=your_actual_github_username
```

## Usage

**Basic usage (all posters):**
```powershell
python src/card_generation/generate_cards.py
```


### Command Line Arguments
- `--poster-dir`: Directory containing posters (default: `game/posters`)
- `--output`: Output PDF file (default: `src/card_generation/printable_cards.pdf`)
- `--template`: Template PDF file (default: `src/card_generation/template.pdf`)
- `--debug`: Process only the first poster for testing
- `--test-positioning`: Process only 4 posters (one per row) to test positioning
- `--add-posters`: Used to add posters hand-picked posters

## How It Works

The script:
1. Reads posters from `game/posters/`
2. Generates QR codes pointing to GitHub Pages URLs (transparent background)
3. Uses `template.pdf` as the base with pre-styled boxes
4. Overlays QR codes (left) and text (right) on each row
5. Creates PDF with 4 rows per page

**Output:** `src/card_generation/printable_cards.pdf` ready for printing
