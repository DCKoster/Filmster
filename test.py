import os
import requests

TMDB_API_KEY = os.environ["TMDB_API_KEY"]  # or hardcode temporarily

BASE = "https://api.themoviedb.org/3"

def tmdb_get(path: str, **params):
    r = requests.get(f"{BASE}{path}", params={"api_key": TMDB_API_KEY, **params}, timeout=30)
    r.raise_for_status()
    return r.json()

def find_movie_id(title: str, year: int | None = None) -> int:
    data = tmdb_get("/search/movie", query=title, year=year)  # year optional
    results = data.get("results", [])
    if not results:
        raise ValueError("No results")
    return results[0]["id"]  # simple: take best match

def get_backdrop_url(movie_id: int, size: str = "w1280") -> str:
    cfg = tmdb_get("/configuration")
    secure_base = cfg["images"]["secure_base_url"]

    imgs = tmdb_get(f"/movie/{movie_id}/images")
    backdrops = imgs.get("backdrops", [])
    if not backdrops:
        raise ValueError("No backdrops for this movie")

    file_path = backdrops[0]["file_path"]
    return f"{secure_base}{size}{file_path}"

mid = find_movie_id("Inception", year=2010)
print("movie_id:", mid)
print("backdrop:", get_backdrop_url(mid))
