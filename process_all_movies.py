"""
Process all movies from movie_list.txt
Downloads posters and removes titles in batch
"""

from get_movie_poster import MoviePosterFetcher
from remove_title import TitleRemover
import os
import time


def process_movie_list(movie_list_file="movie_list.txt", 
                       output_dir="posters",
                       blurred_dir="blurred_posters",
                       method="blur",
                       max_movies=None,
                       delay=0.5):
    """
    Process movies from the list file.
    
    Args:
        movie_list_file: Path to file with movie list
        output_dir: Directory to save original posters
        blurred_dir: Directory to save blurred posters
        method: Removal method ('blur', 'black', 'inpaint')
        max_movies: Maximum number of movies to process (None = all)
        delay: Delay between API calls in seconds
    """
    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(blurred_dir, exist_ok=True)
    
    # Read movie list
    try:
        with open(movie_list_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: {movie_list_file} not found")
        print("Run: python scrape_movie_names.py --auto-save first")
        return
    
    # Parse movies
    movies = []
    for line in lines:
        line = line.strip()
        if line and '(' in line:
            # Format: "Movie Name (Year)"
            name = line.split('(')[0].strip()
            year = line.split('(')[1].split(')')[0].strip()
            movies.append({'name': name, 'year': year})
    
    if max_movies:
        movies = movies[:max_movies]
    
    print(f"=== Processing {len(movies)} movies ===\n")
    
    # Initialize components
    fetcher = MoviePosterFetcher()
    remover = TitleRemover()
    
    # Process each movie
    success_count = 0
    failed_downloads = []
    failed_removals = []
    
    for i, movie in enumerate(movies, 1):
        movie_name = movie['name']
        movie_year = movie['year']
        
        print(f"\n[{i}/{len(movies)}] {movie_name} ({movie_year})")
        print("-" * 60)
        
        # Create safe filename
        safe_name = "".join(c for c in movie_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        
        poster_file = os.path.join(output_dir, f"{safe_name}.jpg")
        blurred_file = os.path.join(blurred_dir, f"{safe_name}_blurred.jpg")
        
        # Skip if already processed
        if os.path.exists(blurred_file):
            print(f"  ✓ Already processed - skipping")
            success_count += 1
            continue
        
        # Download poster
        if not os.path.exists(poster_file):
            print(f"  Downloading poster...")
            if fetcher.download_poster(movie_name, poster_file, size="w500"):
                print(f"  ✓ Downloaded")
            else:
                print(f"  ✗ Download failed")
                failed_downloads.append(movie_name)
                continue
            
            # Delay to respect API rate limits
            time.sleep(delay)
        else:
            print(f"  ✓ Poster exists")
        
        # Remove title
        print(f"  Removing title ({method})...")
        if remover.remove_title_from_poster(poster_file, blurred_file, 
                                           method=method, movie_title=movie_name):
            print(f"  ✓ Title removed")
            success_count += 1
        else:
            print(f"  ✗ Title removal failed")
            failed_removals.append(movie_name)
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"=== Processing Complete ===")
    print(f"{'=' * 60}")
    print(f"Total movies: {len(movies)}")
    print(f"Successfully processed: {success_count}")
    print(f"Failed downloads: {len(failed_downloads)}")
    print(f"Failed removals: {len(failed_removals)}")
    
    if failed_downloads:
        print(f"\nFailed to download:")
        for name in failed_downloads[:10]:
            print(f"  - {name}")
        if len(failed_downloads) > 10:
            print(f"  ... and {len(failed_downloads) - 10} more")
    
    if failed_removals:
        print(f"\nFailed to remove titles:")
        for name in failed_removals[:10]:
            print(f"  - {name}")
        if len(failed_removals) > 10:
            print(f"  ... and {len(failed_removals) - 10} more")
    
    print(f"\nPosters saved to: {output_dir}/")
    print(f"Blurred posters saved to: {blurred_dir}/")


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Process movie posters in batch')
    parser.add_argument('--max', type=int, default=None, 
                       help='Maximum number of movies to process')
    parser.add_argument('--method', choices=['blur', 'black', 'inpaint'], 
                       default='blur', help='Title removal method')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay between API calls (seconds)')
    parser.add_argument('--input', default='movie_list.txt',
                       help='Input movie list file')
    
    args = parser.parse_args()
    
    process_movie_list(
        movie_list_file=args.input,
        method=args.method,
        max_movies=args.max,
        delay=args.delay
    )
