# Complete Setup and Deployment Guide

## Overview

Your prescription processing pipeline is now fully integrated with:
- **Surya OCR** for image processing
- **Your LLM** (Gemini) for data extraction
- **Web interface** for easy uploads
- **CLI tools** for automation
- **Docker** for deployment

## Installation Steps

### Step 1: Verify Files

Check that all files are in place:

```bash
cd /Users/sanvikiran/Desktop/prescription_llm
ls -la
```

You should see:
```
main.py
ocr_processor.py
pipeline.py
app.py
requirements.txt
README.md
QUICKSTART.md
examples.py
test_setup.py
templates/
├── index.html
docker-compose.yml
Dockerfile
.env.example
setup.sh
```

### Step 2: Install Dependencies

```bash
# Option A: Using pip directly
pip install -r requirements.txt

# Option B: Using the setup script
bash setup.sh
```

### Step 3: Set Environment Variables

```bash
# Set Gemini API Key
export GEMINI_API_KEY="your-gemini-api-key-here"

# Verify it's set
echo $GEMINI_API_KEY
```

**To make it permanent**, add to your shell profile (`~/.zshrc` or `~/.bash_profile`):
```bash
echo 'export GEMINI_API_KEY="your-key"' >> ~/.zshrc
source ~/.zshrc
```

### Step 4: Verify Setup

```bash
python test_setup.py
```

Expected output:
```
✓ ALL CHECKS PASSED - Pipeline is ready!
```

## Usage Options

### Option 1: Web Interface (Recommended for Users)

**Start the server:**
```bash
python app.py
```

**Open in browser:**
```
http://localhost:5000
```

**Features:**
- Drag-and-drop image upload
- Real-time processing
- Beautiful results display
- Copy JSON to clipboard
- Support for multiple images

### Option 2: Command Line (Recommended for Automation)

**Single image:**
```bash
python pipeline.py /path/to/prescription.png
```

**Multiple images:**
```bash
python pipeline.py img1.png img2.png img3.png
```

**Custom output directory:**
```bash
python pipeline.py prescription.png --output /custom/output/path
```

**Batch processing from directory:**
```bash
python pipeline.py prescriptions/*.png --output ./results
```

### Option 3: Python Module (Recommended for Integration)

```python
from pipeline import process_prescription, PrescriptionPipeline
from pathlib import Path

# Simple usage
result = process_prescription('prescription.png')
print(result)

# Advanced usage
pipeline = PrescriptionPipeline(output_dir=Path('./results'))
result = pipeline.process_images(['img1.png', 'img2.png'])
```

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start
docker-compose up

# Run in background
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f
```

Then open: `http://localhost:5000`

### Using Docker directly

```bash
# Build image
docker build -t prescription-processor .

# Run container
docker run -p 5000:5000 \
  -e GEMINI_API_KEY="your-key" \
  -v $(pwd)/pipeline_output:/app/pipeline_output \
  prescription-processor
```

## Data Flow

```
Input Image
    ↓
File Upload (Web/CLI)
    ↓
ocr_processor.py
  └─ Surya OCR
    ↓
results.json (Intermediate)
    ↓
main.py (Your LLM)
  └─ Gemini Flash 2.5
    ↓
prescription_result.json (Final)
    ↓
User Response
```

## Output Structure

```
pipeline_output/
├── prescription_result.json      # Final structured output
└── ocr/
    ├── results.json             # Raw OCR results
    └── input_images/            # Copied input files
        ├── prescription1.png
        ├── prescription2.png
        └── ...
```

## Result JSON Format

### Success Response
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

### Error Response
```json
{
  "status": "reupload_required",
  "message": "Insufficient or ambiguous data. Please upload a clearer image.",
  "data": null
}
```

## Configuration

### Modify OCR Settings

Edit `ocr_processor.py`:

```python
cmd = [
    "surya_ocr",
    str(temp_input),
    "--output_dir", str(output_dir),
    "--task_name", "ocr_with_boxes",  # Change to "ocr" for faster processing
    "--images",
    "--disable_math",
]
```

### Modify LLM Behavior

Edit `main.py` - change `MASTER_PROMPT`:

```python
MASTER_PROMPT = """
You are a strict eyeglass prescription parser.

[Customize your rules here]
"""
```

### Modify Web Server

Edit `app.py`:

```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # Change max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', ...}  # Add/remove formats

app.run(debug=False, port=5000)  # Change port, disable debug for production
```

## Advanced Usage

### Custom Pipeline Class

```python
from pipeline import PrescriptionPipeline

class MyCustomPipeline(PrescriptionPipeline):
    def _run_llm(self):
        # Custom logic here
        result = super()._run_llm()
        # Post-process result
        return result
```

### Batch Processing Script

```python
from pipeline import process_prescriptions
from pathlib import Path

images = list(Path('./prescriptions').glob('*.png'))
result = process_prescriptions([str(img) for img in images])
```

### Error Handling

```python
from pipeline import PrescriptionPipeline
from pathlib import Path

try:
    pipeline = PrescriptionPipeline()
    result = pipeline.process_images(['prescription.png'])
    
    if result['status'] == 'ok':
        print(f"Extracted: {result['data']}")
    else:
        print(f"Error: {result['message']}")
        
except FileNotFoundError as e:
    print(f"Image not found: {e}")
except Exception as e:
    print(f"Processing error: {e}")
```

## Troubleshooting

### Issue: "surya_ocr command not found"
```bash
pip install surya-ocr --upgrade
```

### Issue: "GEMINI_API_KEY not set"
```bash
export GEMINI_API_KEY="your-key"
python app.py  # Restart after setting env var
```

### Issue: Port 5000 already in use
```bash
# Option 1: Kill the process
lsof -ti:5000 | xargs kill -9

# Option 2: Use different port
python -c "
from app import app
app.run(port=5001)
"
```

### Issue: OCR not recognizing text
- Ensure images are clear and well-lit
- Try higher resolution images
- Verify prescription is fully visible in image
- Check image format is supported (PNG, JPG, etc.)

### Issue: LLM API errors
- Verify GEMINI_API_KEY is correct
- Check API quota isn't exceeded
- Ensure network connection is stable
- Review API response in console output

### Issue: Slow processing
- Reduce image resolution
- Disable debug mode in Flask
- Use production WSGI server (gunicorn)

## Performance Optimization

### For Web Server

```bash
# Install gunicorn for production
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### For OCR Processing

In `ocr_processor.py`, enable GPU if available:

```python
# For NVIDIA GPU
cmd = [
    "surya_ocr",
    str(temp_input),
    "--output_dir", str(output_dir),
    "--cuda",  # Add this
    "--task_name", "ocr_with_boxes",
    "--images",
    "--disable_math",
]
```

### For LLM Calls

Cache results to avoid reprocessing:

```python
results_cache = {}

def get_cached_result(image_path):
    if image_path in results_cache:
        return results_cache[image_path]
    return None
```

## Deployment Checklist

- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] API key set: `export GEMINI_API_KEY="..."`
- [ ] Setup verified: `python test_setup.py`
- [ ] Web interface tested: `python app.py`
- [ ] Example image processed successfully
- [ ] Output JSON validated
- [ ] HTTPS/Security configured (if cloud deployment)
- [ ] Logging configured
- [ ] Backup strategy planned

## Monitoring and Logging

```bash
# View Flask logs
python app.py 2>&1 | tee pipeline.log

# Check pipeline output
cat pipeline_output/prescription_result.json | python -m json.tool

# Monitor Docker container
docker-compose logs -f prescription-processor
```

## Next Steps

1. **Test the web interface:**
   ```bash
   python app.py
   ```

2. **Upload a prescription image** and verify results

3. **Customize** as needed:
   - Modify extraction rules in `main.py`
   - Adjust OCR settings in `ocr_processor.py`
   - Extend with custom logic

4. **Deploy** using Docker:
   ```bash
   docker-compose up -d
   ```

5. **Monitor and maintain:**
   - Check logs regularly
   - Monitor API usage
   - Keep dependencies updated

## Support and Documentation

- **Quick Start**: See `QUICKSTART.md`
- **Full Docs**: See `README.md`
- **Code Examples**: See `examples.py`
- **Configuration**: See `.env.example`

## Files Reference

| File | Purpose |
|------|---------|
| main.py | LLM processor (your original code) |
| ocr_processor.py | Surya OCR wrapper |
| pipeline.py | Main orchestrator |
| app.py | Flask web server |
| templates/index.html | Web UI |
| requirements.txt | Python dependencies |
| test_setup.py | Verification script |
| examples.py | Usage examples |
| Dockerfile | Container definition |
| docker-compose.yml | Multi-container setup |
| README.md | Full documentation |
| QUICKSTART.md | Quick reference |
| .env.example | Configuration template |

Your complete prescription processing pipeline is ready for production! 🚀
