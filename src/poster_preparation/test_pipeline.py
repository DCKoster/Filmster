"""
Test the complete pipeline: download poster -> detect title -> remove title
"""

from get_movie_poster import MoviePosterFetcher
from detect_title import TitleDetector
from remove_title import TitleRemover

def test_pipeline(movie_name="The Matrix"):
    """Test the complete pipeline on a movie."""
    
    print(f"=== Testing Pipeline with: {movie_name} ===\n")
    
    # Step 1: Download poster
    print("Step 1: Downloading poster...")
    fetcher = MoviePosterFetcher()
    poster_file = f"{movie_name.replace(' ', '_')}_poster.jpg"
    
    if fetcher.download_poster(movie_name, poster_file, size="w500"):
        print(f"✓ Poster downloaded: {poster_file}\n")
    else:
        print("✗ Failed to download poster")
        return
    
    # Step 2: Detect title
    print("Step 2: Detecting title...")
    detector = TitleDetector()
    title_box = detector.find_title_region(poster_file, movie_name)
    
    if title_box:
        x, y, w, h = title_box
        print(f"✓ Title detected at ({x}, {y}) with size {w}x{h}\n")
        
        # Visualize detection
        vis_file = poster_file.replace('.jpg', '_detected.jpg')
        detector.visualize_detections(poster_file, vis_file, [title_box])
        print(f"  Visualization saved: {vis_file}\n")
    else:
        print("⚠ Could not detect title (will try removal anyway)\n")
    
    # Step 3: Remove title (try all methods)
    print("Step 3: Removing title...")
    remover = TitleRemover()
    
    methods = ['blur', 'black', 'inpaint']
    for method in methods:
        output_file = poster_file.replace('.jpg', f'_{method}.jpg')
        print(f"  Testing {method} method...")
        
        success = remover.remove_title_from_poster(
            poster_file, 
            output_file, 
            method=method,
            movie_title=movie_name,
            title_box=title_box
        )
        
        if success:
            print(f"  ✓ {method}: {output_file}")
        else:
            print(f"  ✗ {method}: Failed")
    
    print(f"\n=== Pipeline Test Complete ===")
    print(f"Check the following files:")
    print(f"  - {poster_file} (original)")
    if title_box:
        print(f"  - {poster_file.replace('.jpg', '_detected.jpg')} (detection visualization)")
    for method in methods:
        print(f"  - {poster_file.replace('.jpg', f'_{method}.jpg')} ({method} removal)")

if __name__ == "__main__":
    import sys
    
    movie = sys.argv[1] if len(sys.argv) > 1 else "The Matrix"
    test_pipeline(movie)
