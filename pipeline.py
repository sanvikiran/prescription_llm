"""
Complete Prescription Processing Pipeline
Image → Surya OCR → LLM Processing → Structured Output
"""

import json
import os
import sys
from pathlib import Path
from typing import Union, Optional
import shutil

from ocr_processor import run_surya_ocr, verify_results_json
import main as llm_module


class PrescriptionPipeline:
    """
    End-to-end pipeline for prescription image processing
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the pipeline
        
        Args:
            output_dir: Directory to store intermediate and final results
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "pipeline_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.ocr_dir = self.output_dir / "ocr"
        self.results_json_path = self.ocr_dir / "results.json"
        self.final_output_path = self.output_dir / "prescription_result.json"
        
    def process_images(self, image_paths: list) -> dict:
        """
        Complete pipeline: Images → OCR → LLM → Result
        
        Args:
            image_paths: List of paths to prescription images
            
        Returns:
            Structured prescription data
        """
        print("\n" + "="*60)
        print("PRESCRIPTION PROCESSING PIPELINE")
        print("="*60)
        
        # Step 1: Validate inputs
        print("\n[STEP 1] Validating input images...")
        image_paths = self._validate_images(image_paths)
        
        # Step 2: Run Surya OCR
        print("\n[STEP 2] Running Surya OCR...")
        self.results_json_path = self._run_ocr(image_paths)
        
        # Step 3: Process through LLM
        print("\n[STEP 3] Processing through LLM...")
        result = self._run_llm()
        
        # Step 4: Save final result
        print("\n[STEP 4] Saving results...")
        self._save_result(result)
        
        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60)
        
        return result
    
    def _validate_images(self, image_paths: list) -> list:
        """Validate that all images exist and are readable"""
        valid_paths = []
        
        for path_str in image_paths:
            path = Path(path_str)
            
            if not path.exists():
                print(f"  ✗ Image not found: {path}")
                continue
            
            if not path.is_file():
                print(f"  ✗ Not a file: {path}")
                continue
            
            # Check if it's an image (basic extension check)
            if path.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif', '.webp']:
                print(f"  ✗ Not an image file: {path}")
                continue
            
            valid_paths.append(path)
            print(f"  ✓ {path.name}")
        
        if not valid_paths:
            raise ValueError("No valid images provided")
        
        print(f"\n✓ Found {len(valid_paths)} valid image(s)")
        return valid_paths
    
    def _run_ocr(self, image_paths: list) -> Path:
        """Run Surya OCR on images"""
        self.ocr_dir.mkdir(parents=True, exist_ok=True)
        results_json = run_surya_ocr(image_paths, self.ocr_dir)
        
        # Verify format
        verify_results_json(results_json)
        
        return results_json
    
    def _run_llm(self) -> dict:
        """
        Run the LLM processing on OCR results
        This uses the main.py logic
        """
        try:
            # Extract OCR text and confidence data
            ocr_text = llm_module.extract_ocr_text(str(self.results_json_path))
            ocr_data = llm_module.extract_ocr_with_confidence(str(self.results_json_path))
            
            if not ocr_text.strip():
                print("  ⚠ OCR text is empty")
                return {
                    "status": "reupload_required",
                    "message": "OCR text is empty. Please upload a clearer image.",
                    "data": None
                }
            
            print(f"  ✓ Extracted {len(ocr_text)} characters from OCR")
            
            # Calculate and display OCR confidence
            if ocr_data:
                avg_confidence = sum([item['confidence'] for item in ocr_data]) / len(ocr_data)
                print(f"  ✓ OCR Confidence Score: {round(avg_confidence, 3)}")
            
            # Call Gemini with OCR data
            print("  → Calling Gemini API...")
            result = llm_module.call_gemini(ocr_text, ocr_data)
            
            # Verify result structure
            if "status" not in result or "data" not in result:
                raise ValueError("Invalid LLM response format")
            
            print(f"  ✓ LLM processing complete (status: {result['status']})")
            
            # Validate and fix prescription
            print("  → Validating prescription rules...")
            result = llm_module.validate_and_fix_prescription(result)
            print(f"  ✓ Validation complete")
            
            return result
            
        except Exception as e:
            print(f"  ✗ LLM processing error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
    
    def _save_result(self, result: dict) -> None:
        """Save the final result to JSON"""
        with open(self.final_output_path, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"  ✓ Final result saved to: {self.final_output_path}")
    
    def get_result(self) -> dict:
        """Load and return the final result"""
        if self.final_output_path.exists():
            with open(self.final_output_path, "r") as f:
                return json.load(f)
        return None


def process_prescription(image_path: Union[str, Path], output_dir: Optional[Path] = None) -> dict:
    """
    Convenience function to process a single prescription image
    
    Args:
        image_path: Path to prescription image
        output_dir: Directory for outputs
        
    Returns:
        Structured prescription data
    """
    pipeline = PrescriptionPipeline(output_dir)
    return pipeline.process_images([image_path])


def process_prescriptions(image_paths: list, output_dir: Optional[Path] = None) -> dict:
    """
    Convenience function to process multiple prescription images
    
    Args:
        image_paths: List of paths to prescription images
        output_dir: Directory for outputs
        
    Returns:
        Structured prescription data
    """
    pipeline = PrescriptionPipeline(output_dir)
    return pipeline.process_images(image_paths)


if __name__ == "__main__":
    # CLI interface
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <image_path> [image_path2 ...] [--output <output_dir>]")
        print("\nExample:")
        print("  python pipeline.py prescription.png")
        print("  python pipeline.py img1.png img2.png --output ./results")
        sys.exit(1)
    
    # Parse arguments
    image_paths = []
    output_dir = None
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--output" and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            i += 2
        else:
            image_paths.append(sys.argv[i])
            i += 1
    
    try:
        result = process_prescriptions(image_paths, output_dir)
        print("\n" + "="*60)
        print("FINAL RESULT:")
        print("="*60)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n✗ Pipeline error: {e}")
        sys.exit(1)
