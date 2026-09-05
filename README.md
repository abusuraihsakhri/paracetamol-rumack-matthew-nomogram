# Paracetamol Rumack Matthew Nomogram

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** Standard Clinical Formulations & ISO/IEC Quality Frameworks

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

Rumack-Matthew Nomogram for Acetaminophen Toxicity. Evaluates 4-to-24 hour post-ingestion acetaminophen serum levels against the 150 mcg/mL treatment line for N-acetylcysteine (NAC).

Python implementation with single and batch evaluation modes, FastAPI REST API, and enterprise-grade security features.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## Key Capabilities & Algorithmic Modules

### Analytical Functions

- **`calculate_metrics()`** — Core scoring algorithm with input validation (rejects NaN/Infinity/empty values)
- **`process_single()`** — Evaluate a single case via CLI
- **`process_batch()`** — Process CSV batches with path validation and error handling
- **`main()`** — CLI entry point

### Enterprise Security

- **Zero-PHI Outbound Interceptor** — AST and regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers
- **Tamper-Evident HMAC-SHA256 Audit Trail** — Chained, cryptographically signed logs for every evaluation
- **Path Traversal Protection** — Input/output file paths validated for null bytes and resolved safely

### REST API (FastAPI)

- `GET /health` — Health check
- `GET /metrics` — Operational metrics
- `POST /api/audit` — Submit task for evaluation
- `POST /api/chat` — Supervisory chat query
- `GET /api/audit/logs` — Retrieve and verify audit trail

---

## Installation

```bash
pip install -e .
```

For development with testing:
```bash
pip install -e ".[dev]"
```

---

## CLI Quickstart & Usage

### 1. Single Case Evaluation
```bash
python rumack_matthew.py single --v1 14.5 --v2 4.2 --v3 1.8
```

### 2. Batch CSV Processing
```bash
python rumack_matthew.py batch -i sample.csv -o results.csv
```

### 3. Enterprise CLI (with audit trail)
```bash
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
```

### 4. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--v1` — Primary measurement (default: 10.0)
- `--v2` — Secondary parameter (default: 5.0)
- `--v3` — Tertiary parameter (default: 2.0)

### Input Data Schema (CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary measurement | Required |
| `v2` | Secondary parameter | Required |
| `v3` | Tertiary parameter | Required |

---

## Testing

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## Security Configuration

Set the audit secret key via environment variable for production:

```bash
export AUDIT_SECRET_KEY="your-secure-random-key"
```

If not set, a cryptographically secure random key is generated per process (suitable for development/testing, but audit trail verification will not persist across restarts).

---

## Container Deployment

```bash
docker build -t paracetamol-rumack-matthew-nomogram .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secure-key paracetamol-rumack-matthew-nomogram
```

Or with Docker Compose:

```bash
docker-compose up -d
```
