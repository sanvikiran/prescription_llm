# Quick Reference: Updated Main.py

## What Changed?

### ✅ **New Functions Added**
```python
extract_ocr_with_confidence(path)
```
Extracts OCR text + confidence scores for diagnostic display.

### ✅ **Modified Functions**
```python
call_gemini(ocr_text, ocr_data=None)
```
Now accepts optional OCR confidence data and includes it in diagnostics.

### ✅ **New Display Logic**
When you run `main.py` or use the pipeline, you now see:

1. **Raw OCR Output** - Exactly what OCR extracted
2. **Confidence Scores** - How confident the OCR was (per line + average)
3. **LLM Processing** - Status message
4. **Final JSON** - With confidence scores embedded in diagnostics

## MASTER_PROMPT Changes

### Before (Verbose - 180+ lines)
```
PHASE 1 — PERMISSIVE EXTRACTION
====================
PHASE 2 — VALIDATION & EXPLANATION
====================
[Multiple large sections...]
```

### After (Concise - ~50 lines)
```
EXTRACTION RULES:
- Extract ALL visible prescription values
- Fix obvious OCR errors
- If ambiguous, extract it anyway and note as uncertain

OUTPUT RULES:
- Return ONLY valid JSON
- For missing values, use null
- Mark uncertain extractions in "uncertain_fields"

STATUS RULES:
[Simple, clear guidance]
```

**Result**: LLM is less likely to "go crazy" and null out everything.

## JSON Output Structure

### Before
```json
{
  "status": "ok",
  "message": "...",
  "data": {...},
  "diagnostics": {
    "uncertain_fields": [],
    "reasons": {},
    "confidence": "high"
  }
}
```

### After
```json
{
  "status": "ok",
  "message": "...",
  "data": {...},
  "diagnostics": {
    "uncertain_fields": [],
    "reasons": {},
    "confidence": "high",
    "ocr_confidence_scores": {          ← NEW!
      "average": 0.891,
      "samples": [
        {"text": "...", "confidence": 0.92},
        ...
      ]
    }
  }
}
```

## Console Output Example

```
============================================================
STEP 1: OCR TEXT (RAW, BEFORE LLM PROCESSING)
============================================================
SPH CYL AXIS ADD
OD -1.00 -0.75 180...
[Shows raw OCR exactly as extracted]

============================================================
OCR CONFIDENCE SCORES (Sample)
============================================================
Average Confidence: 0.891
[Shows confidence metrics]

============================================================
STEP 2: LLM PROCESSING (EXTRACTING STRUCTURED DATA)
============================================================

============================================================
FINAL RESULT (JSON)
============================================================
[Shows final extracted data with confidence embedded]
```

## How to Use

### CLI (Direct Python)
```bash
python main.py
# Reads from results.json, shows all 3 output stages, prints JSON
```

### Pipeline (Multi-image)
```bash
python pipeline.py prescription.png
# Runs full pipeline with OCR confidence display
```

### Web Interface
```
http://localhost:5000
# Upload image → see all 3 stages → get JSON with confidence
```

## Key Benefits

| Feature | Before | After |
|---------|--------|-------|
| **OCR Quality Visible** | ❌ No | ✅ Yes (confidence scores) |
| **Raw Output Visible** | ❌ Only LLM output | ✅ Both raw & processed |
| **Confidence Data** | ❌ None | ✅ Included in JSON |
| **Verbose Errors** | ✅ Many nulls | ❌ Lighter, smarter |
| **Debugging** | 😞 Hard | 😊 Easy |
| **Transparency** | ❌ Black box | ✅ Full visibility |

## Confidence Score Interpretation

```
0.90-1.00  → Excellent (high confidence)
0.70-0.89  → Good (medium confidence)
0.50-0.69  → Fair (needs review)
< 0.50     → Poor (consider reupload)
```

Apply this to both:
- **OCR confidence** (in STEP 1 output)
- **LLM confidence** (in diagnostics → confidence field)

## Files Modified

- ✅ `main.py` - Core improvements (3 changes)
- ✅ `pipeline.py` - Integration update (1 change)
- 📄 `IMPROVEMENTS.md` - Detailed explanation (NEW)
- 📄 `OUTPUT_FORMAT_GUIDE.md` - Visual guide (NEW)

---

**Need to set up?** Run: `export GEMINI_API_KEY="your-key-here"`
**Want to test?** Upload a prescription image at http://localhost:5000
