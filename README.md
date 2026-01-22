# Prescription Processing Pipeline

Complete end-to-end pipeline for processing prescription images using Surya OCR and LLM extraction.

## Architecture

```
Image Upload
    ↓
Surya OCR (ocr_processor.py)
    ↓
results.json
    ↓
LLM Processing (main.py)
    ↓
Structured JSON Output
```

## Components

### 1. **ocr_processor.py** - OCR Engine
- Uses Surya OCR to extract text from prescription images
- Generates `results.json` in the expected format
- Validates output format
- Supports batch processing

### 2. **pipeline.py** - Main Orchestrator
- Coordinates the entire workflow
- Validates inputs
- Manages intermediate files
- Interfaces between OCR and LLM
- Can be used as a module or CLI tool

### 3. **main.py** - LLM Processor (Your existing code)
- Extracts structured data from OCR text
- Uses Gemini Flash 2.5 API
- Outputs standardized JSON format
- Handles validation and error cases

### 4. **app.py** - Flask Web Interface
- Provides user-friendly web upload interface
- Handles file uploads
- Manages asynchronous processing
- Returns results in JSON format

## Installation

### 1. Install Dependencies

```bash
# Core dependencies
pip install requests surya-ocr flask pillow opencv-python

# Or install from requirements.txt
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

## Usage

### Option 1: Web Interface (Recommended)

```bash
python app.py
```

Then open `http://localhost:5000` in your browser and upload images.

### Option 2: Command Line

**Single image:**
```bash
python pipeline.py /path/to/prescription.png
```

**Multiple images:**
```bash
python pipeline.py img1.png img2.png img3.png
```

**With custom output directory:**
```bash
python pipeline.py prescription.png --output ./my_results
```

### Option 3: Python Module

```python
from pipeline import process_prescription

# Single image
result = process_prescription('/path/to/prescription.png')
print(result)

# Multiple images with output directory
from pathlib import Path
from pipeline import PrescriptionPipeline

pipeline = PrescriptionPipeline(output_dir=Path('./results'))
result = pipeline.process_images(['img1.png', 'img2.png'])
```

## Output Format

The pipeline outputs JSON in this format:

```json
{
  "status": "ok",
  "message": "Prescription extracted successfully",
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
```

Or if processing fails:

```json
{
  "status": "reupload_required",
  "message": "Insufficient or ambiguous data. Please upload a clearer image.",
  "data": null
}
```

## Configuration

### Surya OCR Settings (in ocr_processor.py)

```python
cmd = [
    "surya_ocr",
    str(temp_input),
    "--output_dir", str(output_dir),
    "--task_name", "ocr_with_boxes",  # or "ocr"
    "--images",
    "--disable_math",
]
```

### LLM Settings (in main.py)

- Model: `gemini-2.5-flash`
- Temperature: 0 (deterministic)
- Modify `MASTER_PROMPT` for different extraction rules

### Flask Settings (in app.py)

```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff', 'tif', 'webp'}
```

## Directory Structure

```
prescription_llm/
├── main.py                 # LLM processor (your original code)
├── ocr_processor.py        # Surya OCR wrapper
├── pipeline.py             # Main orchestrator
├── app.py                  # Flask web interface
├── templates/
│   └── index.html          # Web UI
├── results.json            # OCR output (generated)
└── pipeline_output/        # Pipeline results directory
    └── ocr/
        └── results.json    # OCR results for LLM
```

## Error Handling

The pipeline handles various error scenarios:

1. **Missing/Invalid Images**: Validates files before processing
2. **OCR Failures**: Falls back with empty text handling
3. **API Errors**: Returns error status with message
4. **Invalid JSON**: Safely extracts valid JSON from LLM response

## Performance Tips

1. **Use GPU for OCR** (if available):
   - Modify `ocr_processor.py` to enable GPU in Surya

2. **Batch Processing**:
   - Process multiple images together to save overhead

3. **Caching**:
   - Results are cached in `pipeline_output/`
   - Intermediate `results.json` is available for inspection

## Troubleshooting

### "surya_ocr command not found"
```bash
pip install surya-ocr --upgrade
```

### "GEMINI_API_KEY not set"
```bash
export GEMINI_API_KEY="your-key-here"
echo $GEMINI_API_KEY  # verify
```

### "Port 5000 already in use"
```bash
python app.py --port 5001
```

### Low OCR confidence
- Ensure images are clear and well-lit
- Try higher resolution images
- Check that prescription is fully visible

### Supported Image Formats
- PNG (.png)
- JPEG (.jpg, .jpeg)
- BMP (.bmp)
- GIF (.gif)
- TIFF (.tiff, .tif)
- WebP (.webp)

## Advanced Usage

### Custom Extraction Rules

Modify `MASTER_PROMPT` in `main.py`:

```python
MASTER_PROMPT = """
You are a strict eyeglass prescription parser.

[Your custom rules here]
"""
```

### Custom Output Format

Modify the result structure in `main.py` `call_gemini()` function.

### Extending the Pipeline

```python
from pipeline import PrescriptionPipeline

class CustomPipeline(PrescriptionPipeline):
    def _run_llm(self):
        # Custom LLM logic
        return super()._run_llm()
```

## API Reference

### PrescriptionPipeline Class

```python
class PrescriptionPipeline:
    def __init__(self, output_dir: Optional[Path] = None)
    def process_images(self, image_paths: list) -> dict
    def get_result(self) -> dict
```

### Convenience Functions

```python
# Process single image
def process_prescription(image_path, output_dir=None) -> dict

# Process multiple images
def process_prescriptions(image_paths, output_dir=None) -> dict
```

### Flask Endpoints

- `GET /` - Web interface
- `POST /upload` - Process images (multipart/form-data)
- `GET /health` - Health check

## Support

For issues or questions:
1. Check error messages in console
2. Review logs in `pipeline_output/`
3. Verify environment variables are set
4. Ensure all dependencies are installed

## License

Same as main.py and associated code
