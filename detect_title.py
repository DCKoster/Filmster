"""
Title Detection in Movie Posters
Uses EAST text detector from OpenCV to find text regions in movie posters.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import os


class TitleDetector:
    """Detects text regions in movie posters using EAST text detector."""
    
    # EAST model can be downloaded from:
    # https://github.com/oyyd/frozen_east_text_detection.pb/raw/master/frozen_east_text_detection.pb
    EAST_MODEL_PATH = "frozen_east_text_detection.pb"
    
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.5):
        """
        Initialize the text detector.
        
        Args:
            model_path: Path to EAST model file. If None, uses default path.
            confidence_threshold: Minimum confidence for text detection (0-1)
        """
        self.model_path = model_path or self.EAST_MODEL_PATH
        self.confidence_threshold = confidence_threshold
        self.detector = None
        
        if os.path.exists(self.model_path):
            self.detector = cv2.dnn.readNet(self.model_path)
        else:
            print(f"Warning: EAST model not found at {self.model_path}")
            print("Download from: https://github.com/oyyd/frozen_east_text_detection.pb/raw/master/frozen_east_text_detection.pb")
    
    def detect_text_regions(self, image_path: str, min_size: int = 50) -> List[Tuple[int, int, int, int]]:
        """
        Detect text regions in an image.
        
        Args:
            image_path: Path to the image file
            min_size: Minimum width or height for detected regions (filters small text)
            
        Returns:
            List of bounding boxes as (x, y, width, height) tuples
        """
        if not self.detector:
            print("Error: EAST detector not initialized. Model file not found.")
            return self._fallback_detection(image_path, min_size)
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image from {image_path}")
            return []
        
        orig_height, orig_width = image.shape[:2]
        
        # EAST requires input dimensions to be multiples of 32
        new_width = (orig_width // 32) * 32
        new_height = (orig_height // 32) * 32
        
        # Calculate ratios for coordinate conversion
        ratio_width = orig_width / new_width
        ratio_height = orig_height / new_height
        
        # Resize image for EAST
        resized = cv2.resize(image, (new_width, new_height))
        
        # Create blob and run detection
        blob = cv2.dnn.blobFromImage(resized, 1.0, (new_width, new_height),
                                     (123.68, 116.78, 103.94), swapRB=True, crop=False)
        
        self.detector.setInput(blob)
        
        # Get output layers
        layer_names = ['feature_fusion/Conv_7/Sigmoid', 'feature_fusion/concat_3']
        scores, geometry = self.detector.forward(layer_names)
        
        # Decode predictions
        boxes = self._decode_predictions(scores, geometry, self.confidence_threshold)
        
        # Convert back to original image coordinates and filter by size
        final_boxes = []
        for (x, y, w, h) in boxes:
            x = int(x * ratio_width)
            y = int(y * ratio_height)
            w = int(w * ratio_width)
            h = int(h * ratio_height)
            
            # Filter by minimum size
            if w >= min_size or h >= min_size:
                final_boxes.append((x, y, w, h))
        
        return final_boxes
    
    def _decode_predictions(self, scores, geometry, min_confidence: float) -> List[Tuple[int, int, int, int]]:
        """Decode EAST detector predictions into bounding boxes."""
        num_rows, num_cols = scores.shape[2:4]
        boxes = []
        confidences = []
        
        for y in range(num_rows):
            scores_data = scores[0, 0, y]
            x0_data = geometry[0, 0, y]
            x1_data = geometry[0, 1, y]
            x2_data = geometry[0, 2, y]
            x3_data = geometry[0, 3, y]
            angles_data = geometry[0, 4, y]
            
            for x in range(num_cols):
                if scores_data[x] < min_confidence:
                    continue
                
                # Calculate offset
                offset_x = x * 4.0
                offset_y = y * 4.0
                
                # Extract rotation angle
                angle = angles_data[x]
                cos = np.cos(angle)
                sin = np.sin(angle)
                
                # Calculate dimensions
                h = x0_data[x] + x2_data[x]
                w = x1_data[x] + x3_data[x]
                
                # Calculate box coordinates
                end_x = int(offset_x + (cos * x1_data[x]) + (sin * x2_data[x]))
                end_y = int(offset_y - (sin * x1_data[x]) + (cos * x2_data[x]))
                start_x = int(end_x - w)
                start_y = int(end_y - h)
                
                boxes.append((start_x, start_y, int(w), int(h)))
                confidences.append(scores_data[x])
        
        # Apply non-maximum suppression
        if boxes:
            indices = cv2.dnn.NMSBoxes(boxes, confidences, min_confidence, 0.4)
            return [boxes[i] for i in indices.flatten()] if len(indices) > 0 else []
        
        return []
    
    def _fallback_detection(self, image_path: str, min_size: int) -> List[Tuple[int, int, int, int]]:
        """
        Simple fallback text detection using edge detection and contours.
        Not as accurate as EAST but works without the model file.
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
