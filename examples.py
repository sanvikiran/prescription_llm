#!/usr/bin/env python3
"""
Example usage of the Prescription Processing Pipeline
"""

from pathlib import Path
from pipeline import (
    PrescriptionPipeline,
    process_prescription,
    process_prescriptions
)
import json


def example_1_single_image():
    """Process a single prescription image"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Process Single Image")
    print("="*60)
    
    # Replace with your image path
    image_path = "prescription.png"
    
    try:
        result = process_prescription(image_path)
        print("\nResult:")
        print(json.dumps(result, indent=2))
    except FileNotFoundError:
        print(f"Image not found: {image_path}")
        print("Please provide a valid image path")


def example_2_multiple_images():
    """Process multiple prescription images"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Process Multiple Images")
    print("="*60)
    
    image_paths = [
        "prescription1.png",
        "prescription2.png",
        "prescription3.png",
    ]
    
    try:
        result = process_prescriptions(image_paths)
        print("\nResult:")
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        print(f"One or more images not found: {e}")
        print("Please provide valid image paths")


def example_3_custom_output_dir():
    """Process with custom output directory"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Custom Output Directory")
    print("="*60)
    
    image_path = "prescription.png"
    output_dir = Path("./custom_results")
    
    try:
        pipeline = PrescriptionPipeline(output_dir=output_dir)
        result = pipeline.process_images([image_path])
        
        print(f"\nResults saved to: {output_dir.absolute()}")
        print(f"Final output: {output_dir / 'prescription_result.json'}")
        print(f"Intermediate OCR: {output_dir / 'ocr' / 'results.json'}")
        
        print("\nResult:")
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        print(f"Image not found: {e}")


def example_4_error_handling():
    """Demonstrate error handling"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Error Handling")
    print("="*60)
    
    print("\nScenario 1: Missing image")
    try:
        result = process_prescription("nonexistent.png")
    except FileNotFoundError as e:
        print(f"✓ Caught error: {e}")
    
    print("\nScenario 2: Invalid image format")
    try:
        # Create a dummy file with wrong extension
        Path("test.txt").write_text("not an image")
        result = process_prescription("test.txt")
        Path("test.txt").unlink()
    except Exception as e:
        print(f"✓ Caught error: {e}")
        Path("test.txt").unlink(missing_ok=True)


def example_5_batch_processing():
    """Process images from a directory"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Batch Processing from Directory")
    print("="*60)
    
    # Get all PNG files from current directory
    image_dir = Path("./prescriptions")
    
    if not image_dir.exists():
        print(f"Directory not found: {image_dir}")
        print("Create the directory and add prescription images to test this example")
        return
    
    image_paths = list(image_dir.glob("*.png"))
    
    if not image_paths:
        print(f"No PNG files found in {image_dir}")
        return
    
    print(f"Found {len(image_paths)} images:")
    for img in image_paths:
        print(f"  - {img.name}")
    
    try:
        results = []
        for img_path in image_paths:
            print(f"\nProcessing {img_path.name}...")
            result = process_prescription(str(img_path))
            results.append({
                "file": img_path.name,
                "result": result
            })
        
        # Save batch results
        output_file = Path("batch_results.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Batch results saved to {output_file}")
        
    except Exception as e:
        print(f"✗ Batch processing error: {e}")


def example_6_advanced_pipeline():
    """Advanced usage with custom pipeline"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Advanced Pipeline Customization")
    print("="*60)
    
    class CustomPipeline(PrescriptionPipeline):
        """Extended pipeline with custom logic"""
        
        def _run_llm(self):
            """Custom LLM processing"""
            print("  → Running custom LLM logic...")
            result = super()._run_llm()
            
            # Add custom post-processing
            if result.get("status") == "ok" and result.get("data"):
                # Example: Add extraction confidence
                result["extraction_confidence"] = 0.95
            
            return result
    
    image_path = "prescription.png"
    
    try:
        pipeline = CustomPipeline(output_dir=Path("./advanced_results"))
        result = pipeline.process_images([image_path])
        
        print("\nCustom result:")
        print(json.dumps(result, indent=2))
    except FileNotFoundError:
        print(f"Image not found: {image_path}")


def main():
    """Run examples"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "Prescription Processing Pipeline Examples" + " "*7 + "║")
    print("╚" + "="*58 + "╝")
    
    examples = [
        ("Single Image Processing", example_1_single_image),
        ("Multiple Images", example_2_multiple_images),
        ("Custom Output Directory", example_3_custom_output_dir),
        ("Error Handling", example_4_error_handling),
        ("Batch Processing from Directory", example_5_batch_processing),
        ("Advanced Pipeline Customization", example_6_advanced_pipeline),
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nTo run all examples (requires valid image files):")
    print("  python examples.py\n")
    
    print("To modify these examples:")
    print("  1. Edit this file (examples.py)")
    print("  2. Update image paths to match your files")
    print("  3. Run: python examples.py\n")
    
    print("="*60)


if __name__ == "__main__":
    # Uncomment examples to run them
    
    print("\nNote: These examples require valid prescription images.")
    print("Please update the image paths in this file before running.\n")
    
    main()
    
    # Uncomment to run examples:
    # example_1_single_image()
    # example_2_multiple_images()
    # example_3_custom_output_dir()
    # example_4_error_handling()
    # example_5_batch_processing()
    # example_6_advanced_pipeline()
