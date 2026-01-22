# Code Changes Summary

## Changes to main.py

### Addition #1: New Function - OCR with Confidence
```python
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
```

**Purpose**: Extracts OCR text + confidence scores (EasyOCR provides these in results.json)

---

### Change #2: MASTER_PROMPT Simplified

**BEFORE** (180+ lines, many sections):
```python
MASTER_PROMPT = """
You are an eyeglass prescription extraction system working on noisy OCR text.

IMPORTANT: The OCR text is assumed to be COMPLETE.
Your job is to PRESERVE information, not discard it.

====================
PHASE 1 — PERMISSIVE EXTRACTION
====================
First, extract ALL prescription-related values that plausibly appear in the text.

You MAY:
- Fix obvious OCR character errors (~→-, O/o→0, ,→.)
- Normalize spacing and line breaks
- Use spatial proximity and typical prescription layout conventions
- Associate values with OD / OS / right / left when reasonably implied

DO NOT:
- Invent values that do not exist
- Introduce values not supported by text

[... many more paragraphs ...]
"""
```

**AFTER** (~50 lines, focused):
```python
MASTER_PROMPT = """
You are an eyeglass prescription extractor. Extract prescription values from OCR text.

EXTRACTION RULES:
- Extract ALL visible prescription values (sphere, cylinder, axis, add, pupillary distance, doctor, date)
- Fix obvious OCR errors (~→-, O→0, ,→.)
- If ambiguous, extract it anyway and note as uncertain in diagnostics
- Do NOT invent values that don't appear in the text
- Use spatial layout to infer OD/OS associations when unclear

OUTPUT RULES:
- Return ONLY valid JSON (no markdown, no extra text)
- For missing values, use null
- Mark uncertain extractions in "uncertain_fields" list with brief reason

STATUS RULES:
- "ok": Most core fields extracted successfully
- "needs_review": Values extracted but some associations unclear
- "reupload_required": OCR text is too degraded to extract reliably

Return this JSON structure exactly:
[JSON structure shown]

OCR TEXT TO PROCESS:
"""
```

**Result**: Less verbose = LLM less confused = fewer null values

---

### Change #3: Updated call_gemini() Signature
```python
# BEFORE
def call_gemini(ocr_text):
    ...

# AFTER
def call_gemini(ocr_text, ocr_data=None):
    ...
    # Add OCR confidence scores to diagnostics
    if ocr_data:
        avg_confidence = sum([item['confidence'] for item in ocr_data]) / len(ocr_data) if ocr_data else 0
        result['diagnostics']['ocr_confidence_scores'] = {
            'average': round(avg_confidence, 3),
            'samples': ocr_data[:10]  # Show first 10 OCR lines with confidence
        }
    
    return result
```

**Purpose**: Accepts OCR confidence data and embeds it in the JSON output

---

### Change #4: New Pipeline Execution with Display

**BEFORE**:
```python
if __name__ == "__main__":
    ocr_text = extract_ocr_text("results.json")

    if not ocr_text.strip():
        print(json.dumps({...}, indent=2))
    else:
        result = call_gemini(ocr_text)
        print(json.dumps(result, indent=2))
```

**AFTER**:
```python
if __name__ == "__main__":
    ocr_text = extract_ocr_text("results.json")
    ocr_data = extract_ocr_with_confidence("results.json")

    if not ocr_text.strip():
        result = {...}
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
        
        print("="*60)
        print("FINAL RESULT (JSON)")
        print("="*60)
        print(json.dumps(result, indent=2))
```

**Purpose**: Shows 3 distinct stages with confidence metrics before LLM processes

---

## Changes to pipeline.py

### Update: Enhanced _run_llm() Method

**BEFORE**:
```python
def _run_llm(self) -> dict:
    try:
        ocr_text = llm_module.extract_ocr_text(str(self.results_json_path))
        
        if not ocr_text.strip():
            return {...}
        
        print(f"  ✓ Extracted {len(ocr_text)} characters from OCR")
        print("  → Calling Gemini API...")
        result = llm_module.call_gemini(ocr_text)
        
        if "status" not in result or "data" not in result:
            raise ValueError("Invalid LLM response format")
        
        print(f"  ✓ LLM processing complete (status: {result['status']})")
        return result
```

**AFTER**:
```python
def _run_llm(self) -> dict:
    try:
        # Extract OCR text and confidence data
        ocr_text = llm_module.extract_ocr_text(str(self.results_json_path))
        ocr_data = llm_module.extract_ocr_with_confidence(str(self.results_json_path))
        
        if not ocr_text.strip():
            return {...}
        
        print(f"  ✓ Extracted {len(ocr_text)} characters from OCR")
        
        # Calculate and display OCR confidence
        if ocr_data:
            avg_confidence = sum([item['confidence'] for item in ocr_data]) / len(ocr_data)
            print(f"  ✓ OCR Confidence Score: {round(avg_confidence, 3)}")
        
        # Call Gemini with OCR data
        print("  → Calling Gemini API...")
        result = llm_module.call_gemini(ocr_text, ocr_data)
        
        if "status" not in result or "data" not in result:
            raise ValueError("Invalid LLM response format")
        
        print(f"  ✓ LLM processing complete (status: {result['status']})")
        return result
```

**Improvements**:
- Extracts OCR confidence data
- Displays OCR confidence score during pipeline run
- Passes OCR data to Gemini for inclusion in output

---

## Summary of Code Changes

| File | Type | Size | Impact |
|------|------|------|--------|
| main.py | Addition | +40 lines | `extract_ocr_with_confidence()` function |
| main.py | Modification | ~130 lines | MASTER_PROMPT simplified + display logic |
| main.py | Signature | 1 line | `call_gemini()` now accepts `ocr_data` |
| pipeline.py | Enhancement | ~6 lines | `_run_llm()` now calculates and displays confidence |

**Total Changes**: ~180 lines modified/added across 2 files

---

## Backward Compatibility

✅ **Fully backward compatible**:
- Old code calling `call_gemini(ocr_text)` still works (ocr_data defaults to None)
- No breaking changes to function signatures
- Can be used in existing code without modification

---

## Testing

All changes tested for:
- ✅ Syntax correctness (Python 3.9)
- ✅ Logic correctness
- ✅ Integration with existing code
- ✅ Backward compatibility

Ready for production use!
