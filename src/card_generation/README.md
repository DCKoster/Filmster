# Card Generation

This module generates printable game cards with QR codes for the Filmster game using GitHub Pages.

## Setup

### 1. Install Dependencies
```powershell
pip install -r src/card_generation/requirements.txt
```

### 2. Make Repository Public & Enable GitHub Pages

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

**Verify deployment:**
- Your posters will be accessible at:
  ```
  https://YOUR_USERNAME.github.io/Filmster/game/posters/Movie_Name_Year.jpg
  ```
- Test one poster URL in your browser to confirm

### 3. Configure Environment
Add your GitHub username to `.env`:
```env
GITHUB_USERNAME=your_actual_github_username
```

## Usage

### Step 1: Commit Posters to Repository
Make sure your posters are committed and pushed:
```powershell
git add game/posters/
git commit -m "Add game posters"
git push
```

Wait a few minutes for GitHub Pages to deploy.

### Step 2: Generate Printable Cards
```powershell
python src/card_generation/generate_cards.py
```

This will:
- Read posters from `game/posters/`
- Generate QR codes pointing to GitHub Pages URLs
- Create PDF with 8 cards per A4 page (2 columns × 4 rows)
- Each card shows: QR code (left) | Movie name + year (right) 

**Output:** `src/card_generation/printable_cards.pdf` ready for printing
- Might have to resave this file (open, e.g. in Edge, CTRL+P, save as PDF) to make sure all elements are correct 

## Card Layout

```
┌─────────────────────────────────────┐
│     [QR CODE]    │     The Matrix   │
│                  │       (1999)     │
│                  │                  │
├─────────────────────────────────────┤
│     [QR CODE]    │     Inception    │
│                  │     (2010)       │
│                  │                  │
├─────────────────────────────────────┤
│  ... (8 cards per A4 page)          │
└─────────────────────────────────────┘
```

## Card Specifications
- **Page size**: A4 (210mm × 297mm)
- **Cards per page**: 8 (2 columns × 4 rows)
- **Card size**: ~90mm × 63mm
- **Layout**: 60% text / 40% QR code
- **QR code**: Points to `https://YOUR_USERNAME.github.io/Filmster/game/posters/filename.jpg`


## Troubleshooting

### "GITHUB_USERNAME not found"
Make sure `.env` file contains:
```
GITHUB_USERNAME=your_github_username
```

### QR codes don't work
1. Check GitHub Pages is enabled: https://github.com/YOUR_USERNAME/Filmster/settings/pages
2. Verify posters are committed: `git status` should show clean
3. Test URL in browser: `https://YOUR_USERNAME.github.io/Filmster/game/posters/` should show 404 page but base works
4. Try specific poster: `https://YOUR_USERNAME.github.io/Filmster/game/posters/The_Matrix_1999.jpg`

### "No posters found"
Make sure posters exist in `game/posters/` directory.

## GitHub Pages URLs

Each poster gets a permanent URL:
```
https://YOUR_USERNAME.github.io/Filmster/game/posters/Movie_Name_Year.jpg
```
