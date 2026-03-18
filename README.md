# 🇹🇳 Tunisia Jobs Tracker

A Python web scraping pipeline that collects job listings from major Tunisian job boards, stores them in a structured database, and visualizes the data through an interactive dashboard.

🔗 **Live Demo:** [tn-jobs-tracker.streamlit.app](https://tn-jobs-tracker.streamlit.app/)

---

## 📊 Dashboard Preview

> Built with Streamlit — filters by city, contract type, and source.

---

## 🗂️ Data Sources

| Source | Pages | Status |
|--------|-------|--------|
| [farojob.net](https://www.farojob.net) | 782 | ✅ Active |
| [keejob.com](https://www.keejob.com) | ~100 | ✅ Active |
| [offre-emploi.tn](https://www.offre-emploi.tn) | 43 | ✅ Active |

---

## 🏗️ Project Structure
```
tunisia-jobs-tracker/
├── scrapers/
│   ├── base_scraper.py       # Shared base class (session, rate limiting, logging)
│   ├── farojob.py            # Scraper for farojob.net
│   ├── keejob.py             # Scraper for keejob.com
│   └── offre_emploi_tn.py    # Scraper for offre-emploi.tn
├── processing/
│   └── cleaner.py            # Data cleaning + city normalization + CSV export
├── database/
│   └── db.py                 # SQLite + migration system
├── dashboard/
│   └── app.py                # Streamlit interactive dashboard
├── data/
│   └── jobs_cleaned.csv      # Latest scraped data (auto-updated daily)
├── .github/workflows/
│   └── scrape.yml            # GitHub Actions — runs scrapers daily at 6AM UTC
├── .env.example              # Environment template
└── requirements.txt
```

---

## ⚙️ Tech Stack

- **Python 3.12**
- **requests + BeautifulSoup4** — HTML parsing
- **SQLite** — lightweight local database with migration system
- **pandas** — data cleaning and normalization
- **Streamlit** — interactive dashboard
- **GitHub Actions** — daily automated scraping
- **python-dotenv** — environment configuration

---

## 🚀 Getting Started

> **Windows users:** This project was developed and tested on **WSL (Windows Subsystem for Linux)** with Ubuntu. It is strongly recommended to run it inside WSL rather than native Windows to avoid path and encoding issues.
>
> To enable WSL: `wsl --install` in PowerShell, then follow the [official guide](https://learn.microsoft.com/en-us/windows/wsl/install).

### 1. Clone the repository
```bash
git clone https://github.com/mouhamedhabib/Tunisia-Jobs-Tracker.git
cd Tunisia-Jobs-Tracker
```

### 2. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
```

Edit `.env` if needed:
```
DB_PATH=./data/jobs.db
USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
REQUEST_DELAY=2
MAX_PAGES=10
LOG_LEVEL=INFO
```

### 5. Run scrapers
```bash
python3 -m scrapers.farojob
python3 -m scrapers.keejob
python3 -m scrapers.offre_emploi_tn
```

### 6. Clean and normalize data
```bash
python3 -m processing.cleaner
```

### 7. Launch dashboard
```bash
streamlit run dashboard/app.py
```

---

## 🤖 Automated Updates

This project uses **GitHub Actions** to automatically scrape and update data every day at 6:00 AM UTC.

The workflow:
1. Runs all three scrapers
2. Cleans and normalizes the data
3. Exports `jobs_cleaned.csv`
4. Commits and pushes the updated CSV to the repository
5. Streamlit Cloud picks up the new data automatically

---

## 🗄️ Database Schema
```sql
CREATE TABLE jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    company     TEXT,
    city        TEXT,               -- Normalized to 24 Tunisian governorates
    region      TEXT,
    contract    TEXT,
    skills      TEXT,
    salary      TEXT,
    source      TEXT NOT NULL,
    url         TEXT UNIQUE,        -- Prevents duplicates
    posted_at   TEXT,
    scraped_at  TEXT DEFAULT (datetime('now'))
);
```

---

## 🔒 Security

- Parameterized SQL queries — no SQL injection risk
- URL validation before database insertion
- `DB_PATH` restricted to project directory
- No credentials or API keys required

---

## 📈 Sample Data

| Metric | Value |
|--------|-------|
| Total listings | ~440 |
| Cities covered | 10+ governorates |
| Sources | 3 |
| Auto-update | Daily via GitHub Actions |
| Duplicate prevention | URL UNIQUE constraint |

---

## 📝 License

MIT License — free to use, modify, and distribute.

---

## 👤 Author

Built by **Mohamed Habib Chaieb** · [GitHub](https://github.com/mouhamedhabib) · [LinkedIn](https://www.linkedin.com/in/chaieb-mohammed-habib/)
