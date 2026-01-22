"""
Flask Web Interface for Prescription Processing Pipeline
Upload images → OCR → LLM → Download result
"""

from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import json
import os
from werkzeug.utils import secure_filename
import tempfile
from io import BytesIO

from pipeline import PrescriptionPipeline

# Initialize Flask app
app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "prescription_uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff', 'tif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the upload page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle image upload and process through pipeline
    
    Returns:
        JSON with prescription data or error message
    """
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Validate and save uploaded files
        uploaded_paths = []
        errors = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = app.config['UPLOAD_FOLDER'] / filename
                file.save(filepath)
                uploaded_paths.append(filepath)
            elif file:
                errors.append(f"Invalid file type: {file.filename}")
        
        if not uploaded_paths:
            error_msg = '; '.join(errors) if errors else 'No valid image files'
            return jsonify({'error': error_msg}), 400
        
        # Process through pipeline
        output_dir = app.config['UPLOAD_FOLDER'] / "pipeline_results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pipeline = PrescriptionPipeline(output_dir)
        result = pipeline.process_images([str(p) for p in uploaded_paths])
        
        # Clean up uploaded files
        for path in uploaded_paths:
            try:
                path.unlink()
            except:
                pass
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Prescription Processing Pipeline'
    })


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'error': f'File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB'
    }), 413


if __name__ == '__main__':
    app.run(debug=True, port=5000)
