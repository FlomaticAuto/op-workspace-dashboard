# Olympic Paints — Returns Manager

Streamlit dashboard for end-to-end factory returns management.
Scan intake → OCR review → rework lifecycle → supervisor reports.

**Live app:** deploy via Streamlit Cloud (see below)

---

## Pages

| Page | Purpose |
|---|---|
| Dashboard | KPI overview, charts |
| Review Scan | Correct OCR-flagged product names |
| Batch Tracker | Update rework status (Pending → Completed) |
| Deliveries | Full truck arrival log |
| Corrections Library | Product name learning dictionary |
| Reports | Generate & download supervisor reports |

---

## Local setup

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd returns-manager

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure supervisors (copy the example and edit)
cp supervisor_config.example.json supervisor_config.json
# edit supervisor_config.json with real names and emails

# 4. Run the app
streamlit run scripts/returns_app.py
```

The `Returns_Database.xlsx` file is committed as a seed database.
New data entered via the app is written to this file on your local machine.

---

## Streamlit Cloud deployment

1. Push this repo to GitHub (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select your repo, branch (`main`), and set **Main file path** to:
   ```
   scripts/returns_app.py
   ```
4. Click **Deploy**.

> **Note:** Streamlit Cloud has ephemeral storage. Data written by the app (new deliveries, batch updates) will not persist between restarts. For production use, migrate the database to a persistent store such as Supabase or Google Sheets.

> **Email sending** (`Generate & Email Reports`) uses Windows Outlook via `win32com` and will not work on Streamlit Cloud. Use **Generate (no email)** on cloud.

---

## Ingesting a new scan (local only)

```bash
cd scripts
python ingest_returns_scan.py path/to/scan.pdf
```

Requires an `ANTHROPIC_API_KEY` environment variable set to a valid API key.
The ingest script uses Claude Opus for handwriting OCR.

---

## File structure

```
.
├── .streamlit/
│   └── config.toml          # Theme colours for Streamlit Cloud
├── scripts/
│   ├── returns_app.py       # Streamlit entry point
│   ├── returns_db.py        # Database schema and CRUD operations
│   ├── generate_reports.py  # HTML + Word supervisor reports
│   ├── review_scan.py       # CLI amendment tool
│   └── ingest_returns_scan.py # PDF OCR via Claude API
├── Returns_Database.xlsx    # Seed database (openpyxl-managed)
├── product_corrections.json # OCR learning library
├── supervisor_config.example.json
├── requirements.txt
└── README.md
```
