"""
Title Removal from Movie Posters
Blurs or blacks out detected text regions in movie posters.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import os
from detect_title import TitleDetector


class TitleRemover:
    """Removes or blurs title text from movie posters."""
    
    def __init__(self):
        """Initialize the title remover."""
        self.detector = TitleDetector()
    
    def blur_region(self, image: np.ndarray, box: Tuple[int, int, int, int], 
                   blur_strength: int = 50) -> np.ndarray:
        """
        Apply Gaussian blur to a specific region of the image.
        
        Args:
            image: Input image (numpy array)
            box: Bounding box (x, y, width, height)
            blur_strength: Strength of blur (must be odd number, higher = more blur)
            
        Returns:
            Image with blurred region
        """
        x, y, w, h = box
        
        # Ensure blur strength is odd
        if blur_strength % 2 == 0:
            blur_strength += 1
        
        # Extract region
        height, width = image.shape[:2]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(width, x + w)
        y2 = min(height, y + h)
        
        # Create a copy
        result = image.copy()
        
        # Apply Gaussian blur to the region
        region = result[y1:y2, x1:x2]
        blurred_region = cv2.GaussianBlur(region, (blur_strength, blur_strength), 0)
        result[y1:y2, x1:x2] = blurred_region
        
        return result
    
    def black_out_region(self, image: np.ndarray, box: Tuple[int, int, int, int],
                        color: Tuple[int, int, int] = (0, 0, 0)) -> np.ndarray:
        """
        Fill a specific region with a solid color (default black).
        
        Args:
            image: Input image (numpy array)
            box: Bounding box (x, y, width, height)
            color: BGR color to fill with (default black)
            
        Returns:
            Image with blacked out region
        """
        x, y, w, h = box
        
        # Create a copy
        result = image.copy()
        
        # Fill rectangle
        cv2.rectangle(result, (x, y), (x + w, y + h), color, -1)
        
        return result
    
    def inpaint_region(self, image: np.ndarray, box: Tuple[int, int, int, int],
                       inpaint_radius: int = 3) -> np.ndarray:
        """
        Use inpainting to fill the region naturally based on surrounding pixels.
        
        Args:
            image: Input image (numpy array)
            box: Bounding box (x, y, width, height)
            inpaint_radius: Radius of inpainting neighborhood
            
        Returns:
            Image with inpainted region
        """
        x, y, w, h = box
        
        # Create mask for the region to inpaint
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        
        # Apply inpainting
        result = cv2.inpaint(image, mask, inpaint_radius, cv2.INPAINT_TELEA)
        
        return result
    
    def remove_title_from_poster(self, input_path: str, output_path: str,
                                 method: str = 'blur', movie_title: Optional[str] = None,
                                 blur_strength: int = 50,
                                 title_box: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        Remove title from a movie poster and save the result.
        
        Args:
            input_path: Path to input poster image
            output_path: Path to save the output image
            method: Removal method - 'blur', 'black', or 'inpaint'
            movie_title: Optional movie title for better detection
            blur_strength: Blur strength for 'blur' method (must be odd)
            title_box: Optional pre-detected title box. If None, will auto-detect.
            
        Returns:
            True if successful, False otherwise
        """
        # Load image
        image = cv2.imread(input_path)
        if image is None:
            print(f"Error: Could not load image from {input_path}")
            return False
        
        # Detect title region if not provided
        if title_box is None:
            print("Detecting title region...")
            title_box = self.detector.find_title_region(input_path, movie_title)
            
            if title_box is None:
                print("Error: Could not detect title region")
                return False
        
        print(f"Removing title using method: {method}")
        x, y, w, h = title_box
        print(f"  Region: ({x}, {y}) - Size: {w}x{h}")
        
        # Apply removal method
        if method == 'blur':
            result = self.blur_region(image, title_box, blur_strength)
        elif method == 'black':
            result = self.black_out_region(image, title_box)
        elif method == 'inpaint':
            result = self.inpaint_region(image, title_box)
        else:
            print(f"Error: Unknown method '{method}'. Use 'blur', 'black', or 'inpaint'")
            return False
        
        # Save result
        cv2.imwrite(output_path, result)
        print(f"Saved result to {output_path}")
        
        return True
    
    def batch_process_posters(self, poster_dir: str, output_dir: str,
                             method: str = 'blur', blur_strength: int = 50):
        """
        Process multiple posters in a directory.
        
        Args:
            poster_dir: Directory containing poster images
            output_dir: Directory to save processed images
            method: Removal method - 'blur', 'black', or 'inpaint'
            blur_strength: Blur strength for 'blur' method
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Process all images
        image_extensions = ['.jpg', '.jpeg', '.png']
        processed = 0
        failed = 0
        
        for filename in os.listdir(poster_dir):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                input_path = os.path.join(poster_dir, filename)
                
                # Create output filename
                name, ext = os.path.splitext(filename)
                output_filename = f"{name}_blurred{ext}"
                output_path = os.path.join(output_dir, output_filename)
                
                print(f"\nProcessing: {filename}")
                
                # Extract movie title from filename (assumes format: "Movie Name (Year).jpg")
                movie_title = name.split('(')[0].strip() if '(' in name else None
                
                success = self.remove_title_from_poster(input_path, output_path, 
                                                       method, movie_title, blur_strength)
                
                if success:
                    processed += 1
                else:
                    failed += 1
        
        print(f"\n=== Batch Processing Complete ===")
        print(f"Processed: {processed}")
        print(f"Failed: {failed}")
        print(f"Total: {processed + failed}")


def remove_title_from_poster(input_path: str, output_path: str,
                             method: str = 'blur', movie_title: Optional[str] = None) -> bool:
    """
    Simple function to remove title from a movie poster.
    
    Args:
        input_path: Path to input poster image
        output_path: Path to save the output image
        method: Removal method - 'blur', 'black', or 'inpaint'
        movie_title: Optional movie title for better detection
        
    Returns:
        True if successful, False otherwise
    """
    remover = TitleRemover()
    return remover.remove_title_from_poster(input_path, output_path, method, movie_title)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python remove_title.py <input_image> <output_image> [method] [movie_title]")
        print("  method: 'blur' (default), 'black', or 'inpaint'")
        print("Example: python remove_title.py poster.jpg poster_blurred.jpg blur \"The Matrix\"")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    method = sys.argv[3] if len(sys.argv) > 3 else 'blur'
    movie_title = sys.argv[4] if len(sys.argv) > 4 else None
    
    remover = TitleRemover()
    success = remover.remove_title_from_poster(input_path, output_path, method, movie_title)
    
    if success:
        print("\n✓ Title removed successfully!")
    else:
        print("\n✗ Failed to remove title")
        sys.exit(1)
