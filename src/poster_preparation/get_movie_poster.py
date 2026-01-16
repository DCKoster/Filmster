"""
Movie Poster Fetcher using TMDb API
Gets poster images for movies by name - posters only, no backdrops.
"""
import sys
import requests
import os
from typing import Optional, Dict
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class MoviePosterFetcher:
    """Fetches movie poster URLs from The Movie Database (TMDb) API."""
    
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the fetcher with TMDb API key.
        
        Args:
            api_key: TMDb API key. If None, tries to read from TMDB_API_KEY env variable.
        """
        self.api_key = api_key or os.getenv('TMDB_API_KEY')
        if not self.api_key:
            raise ValueError(
                "TMDb API key is required. Either pass it to __init__ or set TMDB_API_KEY environment variable.\n"
                "Get your free API key at: https://www.themoviedb.org/settings/api"
            )
    
    def search_movie(self, movie_name: str) -> Optional[Dict]:
        """
        Search for a movie by name and return the first match.
        
        Args:
            movie_name: Name of the movie to search for
            
        Returns:
            Dictionary with movie data if found, None otherwise
        """
        endpoint = f"{self.BASE_URL}/search/movie"
        params = {
            'api_key': self.api_key,
            'query': movie_name,
            'language': 'en-US',
            'page': 1
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['results']:
                return data['results'][0]  # Return the first match
            return None
            
        except requests.RequestException as e:
            print(f"Error searching for movie: {e}")
            return None
    
    def get_poster_url(self, movie_name: str, size: str = "w500") -> Optional[str]:
        """
        Get the poster URL for a movie by name.
        
        Args:
            movie_name: Name of the movie
            size: Poster size. Options: w92, w154, w185, w342, w500, w780, original
            
        Returns:
            Full URL to the poster image, or None if not found
        """
        movie = self.search_movie(movie_name)
        
        if not movie:
            print(f"Movie '{movie_name}' not found")
            return None
        
        poster_path = movie.get('poster_path')
        
        if not poster_path:
            print(f"No poster available for '{movie_name}'")
            return None
        
        poster_url = f"{self.IMAGE_BASE_URL}{size}{poster_path}"
        return poster_url
    
    def download_poster(self, movie_name: str, output_path: str = "poster.jpg", size: str = "w500") -> bool:
        """
        Download a movie poster to a file.
        
        Args:
            movie_name: Name of the movie
            output_path: Path where the poster should be saved
            size: Poster size. Options: w92, w154, w185, w342, w500, w780, original
            
        Returns:
            True if successful, False otherwise
        """
        poster_url = self.get_poster_url(movie_name, size)
        
        if not poster_url:
            return False
        
        try:
            response = requests.get(poster_url, timeout=10)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Poster saved to: {output_path}")
            return True
            
        except requests.RequestException as e:
            print(f"Error downloading poster: {e}")
            return False


def get_movie_poster(movie_name: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Simple function to get a movie poster URL.
    
    Args:
        movie_name: Name of the movie
        api_key: TMDb API key (optional if TMDB_API_KEY env variable is set)
        
    Returns:
        URL to the movie poster, or None if not found
    """
    fetcher = MoviePosterFetcher(api_key)
    return fetcher.get_poster_url(movie_name)


def download_movie_poster(movie_name: str) -> bool:
    """
    This script will be run to downlaod a movie poster given the movie name.
    Args:
        movie_name: Name of the movie
    Returns:
        True if successful, False otherwise
    """  
        
    try:
        fetcher = MoviePosterFetcher()
        poster_url = fetcher.get_poster_url(movie_name)
        
        if poster_url:
            print(f"Movie: {movie_name}")
            print(f"Poster URL: {poster_url}")
            filename = f"output/{movie_name.replace(' ', '_')}_poster.jpg"
            fetcher.download_poster(movie_name, filename)
        else:
            print(f"Could not find poster for: {movie_name}")
            return False
        return True
            
    except ValueError as e:
        print(f"Error: {e}")
        return False
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_movie_poster.py 'Movie Name'")
        sys.exit(1)
    
    movie_name = " ".join(sys.argv[1:])
    download_movie_poster(movie_name)