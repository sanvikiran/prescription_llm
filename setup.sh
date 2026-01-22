#!/bin/bash

# Quick Start Script for Prescription Processing Pipeline

set -e

echo "=================================================="
echo "Prescription Processing Pipeline - Setup"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY environment variable is not set"
    echo "   Set it with: export GEMINI_API_KEY='your-api-key'"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Check if surya_ocr is available
echo ""
echo "Verifying Surya OCR installation..."
if ! python3 -c "import surya" 2>/dev/null; then
    echo "⚠️  Surya OCR not fully initialized. This is normal on first install."
    echo "   It will be initialized on first use."
fi

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Choose how to use the pipeline:"
echo ""
echo "1. WEB INTERFACE (Recommended for beginners)"
echo "   $ python app.py"
echo "   Then open http://localhost:5000"
echo ""
echo "2. COMMAND LINE"
echo "   $ python pipeline.py /path/to/prescription.png"
echo ""
echo "3. PYTHON MODULE"
echo "   from pipeline import process_prescription"
echo "   result = process_prescription('image.png')"
echo ""
echo "For more information, see README.md"
echo "=================================================="
