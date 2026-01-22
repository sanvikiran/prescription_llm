import json
import os
import requests
import re

# -----------------------------
# STEP 1: Read OCR text + confidence scores
# -----------------------------
def extract_ocr_text(path):
    with open(path, "r") as f:
        data = json.load(f)

    lines = []
    for image_name in data:
        for page in data[image_name]:
            for line in page.get("text_lines", []):
                text = line.get("text", "").strip()
                if text:
                    lines.append(text)

    return "\n".join(lines)


def extract_ocr_with_confidence(path):
    """Extract OCR text WITH confidence scores for diagnostics."""
    with open(path, "r") as f:
        data = json.load(f)
    
    ocr_data = []
    for image_name in data:
        for page in data[image_name]:
            for line in page.get("text_lines", []):
                text = line.get("text", "").strip()
                confidence = line.get("confidence", 0.0)
                if text:
                    ocr_data.append({
                        "text": text,
                        "confidence": round(confidence, 3)
                    })
    
    return ocr_data


# -----------------------------
# STEP 2: MASTER PROMPT (LIGHT & CLEAR)
# -----------------------------
MASTER_PROMPT = """
You are an eyeglass prescription extractor. Extract prescription values from OCR text.

IMPORTANT: The OCR text may be imperfect. Your job is to EXTRACT what you can, not discard.

EXTRACTION RULES:
1. Sphere: Look for SPH, S, or first column of numbers after OD/OS
   - Format: -X.XX to +X.XX (multiples of 0.25)
   - Examples: -1.25, +2.00, -0.50

2. Cylinder: Look for CYL, C, or second column of prescription numbers
   - Format: -X.XX (usually negative)
   - Only if present

3. Axis: Look for AXIS, AX, or 3-digit numbers (0-180)
   - Integer between 0 and 180
   - Only valid if cylinder is present

4. ADD (Reading Power): Look for ADD, +X.XX
   - Usually positive, typically 0.75 to 3.50

5. Pupillary Distance: Look for PD, spacing, or two-digit numbers (50-75)
   - Format: number or "OD/OS" (e.g., 62/60)

6. Doctor Name: Any name or title (Dr., Doctor, etc.)

7. Date: Any date format (convert to standardized format)

CRITICAL: 
- Fix common OCR errors: O→0, l→1, S→5, B→8
- If a value is present but malformed, EXTRACT IT with best guess
- Do NOT set to null unless completely missing
- Use spatial proximity: values close together = same field

Return ONLY this JSON:
{
  "status": "ok | needs_review | reupload_required",
  "message": "extraction summary",
  "data": {
    "right_eye": {"sphere": "value or null", "cylinder": "value or null", "axis": "value or null", "add": "value or null"},
    "left_eye": {"sphere": "value or null", "cylinder": "value or null", "axis": "value or null", "add": "value or null"},
    "pupillary_distance": "value or null",
    "doctor_name": "value or null",
    "date": "value or null"
  },
  "diagnostics": {
    "uncertain_fields": [],
    "reasons": {},
    "confidence": "high | medium | low"
  }
}

OCR TEXT TO PROCESS:
"""


# -----------------------------
# STEP 3: Gemini Flash 2.5 API Call
# -----------------------------
def call_gemini(ocr_text, ocr_data=None):
    api_key = os.environ["GEMINI_API_KEY"]

    url = (
        "https://generativelanguage.googleapis.com/v1/models/"
        "gemini-2.5-flash:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": MASTER_PROMPT + "\n\n" + ocr_text
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0
        }
    }

    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        params={"key": api_key},
        json=payload
    )

    if response.status_code != 200:
        raise RuntimeError(response.text)

    raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]

    # Safe JSON extraction
    match = re.search(r"\{.*\}", raw_text, re.S)
    if not match:
        raise RuntimeError("Model did not return a valid JSON object")

    result = json.loads(match.group())
    
    # Add OCR confidence scores to diagnostics
    if ocr_data:
        avg_confidence = sum([item['confidence'] for item in ocr_data]) / len(ocr_data) if ocr_data else 0
        result['diagnostics']['ocr_confidence_scores'] = {
            'average': round(avg_confidence, 3),
            'samples': ocr_data[:10]  # Show first 10 OCR lines with confidence
        }
    
    return result


# -----------------------------
# STEP 3B: Prescription Validation Rules
# -----------------------------
def validate_and_fix_prescription(result):
    """
    Validate prescription values against real-world constraints
    and attempt to fix invalid values
    
    Args:
        result: The LLM output dictionary
        
    Returns:
        Validated result with corrections noted in diagnostics
    """
    if result.get('data') is None:
        return result
    
    data = result.get('data', {})
    validation_notes = []
    
    # Helper function to check if value is multiple of 0.25
    def is_multiple_of_025(val):
        if val is None:
            return True
        try:
            num = float(val)
            return abs((num * 4) % 1) < 0.01  # Check if *4 is integer
        except (ValueError, TypeError):
            return False
    
    # Helper function to validate and fix sphere/cylinder
    def validate_sphere_cylinder(val, field_name):
        if val is None:
            return None, None
        
        try:
            num = float(val)
            
            # Check range
            if num < -20.00 or num > 20.00:
                validation_notes.append(f"{field_name} {num} out of range (-20 to +20)")
                return None, "out_of_range"
            
            # Check if multiple of 0.25
            if not is_multiple_of_025(num):
                # Try to round to nearest 0.25
                rounded = round(num * 4) / 4
                if abs(rounded - num) < 0.05:
                    validation_notes.append(f"{field_name} {num} rounded to {rounded}")
                    return rounded, "rounded"
                else:
                    validation_notes.append(f"{field_name} {num} not valid multiple of 0.25")
                    return None, "invalid"
            
            return num, "valid"
        except (ValueError, TypeError):
            validation_notes.append(f"{field_name} invalid format: {val}")
            return None, "invalid_format"
    
    # Validate each eye
    for eye in ['right_eye', 'left_eye']:
        if eye not in data or data[eye] is None:
            continue
        
        eye_data = data[eye]
        
        # Sphere
        sphere_val, sphere_status = validate_sphere_cylinder(eye_data.get('sphere'), f"{eye} sphere")
        if sphere_status != "valid":
            eye_data['sphere'] = sphere_val
        
        # Cylinder
        cyl_val, cyl_status = validate_sphere_cylinder(eye_data.get('cylinder'), f"{eye} cylinder")
        if cyl_status != "valid":
            eye_data['cylinder'] = cyl_val
        
        # Axis - only valid if cylinder is not 0
        axis_val = eye_data.get('axis')
        if axis_val is not None:
            try:
                axis_int = int(float(axis_val))
                cyl = eye_data.get('cylinder')
                
                # Check if cylinder is 0
                if cyl == 0 or (isinstance(cyl, (int, float)) and float(cyl) == 0):
                    validation_notes.append(f"{eye} axis invalid (cylinder is 0)")
                    eye_data['axis'] = None
                elif axis_int < 0 or axis_int > 180:
                    validation_notes.append(f"{eye} axis {axis_int} out of range (0-180)")
                    eye_data['axis'] = None
                else:
                    eye_data['axis'] = axis_int
            except (ValueError, TypeError):
                validation_notes.append(f"{eye} axis invalid format: {axis_val}")
                eye_data['axis'] = None
        
        # ADD Power
        add_val = eye_data.get('add')
        if add_val is not None:
            add_float, add_status = validate_sphere_cylinder(add_val, f"{eye} add")
            if add_float is not None:
                if add_float < 0:
                    validation_notes.append(f"{eye} add {add_float} should be positive")
                    eye_data['add'] = None
                elif add_float < 0.75 or add_float > 3.50:
                    validation_notes.append(f"{eye} add {add_float} outside typical range (0.75-3.50)")
                else:
                    eye_data['add'] = add_float
            else:
                eye_data['add'] = None
    
    # Validate Pupillary Distance (PD)
    pd_val = data.get('pupillary_distance')
    if pd_val is not None:
        try:
            # Extract numeric value (may contain "/" for OD/OS)
            pd_str = str(pd_val).strip()
            if '/' in pd_str:
                parts = pd_str.split('/')
                pd_nums = [float(p.strip()) for p in parts if p.strip()]
            else:
                pd_nums = [float(pd_str)]
            
            valid_pds = []
            for pd in pd_nums:
                if pd < 50 or pd > 75:
                    validation_notes.append(f"PD {pd} outside typical range (50-75mm)")
                else:
                    valid_pds.append(pd)
            
            if valid_pds:
                if len(valid_pds) > 1:
                    data['pupillary_distance'] = '/'.join([str(int(p)) for p in valid_pds])
                else:
                    data['pupillary_distance'] = int(valid_pds[0])
            else:
                data['pupillary_distance'] = None
        except (ValueError, TypeError):
            validation_notes.append(f"PD invalid format: {pd_val}")
            data['pupillary_distance'] = None
    
    # Validate Date - convert to ISO format YYYY-MM-DD
    date_val = data.get('date')
    if date_val is not None:
        from datetime import datetime
        date_str = str(date_val).strip()
        
        # Try common date formats
        date_formats = [
            '%m/%d/%Y', '%m-%d-%Y',  # MM/DD/YYYY
            '%d/%m/%Y', '%d-%m-%Y',  # DD/MM/YYYY
            '%Y/%m/%d', '%Y-%m-%d',  # YYYY/MM/DD
            '%m/%d/%y', '%m-%d-%y',  # MM/DD/YY
            '%d/%m/%y', '%d-%m-%y',  # DD/MM/YY
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if parsed_date:
            data['date'] = parsed_date.strftime('%Y-%m-%d')
        else:
            validation_notes.append(f"Date {date_val} could not be parsed to ISO format")
    
    # Add validation notes to diagnostics
    if 'diagnostics' not in result:
        result['diagnostics'] = {}
    
    result['diagnostics']['validation_notes'] = validation_notes
    result['diagnostics']['validation_status'] = "passed" if not validation_notes else "warnings"
    
    return result


# -----------------------------
# STEP 4: Run pipeline
# -----------------------------
if __name__ == "__main__":
    ocr_text = extract_ocr_text("results.json")
    ocr_data = extract_ocr_with_confidence("results.json")

    if not ocr_text.strip():
        result = {
            "status": "reupload_required",
            "message": "OCR text is empty. Please upload a clearer image.",
            "data": None,
            "diagnostics": {
                "uncertain_fields": [],
                "reasons": {},
                "confidence": "low"
            }
        }
        print(json.dumps(result, indent=2))
    else:
        # =====================
        # BEFORE LLM PROCESSING
        # =====================
        print("\n" + "="*60)
        print("STEP 1: OCR TEXT (RAW, BEFORE LLM PROCESSING)")
        print("="*60)
        print(ocr_text)
        print()
        
        print("="*60)
        print("OCR CONFIDENCE SCORES (Sample)")
        print("="*60)
        avg_confidence = sum([item['confidence'] for item in ocr_data]) / len(ocr_data) if ocr_data else 0
        print(f"Average Confidence: {round(avg_confidence, 3)}")
        print(f"Total OCR Lines: {len(ocr_data)}")
        print("\nFirst 10 lines with confidence:")
        for i, item in enumerate(ocr_data[:10], 1):
            print(f"  {i}. [{item['confidence']:.3f}] {item['text']}")
        print()
        
        # =====================
        # AFTER LLM PROCESSING
        # =====================
        print("="*60)
        print("STEP 2: LLM PROCESSING (EXTRACTING STRUCTURED DATA)")
        print("="*60)
        result = call_gemini(ocr_text, ocr_data)
        print()
        
        # =====================
        # STEP 3: VALIDATION
        # =====================
        print("="*60)
        print("STEP 3: VALIDATION & CORRECTION")
        print("="*60)
        result = validate_and_fix_prescription(result)
        if result.get('diagnostics', {}).get('validation_notes'):
            for note in result['diagnostics']['validation_notes']:
                print(f"  ⚠ {note}")
        else:
            print("  ✓ All values passed validation")
        print()
        
        print("="*60)
        print("FINAL RESULT (JSON)")
        print("="*60)
        print(json.dumps(result, indent=2))
