"""
Movie Name Scraper for IMDB Lists
Scrapes movie names from IMDB charts like Top 250, Most Popular, etc.
Enriches data with TMDb API for accurate years and titles.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
import time
import json
import html
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class IMDBScraper:
    """Scrapes movie names from IMDB list pages and enriches with TMDb data."""
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    CACHE_FILE = "movie_cache.json"
    
    def __init__(self, tmdb_api_key: Optional[str] = None, enrich_with_tmdb: bool = True, use_cache: bool = True):
        """
        Initialize the scraper.
        
        Args:
            tmdb_api_key: TMDb API key for enriching data. If None, uses TMDB_API_KEY env variable.
            enrich_with_tmdb: If True, enriches movie data with TMDb API for accurate years and titles.
            use_cache: If True, uses cached data if available to avoid API rate limits.
        """
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.enrich_with_tmdb = enrich_with_tmdb
        self.use_cache = use_cache
        self.tmdb_api_key = tmdb_api_key or os.getenv('TMDB_API_KEY')
        
        if self.enrich_with_tmdb and not self.tmdb_api_key:
            print("Warning: TMDb API key not found. Years may be incomplete.")
            print("Set TMDB_API_KEY environment variable for complete data.")
            self.enrich_with_tmdb = False
    
    def _load_cache(self) -> Optional[Dict]:
        """Load cached movie data from file."""
        if not self.use_cache or not os.path.exists(self.CACHE_FILE):
            return None
        
        try:
            with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                print(f"Loaded {len(cache.get('movies', []))} movies from cache ({self.CACHE_FILE})")
                print("Run with --force-refresh to scrape fresh data.")
                return cache
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load cache: {e}")
            return None
    
    def _save_cache(self, movies: List[Dict[str, str]]):
        """Save movie data to cache file."""
        try:
            cache = {
                'movies': movies,
                'cached_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'count': len(movies)
            }
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            print(f"Cached {len(movies)} movies to {self.CACHE_FILE}")
        except IOError as e:
            print(f"Warning: Could not save cache: {e}")
    
    def scrape_top_250(self) -> List[Dict[str, str]]:
        """
        Scrape movie names and years from IMDB Top 250 list.
        
        Returns:
            List of dictionaries with 'name', 'original_title', and 'year' keys
        """
        # Try to load from cache first
        cached_data = self._load_cache()
        if cached_data:
            return cached_data['movies']
        
        url = "https://www.imdb.com/chart/top/"
        movies = self._scrape_chart(url)
        
        # Save to cache
        if movies and self.use_cache:
            self._save_cache(movies)
        
        return movies
    
    def scrape_most_popular(self) -> List[Dict[str, str]]:
        """
        Scrape movie names and years from IMDB Most Popular Movies list.
        
        Returns:
            List of dictionaries with 'name', 'original_title', and 'year' keys
        """
        url = "https://www.imdb.com/chart/moviemeter/"
        return self._scrape_chart(url)
    
    def _enrich_with_tmdb(self, movie_name: str, imdb_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Enrich movie data using TMDb API.
        
        Args:
            movie_name: Name of the movie to search for
            imdb_id: IMDB ID (e.g., 'tt0111161') for exact matching
            
        Returns:
            Dictionary with 'title', 'original_title', and 'year' or None if not found
        """
        if not self.enrich_with_tmdb or not self.tmdb_api_key:
            return None
        
        try:
            movie = None
            
            # Method 1: Use IMDB ID for exact match (most reliable)
            if imdb_id:
                find_url = f"https://api.themoviedb.org/3/find/{imdb_id}"
                params = {
                    'api_key': self.tmdb_api_key,
                    'external_source': 'imdb_id'
                }
                
                response = self.session.get(find_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get('movie_results'):
                    movie = data['movie_results'][0]
            
            # Method 2: Fallback to search by name
            if not movie:
                search_url = "https://api.themoviedb.org/3/search/movie"
                params = {
                    'api_key': self.tmdb_api_key,
                    'query': movie_name,
                    'language': 'en-US',
                    'page': 1
                }
                
                response = self.session.get(search_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data['results']:
                    movie = data['results'][0]  # Get the first match
            
            if movie:
                release_date = movie.get('release_date', '')
                year = release_date[:4] if release_date else None
                
                return {
                    'title': movie.get('title', movie_name),  # English title
                    'original_title': movie.get('original_title', movie_name),  # Original title
                    'year': year
                }
            
            return None
            
        except requests.RequestException as e:
            print(f"  Warning: Could not enrich '{movie_name}': {e}")
            return None
    
    def _scrape_chart(self, url: str) -> List[Dict[str, str]]:
        """
        Generic method to scrape IMDB chart pages with pagination support.
        
        Args:
            url: URL of the IMDB chart page
            
        Returns:
            List of dictionaries with 'name' and 'year' keys
        """
        all_movies = []
        seen_ids = set()  # Track IMDB IDs to prevent duplicates
        page = 1
        max_pages = 20  # Safety limit to prevent infinite loops
        
        while page <= max_pages:
            # Add page parameter for custom lists
            page_url = url
            if page > 1:
                separator = '&' if '?' in url else '?'
                page_url = f"{url}{separator}page={page}"
            
            print(f"  Scraping page {page}...")
            
            try:
                response = self.session.get(page_url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                movies = []
                
                # Extract movie names and IMDB IDs from JSON-LD data
                json_scripts = soup.find_all('script', type='application/ld+json')
                movie_data = []  # List of {'name': ..., 'imdb_id': ...}
                
                for script in json_scripts:
                    if script.string:
                        try:
                            data = json.loads(script.string)
                            if '@type' in data and data.get('@type') == 'ItemList':
                                items = data.get('itemListElement', [])
                                for item in items:
                                    if 'item' in item and 'name' in item['item']:
                                        # Decode HTML entities like &apos; to '
                                        name = html.unescape(item['item']['name'])
                                        
                                        # Extract IMDB ID from URL
                                        imdb_id = None
                                        item_url = item['item'].get('url', '')
                                        imdb_match = re.search(r'/title/(tt\d+)/', item_url)
                                        if imdb_match:
                                            imdb_id = imdb_match.group(1)
                                        
                                        movie_data.append({'name': name, 'imdb_id': imdb_id})
                                break
                        except (json.JSONDecodeError, KeyError):
                            continue
                
                # If no movies found on this page, we've reached the end
                if not movie_data:
                    if page == 1:
                        # Try fallback HTML scraping for first page
                        movie_data = self._fallback_html_scrape(soup)
                    if not movie_data:
                        print(f"    No movies found on page {page}, stopping pagination")
                        break
                
                # Get years from HTML - try both metadata and image alt text
                list_items = soup.find_all('li', class_='ipc-metadata-list-summary-item')
                
                # Create a mapping of years from available list items
                year_map = {}
                for idx, list_item in enumerate(list_items):
                    year = None
                    
                    # Method 1: Try metadata items
                    metadata_items = list_item.find_all('span', class_='cli-title-metadata-item')
                    if metadata_items:
                        year_text = metadata_items[0].get_text(strip=True)
                        if year_text.isdigit() and len(year_text) == 4:
                            year = year_text
                    
                    # Method 2: Try extracting from image alt text as fallback
                    if not year:
                        img = list_item.find('img')
                        if img and img.get('alt'):
                            alt_text = img.get('alt')
                            year_match = re.search(r'\((\d{4})\)', alt_text)
                            if year_match:
                                year = year_match.group(1)
                    
                    if year:
                        year_map[idx] = year
                
                # Combine movie names with years and IMDB IDs, checking for duplicates
                new_movies_count = 0
                for i, movie_info in enumerate(movie_data):
                    imdb_id = movie_info.get('imdb_id')
                    
                    # Skip if we've already seen this movie
                    if imdb_id and imdb_id in seen_ids:
                        continue
                    
                    year = year_map.get(i, 'Unknown')
                    movies.append({
                        'name': movie_info['name'],
                        'year': year,
                        'original_title': movie_info['name'],
                        'imdb_id': imdb_id
                    })
                    
                    if imdb_id:
                        seen_ids.add(imdb_id)
                    new_movies_count += 1
                
                if not movies:
                    print(f"    No new movies found on page {page}, stopping pagination")
                    break
                
                all_movies.extend(movies)
                print(f"    Found {new_movies_count} new movies on page {page} (total: {len(all_movies)})")
                
                # If we got no new movies, we're seeing duplicates - stop
                if new_movies_count == 0:
                    print(f"    All movies on page {page} were duplicates, stopping pagination")
                    break
                
                # Check if there's a next page
                # Look for pagination - if no "next" button or we got less than expected, stop
                next_button = soup.find('button', {'aria-label': 'Next'})
                if not next_button or next_button.get('disabled'):
                    print(f"    No next page button found, stopping pagination")
                    break
                
                page += 1
                time.sleep(0.5)  # Be nice to IMDB servers
                
            except requests.RequestException as e:
                print(f"  Error scraping page {page}: {e}")
                break
        
        if not all_movies:
            return []
        
        # Enrich with TMDb data if enabled
        if self.enrich_with_tmdb:
            print(f"Enriching {len(all_movies)} movies with TMDb API (this may take a minute)...")
            all_movies = self._enrich_movies_batch(all_movies)
        
        print(f"Successfully scraped {len(all_movies)} movies from {url}")
        return all_movies
    
    def _fallback_html_scrape(self, soup) -> List[Dict]:
        """Fallback HTML scraping when JSON-LD is not available."""
        movie_data = []
        title_elements = soup.find_all('h3', class_='ipc-title__text')
        
        for title_elem in title_elements:
            text = title_elem.get_text(strip=True)
            if text and not any(skip in text.lower() for skip in ['imdb', 'chart', 'top rated']):
                # Remove leading numbers like "1. " from title
                text = re.sub(r'^\d+\.\s*', '', text)
                movie_data.append({'name': text, 'imdb_id': None})
        
        return movie_data
    
    def _enrich_movies_batch(self, movies: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Enrich a batch of movies with TMDb data."""
        enriched_movies = []
        failed_count = 0
        
        for i, movie in enumerate(movies):
            # Show progress
            if (i + 1) % 25 == 0:
                print(f"  Processed {i + 1}/{len(movies)} movies...")
            
            try:
                tmdb_data = self._enrich_with_tmdb(movie['name'], movie.get('imdb_id'))
                
                if tmdb_data:
                    original_title = tmdb_data['original_title']
                    english_title = tmdb_data['title']
                    
                    # Use English title for non-Latin scripts (Japanese, Korean, Chinese, etc.)
                    # Check if original title contains non-Latin characters
                    has_non_latin = any(ord(c) > 0x024F for c in original_title)
                    
                    # Use English title if original has non-Latin chars, otherwise use original
                    display_title = english_title if has_non_latin else original_title
                    
                    enriched_movies.append({
                        'name': display_title,
                        'original_title': original_title,
                        'english_title': english_title,
                        'year': tmdb_data['year'] or movie['year'],
                        'imdb_id': movie.get('imdb_id')
                    })
                else:
                    # Keep original if TMDb lookup failed
                    enriched_movies.append(movie)
                    failed_count += 1
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print(f"\nInterrupted! Processed {i + 1}/{len(movies)} movies.")
                print(f"Saving partial results...")
                return enriched_movies + movies[i+1:]  # Keep remaining unenriched
            except Exception as e:
                print(f"  Error processing '{movie['name']}': {e}")
                enriched_movies.append(movie)
                failed_count += 1
        
        print(f"Enrichment complete! Failed to enrich {failed_count} movies.")
        return enriched_movies
    
    def scrape_custom_list(self, url: str) -> List[Dict[str, str]]:
        """
        Scrape movie names and years from any IMDB list URL.
        
        Args:
            url: URL of the IMDB list
            
        Returns:
            List of dictionaries with 'name' and 'year' keys
        """
        return self._scrape_chart(url)
    
    def save_to_file(self, movies: List[Dict[str, str]], filename: str = "list/movie_list.txt"):
        """
        Save movie names and years to a text file.
        
        Args:
            movies: List of dictionaries with 'name' and 'year' keys
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for movie in movies:
                    f.write(f"{movie['name']} ({movie['year']})\n")
            print(f"Saved {len(movies)} movies to {filename}")
        except IOError as e:
            print(f"Error saving to file: {e}")


def get_top_250_movies() -> List[Dict[str, str]]:
    """
    Simple function to get IMDB Top 250 movie names and years.
    
    Returns:
        List of dictionaries with 'name' and 'year' keys
    """
    scraper = IMDBScraper()
    return scraper.scrape_top_250()


if __name__ == "__main__":
    import sys
    
    # Check for force refresh flag
    force_refresh = '--force-refresh' in sys.argv or '-f' in sys.argv
    auto_save = '--auto-save' in sys.argv or '-a' in sys.argv
    
    # Remove flags from arguments
    args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    
    scraper = IMDBScraper(use_cache=not force_refresh)
    
    # Check if a custom URL was provided
    if args:
        url = args[0]
        print(f"Scraping movies from: {url}")
        movies = scraper.scrape_custom_list(url)
    else:
        # Default to Top 250
        print("Scraping IMDB Top 250...")
        if force_refresh:
            print("Force refresh enabled - will scrape fresh data from web")
        movies = scraper.scrape_top_250()
    
    if movies:
        print(f"\nFound {len(movies)} movies:")
        print("\nFirst 10 movies:")
        for i, movie in enumerate(movies[:10], 1):
            print(f"{i}. {movie['name']} ({movie['year']})")
        
        # Auto-save or ask user
        if auto_save:
            filename = "list/movie_list.txt"
            scraper.save_to_file(movies, filename)
        else:
            # Ask if user wants to save to file
            save = input("\nSave to file? (y/n): ").lower().strip()
            if save == 'y':
                filename = input("Enter filename (default: list/movie_list.txt): ").strip()
                if not filename:
                    filename = "list/movie_list.txt"
                scraper.save_to_file(movies, filename)
    else:
        print("No movies found. The page structure may have changed.")