# Paracetamol Rumack–Matthew Nomogram

A reference implementation of the US/Canada acetaminophen/paracetamol **150 µg/mL treatment line**, including a standalone browser interface, Python single-case and batch calculator, and FastAPI endpoint.

> **Clinical safety:** This project has not undergone clinical validation and is not a medical device. It must not be the sole basis of treatment. For suspected poisoning, immediately contact emergency services or a poison center; do not delay N-acetylcysteine pending a calculation.

## Browser application

Open [web/index.html](web/index.html) in a modern browser, or start a local web server using:

    python -m http.server 8080 -d web

Then visit http://localhost:8080. Enter elapsed time from the start of ingestion and the measured acetaminophen concentration, verify the history, and evaluate. A logarithmic nomogram plot displays eligible points. Results can be exported as CSV.

The browser application runs entirely in JavaScript: no Python, backend, cookies, external network requests, browser storage or clinical identifiers are required. Do not enter patient information. A GitHub Pages workflow is included; a live URL will be published here only after deployment has been verified.

## Model and applicability

For an **acute ingestion completed within 24 hours**, with reliably known start time and a serum level sampled at **4–24 hours**, the 150-line is:

    threshold (µg/mL) = 150 × 2 ^ (−(hours − 4) / 4)

Reference thresholds: 4 h = 150; 8 h = 75; 12 h = 37.5; 16 h = 18.75; 20 h = 9.375; 24 h = 4.6875 µg/mL. Concentrations on or above the line are classified at/above the treatment line. The tool provides no automatic treatment order.

The nomogram is **not applicable** with unknown/unreliable timing, repeated supratherapeutic ingestion spanning more than 24 h, modified-release products, or samples outside 4–24 hours. Extended-release formulations and opioid/anticholinergic coingestions can result in delayed absorption and require repeat levels. Below-line results do not independently exclude toxicity. Jurisdictions may use different thresholds (e.g. UK 100-line), so this implementation is specifically the US/Canada 150-line.

Primary reference: Dart RC et al. Management of Acetaminophen Poisoning in the US and Canada: A Consensus Statement. JAMA Network Open. 2023;6(8):e2327739. https://doi.org/10.1001/jamanetworkopen.2023.27739

## Python installation and CLI

Requires Python 3.10 or later.

    python -m pip install -e ".[dev]"
    python rumack_matthew.py single --hours 8 --concentration 75
    python rumack_matthew.py single --hours 8 --concentration 20 --pattern repeated
    python rumack_matthew.py batch -i sample.csv -o results.csv

The installed CLI command is paracetamol-nomogram. CSV input requires columns hours_post_ingestion and concentration_mcg_ml. Optional columns: ingestion_pattern, time_known and delayed_absorption (true/false). Invalid rows stop batch processing without overwriting an existing output file. Do not include identifiers or personal health information.

## FastAPI and legacy utilities

    python cli.py serve --host 127.0.0.1 --port 8000

For the clinical reference, POST JSON to /api/nomogram, for example:

    {"hours_post_ingestion": 8, "concentration_mcg_ml": 75, "ingestion_pattern": "acute"}

Interactive generated documentation: http://localhost:8000/docs. The separate legacy /api/audit, /api/chat, and /api/audit/logs endpoints remain for nonclinical demonstrations. Their arbitrary worker thresholds, mock chat text and regex-based PHI checks are **not** validated clinical logic or guaranteed de-identification. Do not expose the backend publicly without authentication, TLS and a security/privacy review.

Docker Compose requires a strong AUDIT_SECRET_KEY in the environment before running docker compose up --build; it does not ship with a default secret. The in-memory audit trail is not a durable medical record.

## Testing

    python -m pip install -e ".[dev]"
    python -m pytest -q
    python -m compileall -q rumack_matthew.py cli.py agents
    node --check web/nomogram.js
    node --test web/nomogram.test.cjs

CI covers Python 3.10–3.12 and Node.js 22. The static browser requires JavaScript and works without Pyodide.

## License

MIT. See [LICENSE](LICENSE).
