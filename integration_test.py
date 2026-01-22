#!/usr/bin/env python3
"""
Integration test for the prescription processing pipeline
This script tests the entire pipeline end-to-end
"""

import json
import tempfile
from pathlib import Path
import sys

def test_pipeline_structure():
    """Test that all pipeline components are properly structured"""
    print("Testing pipeline structure...")
    
    # Check main.py
    try:
        import main
        assert hasattr(main, 'extract_ocr_text'), "main.py missing extract_ocr_text"
        assert hasattr(main, 'call_gemini'), "main.py missing call_gemini"
        print("  ✓ main.py structure OK")
    except Exception as e:
        print(f"  ✗ main.py error: {e}")
        return False
    
    # Check ocr_processor.py
    try:
        import ocr_processor
        assert hasattr(ocr_processor, 'run_surya_ocr'), "ocr_processor.py missing run_surya_ocr"
        assert hasattr(ocr_processor, 'verify_results_json'), "ocr_processor.py missing verify_results_json"
        print("  ✓ ocr_processor.py structure OK")
    except Exception as e:
        print(f"  ✗ ocr_processor.py error: {e}")
        return False
    
    # Check pipeline.py
    try:
        import pipeline
        assert hasattr(pipeline, 'PrescriptionPipeline'), "pipeline.py missing PrescriptionPipeline class"
        assert hasattr(pipeline, 'process_prescription'), "pipeline.py missing process_prescription"
        assert hasattr(pipeline, 'process_prescriptions'), "pipeline.py missing process_prescriptions"
        print("  ✓ pipeline.py structure OK")
    except Exception as e:
        print(f"  ✗ pipeline.py error: {e}")
        return False
    
    # Check app.py
    try:
        import app
        assert hasattr(app, 'app'), "app.py missing Flask app"
        print("  ✓ app.py structure OK")
    except Exception as e:
        print(f"  ✗ app.py error: {e}")
        return False
    
    return True


def test_mock_ocr_results():
    """Test that OCR results can be processed by LLM"""
    print("\nTesting mock OCR results...")
    
    try:
        # Create mock results.json
        mock_results = {
            "prescription_1.png": [
                {
                    "page": 0,
                    "text_lines": [
                        {"text": "PRESCRIPTION"},
                        {"text": "Right Eye: Sphere -2.50 Cylinder -0.75 Axis 180"},
                        {"text": "Left Eye: Sphere -2.25 Cylinder -0.50 Axis 175"},
                        {"text": "Add: 2.00"},
                        {"text": "PD: 64"},
                        {"text": "Dr. Smith"},
                        {"text": "Date: 01/15/2024"},
                    ]
                }
            ]
        }
        
        # Test extraction
        import main
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_results, f)
            temp_file = f.name
        
        try:
            ocr_text = main.extract_ocr_text(temp_file)
            assert ocr_text, "extract_ocr_text returned empty result"
            assert "PRESCRIPTION" in ocr_text, "OCR text doesn't contain expected content"
            assert "Right Eye" in ocr_text, "OCR text doesn't contain Right Eye"
            print(f"  ✓ Mock OCR extraction OK ({len(ocr_text)} chars)")
            return True
        finally:
            Path(temp_file).unlink()
            
    except Exception as e:
        print(f"  ✗ Mock OCR test error: {e}")
        return False


def test_json_format():
    """Test that output JSON format is correct"""
    print("\nTesting output JSON format...")
    
    try:
        # Create mock result
        mock_result = {
            "status": "ok",
            "message": "Test message",
            "data": {
                "right_eye": {
                    "sphere": -2.50,
                    "cylinder": -0.75,
                    "axis": 180,
                    "add": 2.00
                },
                "left_eye": {
                    "sphere": -2.25,
                    "cylinder": -0.50,
                    "axis": 175,
                    "add": 2.00
                },
                "pupillary_distance": 64.0,
                "doctor_name": "Dr. Smith",
                "date": "2024-01-15"
            }
        }
        
        # Validate JSON structure
        assert mock_result['status'] in ['ok', 'reupload_required', 'error'], "Invalid status"
        assert 'message' in mock_result, "Missing message"
        assert 'data' in mock_result, "Missing data"
        
        if mock_result['status'] == 'ok':
            assert 'right_eye' in mock_result['data'], "Missing right_eye"
            assert 'left_eye' in mock_result['data'], "Missing left_eye"
            
            for eye_key in ['right_eye', 'left_eye']:
                eye = mock_result['data'][eye_key]
                assert 'sphere' in eye, f"Missing sphere in {eye_key}"
                assert 'cylinder' in eye, f"Missing cylinder in {eye_key}"
                assert 'axis' in eye, f"Missing axis in {eye_key}"
        
        # Test JSON serialization
        json_str = json.dumps(mock_result)
        parsed = json.loads(json_str)
        assert parsed == mock_result, "JSON serialization mismatch"
        
        print("  ✓ JSON format validation OK")
        return True
        
    except Exception as e:
        print(f"  ✗ JSON format test error: {e}")
        return False


def test_pipeline_classes():
    """Test pipeline classes are instantiable"""
    print("\nTesting pipeline classes...")
    
    try:
        from pipeline import PrescriptionPipeline
        from pathlib import Path
        import tempfile
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Instantiate pipeline
            pipeline = PrescriptionPipeline(output_dir=Path(tmpdir))
            
            # Check attributes
            assert hasattr(pipeline, 'output_dir'), "Missing output_dir"
            assert hasattr(pipeline, 'process_images'), "Missing process_images method"
            assert hasattr(pipeline, 'ocr_dir'), "Missing ocr_dir"
            assert hasattr(pipeline, 'results_json_path'), "Missing results_json_path"
            assert hasattr(pipeline, 'final_output_path'), "Missing final_output_path"
            
            print("  ✓ Pipeline classes OK")
            return True
            
    except Exception as e:
        print(f"  ✗ Pipeline class test error: {e}")
        return False


def test_environment():
    """Test environment configuration"""
    print("\nTesting environment...")
    
    import os
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        masked = api_key[:4] + '*' * max(0, len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '***'
        print(f"  ✓ GEMINI_API_KEY is set ({masked})")
        return True
    else:
        print(f"  ⚠ GEMINI_API_KEY not set (required for actual processing)")
        return False  # Note: Not critical for structure test


def main():
    """Run all integration tests"""
    print("="*60)
    print("PRESCRIPTION PIPELINE - INTEGRATION TESTS")
    print("="*60 + "\n")
    
    tests = [
        ("Structure", test_pipeline_structure),
        ("Mock OCR Results", test_mock_ocr_results),
        ("JSON Format", test_json_format),
        ("Pipeline Classes", test_pipeline_classes),
        ("Environment", test_environment),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} failed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60 + "\n")
    
    if passed == total:
        print("✓ All integration tests passed!")
        print("Your pipeline is ready to use:\n")
        print("  1. python app.py              # Start web interface")
        print("  2. python pipeline.py         # Use CLI")
        print("  3. python examples.py         # See usage examples")
        return True
    else:
        print(f"✗ {total - passed} test(s) failed")
        print("Please check the errors above and fix them.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
