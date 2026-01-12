# Title Detection and Removal - Technical Approach

## Overview
The Filmster game requires removing movie titles from posters while preserving the visual appeal. This document explains the implementation approach for text detection and removal.

## Step 3: Title Detection (`detect_title.py`)

### Chosen Approach: EAST Text Detector + Smart Filtering

**Why EAST?**
- Fast and accurate deep learning model for text detection
- Works with various fonts, sizes, and orientations
- Returns precise bounding boxes
- Pre-trained model available (~100MB)

**Alternative Approaches Considered:**
1. **Tesseract OCR**: Slower, less accurate for stylized poster fonts
2. **Template Matching**: Requires knowing the font beforehand
3. **Edge Detection**: Simple but less reliable for complex backgrounds

### Implementation Details

#### Text Detection Pipeline:
```python
1. Load poster image
2. Resize to multiple of 32 (EAST requirement)
3. Run EAST detector → Get text regions
4. Apply Non-Maximum Suppression → Remove overlaps
5. Filter by minimum size → Remove small text
```

#### Smart Title Identification:
Since EAST detects ALL text (titles, taglines, credits, etc.), we score each region:

**Scoring Factors:**
- **Size (50%)**: Titles are usually large (0.3% of image area)
- **Position (30%)**: Titles typically in top third or center
- **Aspect Ratio (20%)**: Titles are wide (width/height > 1)

**Formula:**
```python
score = (size_score * 0.5) + (position_score * 0.3) + (aspect_score * 0.2)
```

The highest-scoring region is considered the title.

#### Fallback Detection:
If EAST model is unavailable, uses edge detection + contours:
```python
1. Convert to grayscale
2. Apply adaptive thresholding
3. Find contours
4. Filter by size and aspect ratio
```

Less accurate but works without model file.

### Usage
```python
from detect_title import TitleDetector

detector = TitleDetector()
title_box = detector.find_title_region("poster.jpg", "The Matrix")
# Returns: (x, y, width, height)
```

## Step 4: Title Removal (`remove_title.py`)

### Three Removal Methods Implemented

#### Method 1: Gaussian Blur (Default - Recommended)

**Advantages:**
- ✅ Natural looking
- ✅ Clear indication something was hidden
- ✅ Preserves overall aesthetic
- ✅ Adjustable blur strength

**How it works:**
```python
1. Extract title region from image
2. Apply Gaussian blur kernel (default: 50x50)
3. Replace original region with blurred version
```

**Best for:** Most posters, especially with complex backgrounds

#### Method 2: Black Box

**Advantages:**
- ✅ Guaranteed to hide text
- ✅ Fast and simple
- ✅ No ambiguity

**Disadvantages:**
- ❌ Looks artificial
- ❌ May draw more attention

**How it works:**
```python
1. Draw filled rectangle over title region
2. Use black (0, 0, 0) or custom color
```

**Best for:** Minimalist posters, when blur isn't strong enough

#### Method 3: Inpainting

**Advantages:**
- ✅ Most natural result
- ✅ "Fills in" the area intelligently

**Disadvantages:**
- ❌ May fail on complex backgrounds
- ❌ Slower than other methods
- ❌ Can create artifacts

**How it works:**
```python
1. Create mask of title region
2. Use OpenCV inpainting (TELEA algorithm)
3. Algorithm fills area based on surrounding pixels
```

**Best for:** Simple backgrounds, solid colors

### Method Comparison

| Method | Speed | Quality | Reliability | Recommended For |
|--------|-------|---------|-------------|----------------|
| Blur | Fast | Good | High | Most posters |
| Black | Fastest | Acceptable | Very High | Minimalist designs |
| Inpaint | Slow | Excellent* | Medium | Simple backgrounds |

*Quality varies based on background complexity

### Usage

**Single poster:**
```python
from remove_title import remove_title_from_poster

remove_title_from_poster(
    "poster.jpg", 
    "poster_blurred.jpg", 
    method="blur",
    movie_title="The Matrix"
)
```

**Batch processing:**
```python
from remove_title import TitleRemover

remover = TitleRemover()
remover.batch_process_posters(
    poster_dir='posters/',
    output_dir='blurred/',
    method='blur'
)
```

## Complete Pipeline

```python
# 1. Scrape movies
python scrape_movie_names.py --auto-save

# 2. Process all posters
python process_all_movies.py --method blur --max 10

# Results in:
# - posters/ (original posters)
# - blurred_posters/ (game-ready posters)
```

## Performance Considerations

### Text Detection
- **EAST model**: ~0.5-1s per image
- **Fallback method**: ~0.1-0.3s per image
- **Model size**: 100MB (one-time download)

### Title Removal
- **Blur**: ~0.1s per image
- **Black**: ~0.05s per image
- **Inpaint**: ~0.3-0.5s per image

### Batch Processing
For 250 movies:
- Download posters: ~5-10 minutes (with API delays)
- Title detection + removal: ~2-5 minutes
- **Total**: ~10-15 minutes for complete game setup

## Error Handling

### When Title Detection Fails:
1. Try fallback detection method
2. Use largest text region as default
3. Allow manual bounding box specification

### When Removal Fails:
1. Log error but continue with next movie
2. Keep original poster as fallback
3. Report failed movies in summary

## Future Improvements

**Potential Enhancements:**
1. Use OCR to verify detected text matches movie title
2. Train custom model on movie poster fonts
3. Add more sophisticated scoring (detect taglines vs titles)
4. Implement smart inpainting using AI models (e.g., LaMa)
5. Add edge blending for more natural transitions
6. Support for multi-line titles

## Dependencies

```
opencv-python>=4.8.0  # EAST detector, image processing
numpy>=1.24.0         # Array operations
```

## Files

- `detect_title.py`: Text detection implementation
- `remove_title.py`: Title removal implementation  
- `download_east_model.py`: EAST model downloader
- `test_pipeline.py`: End-to-end test
- `process_all_movies.py`: Batch processor
