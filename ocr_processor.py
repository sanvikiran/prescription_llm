"""
OCR Processor using EasyOCR (simpler, more reliable)
Processes images and generates results.json in the expected format
"""

import json
from pathlib import Path
import tempfile
from typing import Optional
import cv2
import numpy as np


def rotate_image(image, angle):
    """Rotate image by angle degrees"""
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    return rotated


def detect_and_correct_rotation(image):
    """
    Detect if image is rotated 90, 180, or 270 degrees and correct it
    Uses simple aspect ratio analysis on the image
    
    Args:
        image: Input image (grayscale)
        
    Returns:
        Corrected image
    """
    h, w = image.shape
    
    # If image is more vertical than horizontal, it might need 90/270 rotation
    aspect_ratio = w / h
    
    # Only rotate if aspect ratio suggests the image needs it
    # Normal documents are wider than tall
    if aspect_ratio < 0.6:  # Very tall image, likely needs 90 or 270
        # Try 90 degree rotation
        test_90 = rotate_image(image, 90)
        # If after rotation it's wider, keep it
        h90, w90 = test_90.shape
        if w90 / h90 > 1.2:  # Now wider after 90 rotation
            return test_90
    
    return image


def deskew_image(image):
    """
    Deskew slightly tilted image using contour analysis
    Only corrects if angle is > 2 degrees
    
    Args:
        image: Input image (grayscale)
        
    Returns:
        Deskewed image
    """
    # Get non-zero coordinates
    coords = np.column_stack(np.where(image > 0))
    
    if len(coords) < 50:  # Not enough text
        return image
    
    try:
        # Fit a line to the text using least squares
        data_pts = np.float32(coords)
        vx, vy, x, y = cv2.fitLine(data_pts, cv2.DIST_L2, 0, 0.01, 0.01)
        
        # Calculate angle
        angle = np.arctan2(vy, vx) * 180 / np.pi
        
        # Normalize angle to [-45, 45]
        if angle > 45:
            angle -= 90
        elif angle < -45:
            angle += 90
        
        # Only correct if significant tilt
        if abs(angle) > 2:
            image = rotate_image(image, angle)
    except:
        pass
    
    return image


def preprocess_image(image_path):
    """
    Preprocess image for better OCR accuracy (minimal changes)
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Preprocessed image (numpy array) or original if preprocessing fails
    """
    # Read image
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # =====================
        # ROTATION CORRECTION
        # =====================
        # Detect and correct 90/180/270 degree rotations
        gray = detect_and_correct_rotation(gray)
        
        # Deskew slightly tilted images
        gray = deskew_image(gray)
        
        # =====================
        # VERY LIGHT ENHANCEMENT
        # =====================
        # Only apply if image is too dark
        if np.mean(gray) < 100:
            # Light CLAHE only if dark
            clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(12, 12))
            gray = clahe.apply(gray)
        
        # Very light denoising
        gray = cv2.fastNlMeansDenoising(gray, h=3)
        
        return gray
    except Exception as e:
        print(f"  ⚠ Preprocessing warning: {e}, using original image")
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def run_surya_ocr(image_paths: list, output_dir: Optional[Path] = None) -> Path:
    """
    Run OCR on a list of images and generate results.json
    
    Args:
        image_paths: List of paths to image files
        output_dir: Directory to save results. If None, uses a temp directory
        
    Returns:
        Path to the results.json file
    """
    if not output_dir:
        output_dir = Path(tempfile.mkdtemp(prefix="ocr_"))
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate input images
    validated_paths = []
    for img_path in image_paths:
        img_path = Path(img_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")
        validated_paths.append(img_path)
    
    print(f"Running OCR on {len(validated_paths)} image(s)...")
    
    try:
        import easyocr
        
        # Initialize reader (English language)
        print("  Initializing OCR reader...")
        reader = easyocr.Reader(['en'], gpu=False)
        
        # Process each image
        results_dict = {}
        
        for img_path in validated_paths:
            img_path = Path(img_path)
            print(f"  Processing: {img_path.name}")
            
            # Preprocess image
            print(f"    Preprocessing image...")
            preprocessed = preprocess_image(img_path)
            
            # Run OCR on preprocessed image
            results = reader.readtext(preprocessed)
            
            # Format results
            text_lines = []
            for (bbox, text, confidence) in results:
                text_lines.append({
                    "text": text.strip(),
                    "confidence": float(confidence),
                    "bbox": bbox,
                    "polygon": None
                })
            
            results_dict[img_path.name] = [
                {
                    "page": 0,
                    "text_lines": text_lines
                }
            ]
        
        # Save results.json
        results_json = output_dir / "results.json"
        with open(results_json, "w", encoding="utf-8") as f:
            json.dump(results_dict, f, indent=2, default=str)
        
        print(f"✓ OCR completed. Results saved to {results_json}")
        return results_json
        
    except ImportError:
        raise RuntimeError(
            "EasyOCR not installed. Please run:\n"
            "  python3 -m pip install easyocr"
        )
    except Exception as e:
        raise RuntimeError(f"Error running OCR: {e}")


def verify_results_json(results_path: Path) -> dict:
    """
    Verify that results.json has the expected format
    
    Args:
        results_path: Path to results.json
        
    Returns:
        The parsed JSON data
        
    Raises:
        ValueError if format is invalid
    """
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Verify structure
    if not isinstance(data, dict):
        raise ValueError("results.json should be a dictionary")
    
    for file_key, pages in data.items():
        if not isinstance(pages, list):
            raise ValueError(f"Value for {file_key} should be a list of pages")
        
        for page in pages:
            if not isinstance(page, dict):
                raise ValueError("Each page should be a dictionary")
            
            if "text_lines" not in page:
                raise ValueError("Each page must have 'text_lines' key")
            
            for line in page["text_lines"]:
                if "text" not in line:
                    raise ValueError("Each text_line must have 'text' key")
    
    print(f"✓ results.json validation passed")
    return data


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_processor.py <image_path> [image_path2 ...]")
        sys.exit(1)
    
    image_paths = sys.argv[1:]
    results_json = run_surya_ocr(image_paths)
    print(f"Results: {results_json}")
