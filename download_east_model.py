"""
Download EAST text detection model
"""

import requests
import os

EAST_MODEL_URL = "https://github.com/oyyd/frozen_east_text_detection.pb/raw/master/frozen_east_text_detection.pb"
MODEL_PATH = "frozen_east_text_detection.pb"

def download_east_model():
    """Download the EAST text detection model if it doesn't exist."""
    if os.path.exists(MODEL_PATH):
        print(f"EAST model already exists at {MODEL_PATH}")
        return True
    
    print("Downloading EAST text detection model...")
    print(f"URL: {EAST_MODEL_URL}")
    print("This may take a minute (file is ~100MB)...")
    
    try:
        response = requests.get(EAST_MODEL_URL, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(MODEL_PATH, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end='')
        
        print(f"\n✓ Model downloaded successfully to {MODEL_PATH}")
        return True
        
    except Exception as e:
        print(f"\n✗ Error downloading model: {e}")
        print("\nYou can manually download from:")
        print(EAST_MODEL_URL)
        return False

if __name__ == "__main__":
    download_east_model()
