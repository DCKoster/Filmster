"""
Prepare Posters - Main entry point for Filmster game preparation
Handles scraping multiple IMDB lists, validation, and poster preparation.
"""

import os
import sys
import requests
from typing import List, Dict, Tuple
from scrape_movie_names import IMDBScraper
from get_movie_poster import MoviePosterFetcher
from remove_title import TitleRemover
import time


class PosterPreparer:
    """Main class for preparing movie posters for the game."""
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize the preparer.
        
        Args:
            use_cache: Whether to use cached data
        """
        self.use_cache = use_cache
        self.scraper = IMDBScraper(use_cache=use_cache)
    
    def validate_urls(self, urls: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate that all IMDB URLs are reachable.
        
        Args:
            urls: List of IMDB URLs to validate
            
        Returns:
            Tuple of (valid_urls, invalid_urls)
        """
        print("=== Validating IMDB URLs ===")
        valid = []
        invalid = []
        
        for url in urls:
            print(f"\nChecking: {url}")
            try:
                response = requests.head(url, timeout=10, allow_redirects=True)
                # Accept 200, 202, and other 2xx status codes
                if 200 <= response.status_code < 300:
                    print(f"  ✓ Reachable (status {response.status_code})")
                    valid.append(url)
                else:
                    print(f"  ✗ Status code: {response.status_code}")
                    invalid.append(url)
            except requests.RequestException as e:
                print(f"  ✗ Error: {e}")
                invalid.append(url)
        
        print(f"\n{'=' * 60}")
        print(f"Valid URLs: {len(valid)}/{len(urls)}")
        if invalid:
            print(f"Invalid URLs: {len(invalid)}")
            for url in invalid:
                print(f"  - {url}")
            sys.exit(1) #Program should stop
        print(f"{'=' * 60}\n")
        
        return valid, invalid
    
    def get_list_count(self, url: str) -> int:
        """
        Get the number of movies in an IMDB list without scraping.
        
        Args:
            url: IMDB list URL
            
        Returns:
            Number of movies, or 0 if couldn't determine
        """
        try:
            from bs4 import BeautifulSoup
            import json
            import html as html_module
            
            response = self.scraper.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Try to get count from JSON-LD
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                if script.string:
                    try:
                        data = json.loads(script.string)
                        if '@type' in data and data.get('@type') == 'ItemList':
                            return len(data.get('itemListElement', []))
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            return 0
        except Exception as e:
            print(f"  Warning: Could not get count: {e}")
            return 0
    
    def scrape_multiple_lists(self, urls: List[str], output_file: str = "list/movie_list.txt") -> List[Dict[str, str]]:
        """
        Scrape multiple IMDB lists and combine them.
        
        Args:
            urls: List of IMDB URLs to scrape
            output_file: Output file path
            
        Returns:
            Combined list of movies
        """
        print("=== Scraping Movie Lists ===\n")
        
        all_movies = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n{'=' * 60}")
            print(f"List {i}/{len(urls)}: {url}")
            print(f"{'=' * 60}")
            
            # Get count first
            count = self.get_list_count(url)
            if count > 0:
                print(f"Expected movies: {count}\n")
            
            # Scrape the list
            movies = self.scraper.scrape_custom_list(url)
            
            if movies:
                print(f"✓ Scraped {len(movies)} movies from list {i}")
                
                # Add list metadata to each movie
                for movie in movies:
                    movie['source_list'] = str(i)
                    movie['source_url'] = url
                
                all_movies.extend(movies)
            else:
                print(f"✗ Failed to scrape list {i}")
        
        print(f"\n{'=' * 60}")
        print(f"Total movies scraped: {len(all_movies)}")
        print(f"{'=' * 60}\n")
        
        return all_movies
    
    def validate_and_clean_movies(self, movies: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Validate and clean the movie list.
        - Remove movies with unknown years
        - Remove movies with invalid names
        - Remove duplicates
        
        Args:
            movies: List of movie dictionaries
            
        Returns:
            Cleaned list of movies
        """
        print("=== Validating and Cleaning Movie List ===\n")
        
        initial_count = len(movies)
        
        # Step 1: Remove movies with invalid names
        valid_name_movies = []
        invalid_names = []
        
        for movie in movies:
            name = movie.get('name', '').strip()
            if name and len(name) > 0:
                valid_name_movies.append(movie)
            else:
                invalid_names.append(movie)
        
        print(f"1. Name validation:")
        print(f"   Valid: {len(valid_name_movies)}")
        print(f"   Invalid: {len(invalid_names)}")
        if invalid_names:
            for m in invalid_names[:5]:
                print(f"     - {m}")
            if len(invalid_names) > 5:
                print(f"     ... and {len(invalid_names) - 5} more")
        
        # Step 2: Remove movies with unknown years
        valid_year_movies = []
        unknown_years = []
        
        for movie in valid_name_movies:
            year = movie.get('year', 'Unknown')
            if year and year != 'Unknown' and year.isdigit() and len(year) == 4:
                valid_year_movies.append(movie)
            else:
                unknown_years.append(movie)
        
        print(f"\n2. Year validation:")
        print(f"   Valid: {len(valid_year_movies)}")
        print(f"   Unknown/Invalid: {len(unknown_years)}")
        if unknown_years:
            for m in unknown_years[:5]:
                print(f"     - {m.get('name')} ({m.get('year', 'N/A')})")
            if len(unknown_years) > 5:
                print(f"     ... and {len(unknown_years) - 5} more")
        
        # Step 3: Remove duplicates (by name + year)
        seen = set()
        unique_movies = []
        duplicates = []
        
        for movie in valid_year_movies:
            key = (movie['name'].lower(), movie['year'])
            if key not in seen:
                seen.add(key)
                unique_movies.append(movie)
            else:
                duplicates.append(movie)
        
        print(f"\n3. Duplicate removal:")
        print(f"   Unique: {len(unique_movies)}")
        print(f"   Duplicates: {len(duplicates)}")
        if duplicates:
            for m in duplicates[:5]:
                print(f"     - {m.get('name')} ({m.get('year')})")
            if len(duplicates) > 5:
                print(f"     ... and {len(duplicates) - 5} more")
        
        # Summary
        print(f"\n{'=' * 60}")
        print(f"Summary:")
        print(f"  Initial count: {initial_count}")
        print(f"  After validation: {len(unique_movies)}")
        print(f"  Removed: {initial_count - len(unique_movies)}")
        print(f"    - Invalid names: {len(invalid_names)}")
        print(f"    - Unknown years: {len(unknown_years)}")
        print(f"    - Duplicates: {len(duplicates)}")
        print(f"{'=' * 60}\n")
        
        return unique_movies
    
    def save_movies_to_file(self, movies: List[Dict[str, str]], output_file: str):
        """
        Save movies to file with list separators.
        
        Args:
            movies: List of movie dictionaries
            output_file: Output file path
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                current_list = None
                
                for movie in movies:
                    source_list = movie.get('source_list')
                    
                    # Add separator when switching to new list
                    if source_list != current_list:
                        if current_list is not None:
                            f.write(f"\n{'=' * 60}\n")
                        f.write(f"# List {source_list}: {movie.get('source_url', 'Unknown')}\n")
                        f.write(f"{'=' * 60}\n\n")
                        current_list = source_list
                    
                    # Write movie
                    f.write(f"{movie['name']} ({movie['year']})\n")
            
            print(f"✓ Saved {len(movies)} movies to {output_file}")
            
        except IOError as e:
            print(f"✗ Error saving file: {e}")
    
    def read_movies_from_file(self, input_file: str) -> List[Dict[str, str]]:
        """
        Read movies from file.
        
        Args:
            input_file: Input file path
            
        Returns:
            List of movie dictionaries with name and year
        """
        movies = []
        
        if not os.path.exists(input_file):
            print(f"✗ File not found: {input_file}")
            return movies
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines, comments, and separators
                    if not line or line.startswith('#') or line.startswith('='):
                        continue
                    
                    # Parse "Movie Name (Year)" format
                    if '(' in line and line.endswith(')'):
                        name = line[:line.rfind('(')].strip()
                        year = line[line.rfind('(')+1:-1].strip()
                        
                        if name and year:
                            movies.append({'name': name, 'year': year})
            
            print(f"✓ Read {len(movies)} movies from {input_file}")
            
        except IOError as e:
            print(f"✗ Error reading file: {e}")
        
        return movies
    
    def download_all_posters(self, movie_list_file: str = "list/movie_list.txt"):
        """
        Download posters for all movies in the list.
        
        Args:
            movie_list_file: Path to the movie list file
        """
        print("\n" + "=" * 60)
        print("DOWNLOADING MOVIE POSTERS")
        print("=" * 60 + "\n")
        
        # Read movies from file
        movies = self.read_movies_from_file(movie_list_file)
        
        if not movies:
            print("✗ No movies to download. Exiting.")
            return
        
        # Create directories
        poster_dir = "output/posters"
        list_dir = "list"
        os.makedirs(poster_dir, exist_ok=True)
        os.makedirs(list_dir, exist_ok=True)
        
        # Initialize poster fetcher
        fetcher = MoviePosterFetcher()
        
        # Track results
        successful = []
        failed = []
        skipped = []
        
        print(f"Total movies: {len(movies)}")
        print(f"Output directory: {poster_dir}\n")
        
        # Download each poster
        for i, movie in enumerate(movies, 1):
            name = movie['name']
            year = movie['year']
            
            # Create safe filename
            safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
            safe_name = safe_name.replace(' ', '_')
            filename = f"{safe_name}_{year}.jpg"
            filepath = os.path.join(poster_dir, filename)
            
            print(f"[{i}/{len(movies)}] {name} ({year})")
            
            # Check if already exists
            if os.path.exists(filepath):
                print(f"  ⊘ Skipped - already exists: {filename}")
                skipped.append(movie)
                continue
            
            # Download poster
            try:
                success = fetcher.download_poster(name, filepath)
                
                if success:
                    print(f"  ✓ Downloaded: {filename}")
                    successful.append(movie)
                else:
                    print(f"  ✗ Failed to download")
                    failed.append(movie)
                
                # Small delay to avoid rate limiting
                time.sleep(0.3)
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                failed.append(movie)
        
        # Save results to lists
        print("\n" + "=" * 60)
        print("SAVING RESULTS")
        print("=" * 60 + "\n")
        
        # Save successful downloads
        success_file = os.path.join(list_dir, "successful_downloads.txt")
        with open(success_file, 'w', encoding='utf-8') as f:
            f.write(f"# Successfully downloaded posters ({len(successful)} movies)\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for movie in successful:
                f.write(f"{movie['name']} ({movie['year']})\n")
        print(f"✓ Saved successful downloads: {success_file}")
        
        # Save failed downloads
        failed_file = os.path.join(list_dir, "failed_downloads.txt")
        with open(failed_file, 'w', encoding='utf-8') as f:
            f.write(f"# Failed poster downloads ({len(failed)} movies)\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for movie in failed:
                f.write(f"{movie['name']} ({movie['year']})\n")
        print(f"✓ Saved failed downloads: {failed_file}")
        
        # Summary
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Total movies: {len(movies)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print(f"Skipped (already exists): {len(skipped)}")
        print("=" * 60 + "\n")
    
    def process_all_posters(self):
        """
        Process all downloaded posters: detect title and blur using inpaint.
        """
        print("\n" + "=" * 60)
        print("PROCESSING MOVIE POSTERS")
        print("=" * 60 + "\n")
        
        poster_dir = "output/posters"
        output_dir = "output/blurred_posters"
        list_dir = "list"
        
        # Check if poster directory exists
        if not os.path.exists(poster_dir):
            print(f"✗ Poster directory not found: {poster_dir}")
            print("  Please download posters first using --download")
            return
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(list_dir, exist_ok=True)
        
        # Get all poster files
        poster_files = [f for f in os.listdir(poster_dir) if f.endswith('.jpg') or f.endswith('.png')]
        
        if not poster_files:
            print(f"✗ No posters found in {poster_dir}")
            return
        
        print(f"Total posters: {len(poster_files)}")
        print(f"Input directory: {poster_dir}")
        print(f"Output directory: {output_dir}\n")
        
        # Initialize detector and remover
        from detect_title import TitleDetector
        detector = TitleDetector()
        remover = TitleRemover()
        
        # Track results
        successful = []
        failed = []
        skipped = []
        
        # Process each poster
        for i, filename in enumerate(poster_files, 1):
            input_path = os.path.join(poster_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            print(f"[{i}/{len(poster_files)}] {filename}")
            
            # Check if already processed
            if os.path.exists(output_path):
                print(f"  ⊘ Skipped - already exists")
                skipped.append(filename)
                continue
            
            try:
                # Detect title region
                region = detector.find_title_region(input_path)
                
                if region is None:
                    print(f"  ⚠ No title detected, copying original")
                    # Copy original if no title detected
                    import shutil
                    shutil.copy2(input_path, output_path)
                    successful.append(filename)
                else:
                    x, y, w, h = region
                    print(f"  ✓ Title detected at ({x}, {y}) size {w}x{h}")
                    
                    # Apply inpaint to blur title
                    success = remover.remove_title_from_poster(input_path, output_path, 
                                                              method='inpaint', 
                                                              title_box=region)
                    
                    if success:
                        print(f"  ✓ Processed with inpaint")
                        successful.append(filename)
                    else:
                        print(f"  ✗ Failed to process")
                        failed.append(filename)
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                failed.append(filename)
        
        # Save results to lists
        print("\n" + "=" * 60)
        print("SAVING RESULTS")
        print("=" * 60 + "\n")
        
        # Save successful processing
        success_file = os.path.join(list_dir, "successful_processing.txt")
        with open(success_file, 'w', encoding='utf-8') as f:
            f.write(f"# Successfully processed posters ({len(successful)} files)\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for filename in successful:
                f.write(f"{filename}\n")
        print(f"✓ Saved successful processing: {success_file}")
        
        # Save failed processing
        failed_file = os.path.join(list_dir, "failed_processing.txt")
        with open(failed_file, 'w', encoding='utf-8') as f:
            f.write(f"# Failed poster processing ({len(failed)} files)\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for filename in failed:
                f.write(f"{filename}\n")
        print(f"✓ Saved failed processing: {failed_file}")
        
        # Summary
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total posters: {len(poster_files)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print(f"Skipped (already exists): {len(skipped)}")
        print("=" * 60 + "\n")
    
    def sample_for_game(self, movie_list_file: str = "list/movie_list.txt"):
        """
        Randomly sample up to 100 movies from each list for the game.
        
        Args:
            movie_list_file: Path to the movie list file
        """
        import random
        import shutil
        
        print("\n" + "=" * 60)
        print("SAMPLING POSTERS FOR GAME")
        print("=" * 60 + "\n")
        
        blurred_dir = "output/blurred_posters"
        game_dir = "game/posters"
        list_dir = "list"
        
        # Check if blurred poster directory exists
        if not os.path.exists(blurred_dir):
            print(f"✗ Blurred poster directory not found: {blurred_dir}")
            print("  Please process posters first using --process")
            return
        
        # Read movies from file to get list information
        if not os.path.exists(movie_list_file):
            print(f"✗ Movie list file not found: {movie_list_file}")
            return
        
        # Create directories
        os.makedirs(game_dir, exist_ok=True)
        os.makedirs(list_dir, exist_ok=True)
        
        # Parse movie list file and group by source list
        movies_by_list = {}
        current_list = None
        current_url = None
        
        try:
            with open(movie_list_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Detect list separator
                    if line.startswith('# List '):
                        # Extract list number and URL
                        parts = line.split(': ', 1)
                        list_part = parts[0].replace('# List ', '').strip()
                        current_url = parts[1] if len(parts) > 1 else 'Unknown'
                        current_list = list_part
                        movies_by_list[current_list] = {'url': current_url, 'movies': []}
                    elif line and not line.startswith('=') and not line.startswith('#'):
                        # Parse movie
                        if '(' in line and line.endswith(')'):
                            name = line[:line.rfind('(')].strip()
                            year = line[line.rfind('(')+1:-1].strip()
                            
                            if current_list and name and year:
                                movies_by_list[current_list]['movies'].append({
                                    'name': name,
                                    'year': year
                                })
        except IOError as e:
            print(f"✗ Error reading file: {e}")
            return
        
        if not movies_by_list:
            print("✗ No lists found in movie file")
            return
        
        print(f"Found {len(movies_by_list)} list(s)\n")
        
        # Sample from each list
        total_sampled = 0
        
        for list_id, list_data in movies_by_list.items():
            movies = list_data['movies']
            url = list_data['url']
            
            print(f"\n{'=' * 60}")
            print(f"List {list_id}: {url}")
            print(f"{'=' * 60}")
            print(f"Total movies in list: {len(movies)}")
            
            # Filter movies that have blurred posters
            available_movies = []
            for movie in movies:
                name = movie['name']
                year = movie['year']
                safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
                safe_name = safe_name.replace(' ', '_')
                filename = f"{safe_name}_{year}.jpg"
                filepath = os.path.join(blurred_dir, filename)
                
                if os.path.exists(filepath):
                    available_movies.append((movie, filename, filepath))
            
            print(f"Available processed posters: {len(available_movies)}")
            
            if not available_movies:
                print("✗ No processed posters found for this list")
                continue
            
            # Sample up to 100
            sample_size = min(100, len(available_movies))
            sampled = random.sample(available_movies, sample_size)
            
            print(f"Sampling: {sample_size} movies")
            
            # Copy sampled posters to game folder
            copied = []
            for movie, filename, source_path in sampled:
                dest_path = os.path.join(game_dir, filename)
                
                # Copy if not already exists
                if not os.path.exists(dest_path):
                    try:
                        shutil.copy2(source_path, dest_path)
                        copied.append(movie)
                    except Exception as e:
                        print(f"  ✗ Error copying {filename}: {e}")
                else:
                    copied.append(movie)  # Already exists, count as copied
            
            print(f"✓ Copied {len(copied)} posters to game folder")
            
            # Save sampling list
            list_filename = f"sampled_list_{list_id}.txt"
            list_filepath = os.path.join(list_dir, list_filename)
            
            with open(list_filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Sampled movies from List {list_id}\n")
                f.write(f"# Source: {url}\n")
                f.write(f"# Total available: {len(available_movies)}\n")
                f.write(f"# Sampled: {len(copied)}\n")
                f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for movie in copied:
                    f.write(f"{movie['name']} ({movie['year']})\n")
            
            print(f"✓ Saved sampling list: {list_filepath}")
            total_sampled += len(copied)
        
        # Summary
        print("\n" + "=" * 60)
        print("SAMPLING SUMMARY")
        print("=" * 60)
        print(f"Lists processed: {len(movies_by_list)}")
        print(f"Total sampled: {total_sampled}")
        print(f"Game folder: {game_dir}")
        print("=" * 60 + "\n")
    
    def prepare_posters(self, 
                       urls: List[str], 
                       output_file: str = "list/movie_list.txt",
                       force_refresh: bool = False):
        """
        Complete pipeline: validate URLs, scrape, validate data, save.
        
        Args:
            urls: List of IMDB URLs to scrape
            output_file: Output file for movie list
            force_refresh: Force fresh scrape (ignore cache)
        """
        print("\n" + "=" * 60)
        print("FILMSTER - POSTER PREPARATION PIPELINE")
        print("=" * 60 + "\n")
        
        # Step 1: Validate URLs
        valid_urls, invalid_urls = self.validate_urls(urls)
        
        if not valid_urls:
            print("✗ No valid URLs to process. Exiting.")
            return False
        
        if invalid_urls:
            response = input(f"\nContinue with {len(valid_urls)} valid URLs? (y/n): ").lower()
            if response != 'y':
                print("Aborted by user.")
                return False
        
        # Step 2: Scrape all lists
        if force_refresh:
            print("\nForce refresh enabled - ignoring cache\n")
        
        all_movies = self.scrape_multiple_lists(valid_urls, output_file)
        
        if not all_movies:
            print("✗ No movies scraped. Exiting.")
            return False
        
        # Step 3: Validate and clean
        clean_movies = self.validate_and_clean_movies(all_movies)
        
        if not clean_movies:
            print("✗ No valid movies after cleaning. Exiting.")
            return False
        
        # Step 4: Save to file
        self.save_movies_to_file(clean_movies, output_file)
        
        print("\n" + "=" * 60)
        print("✓ PREPARATION COMPLETE")
        print("=" * 60)
        print(f"\nMovie list saved to: {output_file}")
        print(f"Total movies: {len(clean_movies)}")
        print(f"Ready to download posters!")
        print("\nNext steps:")
        print(f"  python prepare_posters.py --download")
        print("=" * 60 + "\n")
        
        return True


# Predefined IMDB list URLs
IMDB_LISTS = {
    'top250': 'https://www.imdb.com/chart/top/',
    'popular': 'https://www.imdb.com/chart/moviemeter/',
    'top250_tv': 'https://www.imdb.com/chart/toptv/',
}


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Prepare movie posters for Filmster game',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape IMDB Top 250
  python prepare_posters.py
  
  # Scrape multiple predefined lists
  python prepare_posters.py --lists top250 popular
  
  # Scrape custom URLs
  python prepare_posters.py --urls "https://www.imdb.com/chart/top/" "https://www.imdb.com/chart/moviemeter/"
  
  # Force refresh (ignore cache)
  python prepare_posters.py --force-refresh
  
  # Custom output file
  python prepare_posters.py --output my_movies.txt
  
  # Download posters from default movie list
  python prepare_posters.py --download
  
  # Download posters from custom movie list
  python prepare_posters.py --download my_movies.txt
  
  # Process downloaded posters (detect and blur titles)
  python prepare_posters.py --process
  
  # Sample up to 100 movies per list for game
  python prepare_posters.py --sample
  
  # Sample from custom movie list
  python prepare_posters.py --sample my_movies.txt
        """
    )
    
    parser.add_argument('--lists', nargs='+', choices=list(IMDB_LISTS.keys()),
                       help='Predefined IMDB lists to scrape')
    parser.add_argument('--urls', nargs='+',
                       help='Custom IMDB URLs to scrape')
    parser.add_argument('--output', default='list/movie_list.txt',
                       help='Output file for movie list (default: list/movie_list.txt)')
    parser.add_argument('--force-refresh', '-f', action='store_true',
                       help='Force fresh scrape (ignore cache)')
    parser.add_argument('--download', nargs='?', const='list/movie_list.txt', metavar='MOVIE_LIST',
                       help='Download posters from movie list file (default: list/movie_list.txt)')
    parser.add_argument('--process', action='store_true',
                       help='Process downloaded posters (detect and blur titles)')
    parser.add_argument('--sample', nargs='?', const='list/movie_list.txt', metavar='MOVIE_LIST',
                       help='Sample up to 100 movies per list for game (default: list/movie_list.txt)')
    
    args = parser.parse_args()
    
    # Determine which URLs to use
    urls = []
    
    if args.urls:
        urls = args.urls
    elif args.lists:
        urls = [IMDB_LISTS[list_name] for list_name in args.lists]
    else:
        # Default to Top 250
        urls = [IMDB_LISTS['top250']]
        print("No lists specified, using default: IMDB Top 250\n")
    
    # Create preparer
    preparer = PosterPreparer(use_cache=not args.force_refresh)
    
    # Handle sample mode
    if args.sample:
        preparer.sample_for_game(args.sample)
        return
    
    # Handle process mode
    if args.process:
        preparer.process_all_posters()
        return
    
    # Handle download mode
    if args.download:
        preparer.download_all_posters(args.download)
        return
    
    # Otherwise, run scraping pipeline
    success = preparer.prepare_posters(urls, args.output, args.force_refresh)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
