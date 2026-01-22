# Main.py Output Flow - Visual Guide

## What You'll See When Running the Pipeline

### Before: Old Output (Confusing)
```
{
  "status": "ok",
  "message": "...",
  "data": {
    "right_eye": null,  ← Everything null! What went wrong?
    "left_eye": null,
    ...
  }
}
```

### After: New Output (Clear & Diagnostic)

```
============================================================
STEP 1: OCR TEXT (RAW, BEFORE LLM PROCESSING)
============================================================
SPH CYL AXIS ADD
OD -1.00 -0.75 180 +2.50
OS -0.50 -1.25 175 +2.50
PD: 62/60
Dr. Smith
Date: 12/15/2024

============================================================
OCR CONFIDENCE SCORES (Sample)
============================================================
Average Confidence: 0.891
Total OCR Lines: 6

First 10 lines with confidence:
  1. [0.956] SPH CYL AXIS ADD
  2. [0.923] OD -1.00 -0.75 180 +2.50
  3. [0.874] OS -0.50 -1.25 175 +2.50
  4. [0.852] PD: 62/60
  5. [0.901] Dr. Smith
  6. [0.920] Date: 12/15/2024

============================================================
STEP 2: LLM PROCESSING (EXTRACTING STRUCTURED DATA)
============================================================

============================================================
FINAL RESULT (JSON)
============================================================
{
  "status": "ok",
  "message": "Successfully extracted prescription data",
  "data": {
    "right_eye": {
      "sphere": "-1.00",
      "cylinder": "-0.75",
      "axis": "180",
      "add": "+2.50"
    },
    "left_eye": {
      "sphere": "-0.50",
      "cylinder": "-1.25",
      "axis": "175",
      "add": "+2.50"
    },
    "pupillary_distance": "62/60",
    "doctor_name": "Dr. Smith",
    "date": "12/15/2024"
  },
  "diagnostics": {
    "uncertain_fields": [],
    "reasons": {},
    "confidence": "high",
    "ocr_confidence_scores": {
      "average": 0.891,
      "samples": [
        {"text": "SPH CYL AXIS ADD", "confidence": 0.956},
        {"text": "OD -1.00 -0.75 180 +2.50", "confidence": 0.923},
        {"text": "OS -0.50 -1.25 175 +2.50", "confidence": 0.874},
        {"text": "PD: 62/60", "confidence": 0.852},
        {"text": "Dr. Smith", "confidence": 0.901},
        {"text": "Date: 12/15/2024", "confidence": 0.920}
      ]
    }
  }
}
```

## Key Improvements Highlighted

### 1. **Raw OCR Visibility**
You can now see EXACTLY what the OCR engine extracted before Gemini processes it. This helps debug OCR quality issues.

### 2. **Confidence Scores**
- **OCR Confidence**: Shows how confident the OCR was (0.0-1.0)
- **LLM Confidence**: Shows how certain the extraction is (high/medium/low)
- **Average Score**: Quick metric of overall OCR quality (0.891 = 89.1% confident)

### 3. **Diagnostic Information**
```json
"ocr_confidence_scores": {
  "average": 0.891,        ← Overall quality metric
  "samples": [             ← Real data with confidence
    {"text": "...", "confidence": 0.956}
  ]
}
```

### 4. **Reduced "Going Crazy" Problem**
The new MASTER_PROMPT is:
- ✅ More concise (fewer instructions to confuse the LLM)
- ✅ Clearer priority (extract → validate → mark uncertain)
- ✅ Less demanding (allows LLM to be more flexible)
- ✅ Focuses on what's important (extraction over verbosity)

## How to Interpret the Output

| Scenario | What to Look For |
|----------|-----------------|
| **Perfect extraction** | `status: "ok"`, high confidence scores, no uncertain_fields |
| **Good but uncertain** | `status: "needs_review"`, some fields in uncertain_fields, medium confidence |
| **Bad OCR** | Low average OCR confidence (< 0.6), many null values |
| **Should reupload** | `status: "reupload_required"`, low confidence scores, OCR avg < 0.3 |

## Troubleshooting Guide

### Problem: Fields are null
**Check**: OCR confidence scores in the output
- **High OCR confidence (>0.8)** → LLM issue (try rephrasing MASTER_PROMPT)
- **Low OCR confidence (<0.6)** → Image quality issue (reupload clearer image)

### Problem: Extraction is wrong
**Check**: Diagnostics → uncertain_fields and reasons
- Shows which fields the system flagged as unreliable
- Explains why (e.g., "OD/OS association ambiguous")

### Problem: Want to see what changed
**Compare**: 
- STEP 1: Raw OCR text
- FINAL RESULT: Extracted data
- See exactly how Gemini interpreted the OCR

## Next Steps

1. **Upload a prescription image** via http://localhost:5000
2. **Check STEP 1** to verify OCR quality
3. **Check confidence scores** to understand reliability
4. **Review FINAL RESULT** to see extracted data
5. **If fields are wrong**, check the diagnostics for reasons

You now have full transparency into the entire pipeline! 🎯
