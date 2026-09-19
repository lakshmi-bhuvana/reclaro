# Reclaro ⚕️

**Reclaro** is an engineering platform that identifies potentially affected medical devices in hospital inventory datasets when an FDA medical-device recall notice is issued.

It fetches live recall notices directly from the public openFDA Device Recall API (`https://api.fda.gov/device/recall.json`), parses the scope parameters, normalizes inventory fields, and evaluates records using a **Deterministic Verification Engine**.

---

## 🎯 Authoritative Verification Rule

> **CRITICAL RULE**: The deterministic verification layer is the **FINAL AUTHORITY**.
> Rule/AI candidate matching can flag ambiguous records as `NEEDS_REVIEW`, but **ONLY** exact or range-verified rule signals (Catalog REF, UDI-DI, Model + Lot Range / Serial Range) can classify an item as `CONFIRMED`.

### Classification Statuses
* 🔴 **CONFIRMED**: Device matches the manufacturer, product line, and catalog/model parameters **AND** has verified lot, serial, or UDI-DI match in recall scope. Immediate quarantine required.
* 🟡 **NEEDS_REVIEW**: Device matches manufacturer and model/family patterns, but lot number or serial number verification is pending or missing. Flagged for biomedical inspection.
* 🟢 **NOT_AFFECTED**: Device does not match manufacturer or product line specifications defined in the recall notice. Safe for clinical operation.

---

## 📁 Repository Structure

```
recallmatch/
├── backend/
│   ├── api/
│   │   └── main.py              # FastAPI endpoints (/api/recalls, /api/match, /api/health)
│   ├── models/
│   │   └── schemas.py           # Pydantic models (Recall, NormalizedRecall, InventoryItem, MatchResult)
│   ├── services/
│   │   ├── fda/                 # openFDA live client & fallback dataset
│   │   ├── recall_parser/       # Extracts models, catalog REF, UDI-DI, lot/serial ranges
│   │   ├── normalization/       # Text & legal entity suffix normalizer
│   │   ├── matching/            # Signal & candidate generator
│   │   ├── verification/        # Authoritative deterministic verification engine
│   │   └── evidence/            # Diagnostic evidence builder & action recommendations
│   └── tests/                   # Pytest unit test suite
├── data/
│   └── synthetic_inventory/
│       └── hospital_inventory_sample.csv   # Realistic synthetic test inventory dataset
├── frontend/
│   ├── src/
│   │   ├── components/          # Header, RecallSelector, InventoryUploader, StatsOverview, MatchResultsTable, EvidenceModal
│   │   ├── pages/               # Dashboard workspace
│   │   ├── services/            # API client layer
│   │   ├── types/               # TypeScript interfaces matching backend models
│   │   ├── index.css            # Custom glassmorphism UI & status badge styling
│   │   ├── main.tsx
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── .env.example
├── requirements.txt
└── README.md
```

---

## ⚡ Instructions for Running Locally

### 1. Backend Setup (FastAPI / Python)

Make sure Python 3.10+ is installed on your system.

```bash
# Navigate to project directory
cd C:\Users\HP\.gemini\antigravity-ide\scratch\recallmatch

# Install backend dependencies
pip install -r requirements.txt

# Run FastAPI backend server
uvicorn backend.api.main:app --reload --port 8000
```

The backend server will start at: `http://127.0.0.1:8000`  
API Interactive Docs (Swagger): `http://127.0.0.1:8000/docs`

### 2. Frontend Setup (React / Vite / TypeScript)

Make sure Node.js 18+ is installed.

```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```

The React dashboard will be available at: `http://localhost:5173`

---

## 🧪 Running Unit Tests

Run the complete Pytest backend test suite covering schemas, normalizers, recall scope parsing, candidate signal generation, and deterministic verification rules:

```bash
# Run pytest from project root
pytest backend/tests -v
```

---

## 🔒 Product Boundaries & Disclaimers

* **No Manual Recall PDF Upload**: Directly queries openFDA REST API.
* **No Patient Data**: Does not perform patient-level matching or handle PHI.
* **No Clinical Decisions**: Software flags medical inventory hardware; does not make clinical diagnostic decisions.
* **Not FDA Certified**: Designed as a hackathon engineering prototype.
