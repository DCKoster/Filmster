"""
Title Detection in Movie Posters
Uses CRAFT text detector via EasyOCR to find text regions in movie posters.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import os


class TitleDetector:
    """Detects text regions in movie posters using CRAFT text detector (via EasyOCR)."""
    
    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize the text detector.
        
        Args:
            confidence_threshold: Minimum confidence for text detection (0-1)
        """
        self.confidence_threshold = confidence_threshold
        self.detector = None
        
        try:
            import easyocr
            # EasyOCR uses CRAFT internally for detection
            self.detector = easyocr.Reader(['en'], gpu=False, verbose=False)
            print("✓ CRAFT detector loaded successfully")
        except ImportError:
            print("Warning: EasyOCR not installed. Install with: pip install easyocr")
        except Exception as e:
            print(f"Warning: Could not load CRAFT detector: {e}")
    
    def detect_text_regions(self, image_path: str, min_size: int = 50) -> List[Tuple[int, int, int, int]]:
        """
        Detect text regions in an image using CRAFT.
        
        Args:
            image_path: Path to the image file
            min_size: Minimum width or height for detected regions (filters small text)
            
        Returns:
            List of bounding boxes as (x, y, width, height) tuples
        """
        if not self.detector:
            print("Error: CRAFT detector not initialized.")
            return self._fallback_detection(image_path, min_size)
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image from {image_path}")
            return []
        
        orig_height, orig_width = image.shape[:2]
        
        # Run CRAFT detection via EasyOCR
        # Returns (horizontal_list, free_list)
        results = self.detector.detect(image)
        
        boxes = []
        if results and len(results) > 0:
            # results[0] contains horizontal text regions as [xmin, xmax, ymin, ymax]
            horizontal_list = results[0]
            
            # horizontal_list is [[boxes...]], need to unwrap
            if horizontal_list and len(horizontal_list) > 0:
                if isinstance(horizontal_list[0], list):
                    horizontal_list = horizontal_list[0]
                    
                for box in horizontal_list:
                    # box is [xmin, xmax, ymin, ymax] but may contain np.int32
                    x = int(box[0])
                    xmax = int(box[1])
                    y = int(box[2])
                    ymax = int(box[3])
                    w = xmax - x
                    h = ymax - y
                    
                    # Filter by minimum size
                    if w >= min_size or h >= min_size:
                        boxes.append((x, y, w, h))
        
        # Merge nearby boxes (handles multi-line titles)
        if boxes:
            boxes = self.merge_boxes(boxes, orig_width, orig_height)
        
        return boxes
    
    def _fallback_detection(self, image_path: str, min_size: int) -> List[Tuple[int, int, int, int]]:
        """
        Simple fallback text detection using edge detection and contours.
        Not as accurate as CRAFT but works without EasyOCR installed.
        """
        image = cv2.imread(image_path)
        if image is None:
            return []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        boxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size and aspect ratio (text is usually wider than tall)
            if w >= min_size and h >= min_size / 2 and w > h:
                boxes.append((x, y, w, h))
        
        return boxes
    
    def merge_boxes(self, boxes: List[Tuple[int, int, int, int]], img_width: int, img_height: int) -> List[Tuple[int, int, int, int]]:
        """
        Merge nearby bounding boxes both horizontally and vertically.
        This handles cases where text is split into multiple detections (e.g., multi-line titles).
        
        Args:
            boxes: List of bounding boxes as (x, y, width, height)
            img_width: Image width for calculating relative distances
            img_height: Image height for calculating relative distances
            
        Returns:
            List of merged bounding boxes
        """
        if not boxes:
            return []
        
        # Sort boxes by position (top-to-bottom, left-to-right)
        boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
        merged = []
        
        # Thresholds as percentage of image dimensions
        # These control how close boxes need to be to merge
        horizontal_threshold = img_width * 0.08   # 8% of width
        vertical_threshold = img_height * 0.10     # 10% of height
        
        for box in boxes:
            x, y, w, h = box
            was_merged = False
            
            # Try to merge with existing boxes
            for i, (mx, my, mw, mh) in enumerate(merged):
                # Calculate box boundaries
                box_right = x + w
                box_bottom = y + h
                merged_right = mx + mw
                merged_bottom = my + mh
                
                # Check for HORIZONTAL merging (boxes on same line)
                # Boxes are horizontally aligned if their Y positions are similar
                y_overlap = min(box_bottom, merged_bottom) - max(y, my)
                y_alignment = y_overlap / min(h, mh) if min(h, mh) > 0 else 0
                
                if y_alignment > 0.5:  # At least 50% vertical overlap
                    # Check if boxes are close horizontally
                    horizontal_gap = max(x, mx) - min(box_right, merged_right)
                    if horizontal_gap < horizontal_threshold:
                        # Merge horizontally
                        new_x = min(x, mx)
                        new_y = min(y, my)
                        new_right = max(box_right, merged_right)
                        new_bottom = max(box_bottom, merged_bottom)
                        merged[i] = (new_x, new_y, new_right - new_x, new_bottom - new_y)
                        was_merged = True
                        break
                
                # Check for VERTICAL merging (boxes stacked vertically)
                # Boxes are vertically aligned if their X positions overlap
                x_overlap = min(box_right, merged_right) - max(x, mx)
                x_alignment = x_overlap / min(w, mw) if min(w, mw) > 0 else 0
                
                if x_alignment > 0.3:  # At least 30% horizontal overlap
                    # Check if boxes are close vertically
                    vertical_gap = max(y, my) - min(box_bottom, merged_bottom)
                    if vertical_gap < vertical_threshold:
                        # Merge vertically
                        new_x = min(x, mx)
                        new_y = min(y, my)
                        new_right = max(box_right, merged_right)
                        new_bottom = max(box_bottom, merged_bottom)
                        merged[i] = (new_x, new_y, new_right - new_x, new_bottom - new_y)
                        was_merged = True
                        break
            
            if not was_merged:
                merged.append(box)
        
        return merged
    
    def find_title_region(self, image_path: str, movie_title: Optional[str] = None) -> Optional[Tuple[int, int, int, int]]:
        """
        Find the most likely title region in a movie poster.
        
        Args:
            image_path: Path to the poster image
            movie_title: Optional movie title to help identify the correct text region
            
        Returns:
            Bounding box (x, y, width, height) of the title, or None if not found
        """
        # Detect all text regions
        boxes = self.detect_text_regions(image_path, min_size=30)
        
        if not boxes:
            print("No text regions detected")
            return None
        
        # Load image to get dimensions
        image = cv2.imread(image_path)
        img_height, img_width = image.shape[:2]
        
        # Score each box based on:
        # 1. Size (larger is more likely to be title)
        # 2. Position (top third or center is more likely)
        # 3. Aspect ratio (titles are usually wide)
        
        scored_boxes = []
        for (x, y, w, h) in boxes:
            # Size score (0-1)
            size_score = min(1.0, (w * h) / (img_width * img_height * 0.3))
            
            # Position score (0-1) - prefer top third or center
            center_y = y + h / 2
            if center_y < img_height * 0.33:  # Top third
                position_score = 1.0
            elif center_y < img_height * 0.66:  # Middle third
                position_score = 0.7
            else:  # Bottom third
                position_score = 0.3
            
            # Aspect ratio score (prefer wider text)
            aspect_ratio = w / h if h > 0 else 0
            aspect_score = min(1.0, aspect_ratio / 5.0) if aspect_ratio > 1 else 0.2
            
            # Combined score
            total_score = size_score * 0.5 + position_score * 0.3 + aspect_score * 0.2
            
            scored_boxes.append((total_score, (x, y, w, h)))
        
        # Return the highest scoring box
        scored_boxes.sort(reverse=True, key=lambda x: x[0])
        
        if scored_boxes:
            best_score, best_box = scored_boxes[0]
            print(f"Found title region with confidence score: {best_score:.2f}")
            return best_box
        
        return None
    
    def visualize_detections(self, image_path: str, output_path: str, boxes: List[Tuple[int, int, int, int]]):
        """
        Visualize detected text regions by drawing boxes on the image.
        
        Args:
            image_path: Path to input image
            output_path: Path to save visualization
            boxes: List of bounding boxes to draw
        """
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image from {image_path}")
            return
        
        # Draw boxes
        for (x, y, w, h) in boxes:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        cv2.imwrite(output_path, image)
        print(f"Visualization saved to {output_path}")


def detect_title_in_poster(image_path: str, movie_title: Optional[str] = None) -> Optional[Tuple[int, int, int, int]]:
    """
    Simple function to detect title region in a movie poster.
    
    Args:
        image_path: Path to the poster image
        movie_title: Optional movie title for better detection
        
    Returns:
        Bounding box (x, y, width, height) of the title, or None if not found
    """
    detector = TitleDetector()
    return detector.find_title_region(image_path, movie_title)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python detect_title.py <image_path> [movie_title]")
        print("Example: python detect_title.py poster.jpg \"The Matrix\"")
        sys.exit(1)
    
    image_path = sys.argv[1]
    movie_title = sys.argv[2] if len(sys.argv) > 2 else None
    
    detector = TitleDetector()
    
    # Find title region
    title_box = detector.find_title_region(image_path, movie_title)
    
    if title_box:
        x, y, w, h = title_box
        print(f"\nTitle found at:")
        print(f"  Position: ({x}, {y})")
        print(f"  Size: {w}x{h}")
        
        # Visualize
        output = image_path.replace('.jpg', '_detected.jpg').replace('.png', '_detected.png')
        detector.visualize_detections(image_path, output, [title_box])
    else:
        print("Could not find title in poster")
