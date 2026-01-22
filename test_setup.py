#!/usr/bin/env python3
"""
Test script to verify the pipeline setup
"""

import sys
import json
from pathlib import Path

def check_dependencies():
    """Check if all required packages are installed"""
    print("Checking dependencies...")
    
    dependencies = {
        'requests': 'API calls',
        'flask': 'Web interface',
        'surya': 'OCR processing',
        'PIL': 'Image processing',
        'cv2': 'Computer vision',
    }
    
    missing = []
    
    for package, description in dependencies.items():
        try:
            if package == 'cv2':
                import cv2
            elif package == 'PIL':
                from PIL import Image
            elif package == 'surya':
                import surya
            else:
                __import__(package)
            print(f"  ✓ {package} ({description})")
        except ImportError:
            print(f"  ✗ {package} ({description})")
            missing.append(package)
    
    return len(missing) == 0, missing


def check_files():
    """Check if all required files exist"""
    print("\nChecking files...")
    
    required_files = [
        ('main.py', 'LLM processor'),
        ('pipeline.py', 'Pipeline orchestrator'),
        ('ocr_processor.py', 'OCR processor'),
        ('app.py', 'Flask web server'),
        ('templates/index.html', 'Web interface'),
        ('requirements.txt', 'Dependencies'),
    ]
    
    missing = []
    
    for filename, description in required_files:
        filepath = Path(filename)
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"  ✓ {filename} ({description}) - {size} bytes")
        else:
            print(f"  ✗ {filename} ({description}) - NOT FOUND")
            missing.append(filename)
    
    return len(missing) == 0, missing


def check_env_vars():
    """Check environment variables"""
    print("\nChecking environment variables...")
    
    import os
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
        print(f"  ✓ GEMINI_API_KEY is set ({masked_key})")
        return True
    else:
        print(f"  ✗ GEMINI_API_KEY is not set")
        print(f"    Run: export GEMINI_API_KEY='your-api-key'")
        return False


def check_imports():
    """Check if modules can be imported"""
    print("\nChecking module imports...")
    
    try:
        import main as llm_module
        print("  ✓ main module imports successfully")
    except Exception as e:
        print(f"  ✗ main module import failed: {e}")
        return False
    
    try:
        import ocr_processor
        print("  ✓ ocr_processor module imports successfully")
    except Exception as e:
        print(f"  ✗ ocr_processor module import failed: {e}")
        return False
    
    try:
        import pipeline
        print("  ✓ pipeline module imports successfully")
    except Exception as e:
        print(f"  ✗ pipeline module import failed: {e}")
        return False
    
    try:
        import app
        print("  ✓ app module imports successfully")
    except Exception as e:
        print(f"  ✗ app module import failed: {e}")
        return False
    
    return True


def test_ocr_processor():
    """Test OCR processor configuration"""
    print("\nTesting OCR processor...")
    
    try:
        import ocr_processor
        # Just test that the module loads and has the expected function
        assert hasattr(ocr_processor, 'run_surya_ocr')
        assert hasattr(ocr_processor, 'verify_results_json')
        print("  ✓ OCR processor functions available")
        return True
    except Exception as e:
        print(f"  ✗ OCR processor test failed: {e}")
        return False


def test_pipeline():
    """Test pipeline configuration"""
    print("\nTesting pipeline...")
    
    try:
        import pipeline
        assert hasattr(pipeline, 'PrescriptionPipeline')
        assert hasattr(pipeline, 'process_prescription')
        assert hasattr(pipeline, 'process_prescriptions')
        print("  ✓ Pipeline classes and functions available")
        return True
    except Exception as e:
        print(f"  ✗ Pipeline test failed: {e}")
        return False


def test_llm_module():
    """Test LLM module configuration"""
    print("\nTesting LLM module...")
    
    try:
        import main as llm_module
        assert hasattr(llm_module, 'extract_ocr_text')
        assert hasattr(llm_module, 'call_gemini')
        print("  ✓ LLM module functions available")
        return True
    except Exception as e:
        print(f"  ✗ LLM module test failed: {e}")
        return False


def generate_report():
    """Generate health check report"""
    print("\n" + "="*60)
    print("PIPELINE HEALTH CHECK REPORT")
    print("="*60 + "\n")
    
    results = {
        'dependencies': check_dependencies(),
        'files': check_files(),
        'environment': check_env_vars(),
        'imports': check_imports(),
        'ocr': test_ocr_processor(),
        'pipeline': test_pipeline(),
        'llm': test_llm_module(),
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_ok = True
    
    if isinstance(results['dependencies'], tuple):
        dep_ok, missing = results['dependencies']
        status = "✓ PASS" if dep_ok else "✗ FAIL"
        print(f"{status}: Dependencies")
        if not dep_ok:
            print(f"     Missing: {', '.join(missing)}")
            print(f"     Run: pip install -r requirements.txt")
            all_ok = False
    
    if isinstance(results['files'], tuple):
        files_ok, missing = results['files']
        status = "✓ PASS" if files_ok else "✗ FAIL"
        print(f"{status}: Files")
        if not files_ok:
            print(f"     Missing: {', '.join(missing)}")
            all_ok = False
    
    env_ok = results['environment']
    status = "✓ PASS" if env_ok else "✗ FAIL"
    print(f"{status}: Environment")
    if not env_ok:
        all_ok = False
    
    imports_ok = results['imports']
    status = "✓ PASS" if imports_ok else "✗ FAIL"
    print(f"{status}: Module Imports")
    if not imports_ok:
        all_ok = False
    
    ocr_ok = results['ocr']
    status = "✓ PASS" if ocr_ok else "✗ FAIL"
    print(f"{status}: OCR Processor")
    if not ocr_ok:
        all_ok = False
    
    pipeline_ok = results['pipeline']
    status = "✓ PASS" if pipeline_ok else "✗ FAIL"
    print(f"{status}: Pipeline")
    if not pipeline_ok:
        all_ok = False
    
    llm_ok = results['llm']
    status = "✓ PASS" if llm_ok else "✗ FAIL"
    print(f"{status}: LLM Module")
    if not llm_ok:
        all_ok = False
    
    print("\n" + "="*60)
    
    if all_ok:
        print("✓ ALL CHECKS PASSED - Pipeline is ready!")
        print("\nNext steps:")
        print("  1. python app.py          (Start web server)")
        print("  2. python pipeline.py     (Use CLI)")
        print("  3. python examples.py     (See usage examples)")
    else:
        print("✗ SOME CHECKS FAILED - Please fix issues above")
        print("\nCommon fixes:")
        print("  • pip install -r requirements.txt")
        print("  • export GEMINI_API_KEY='your-api-key'")
        print("  • Check that all files are in the correct directory")
    
    print("="*60 + "\n")
    
    return all_ok


if __name__ == "__main__":
    success = generate_report()
    sys.exit(0 if success else 1)
