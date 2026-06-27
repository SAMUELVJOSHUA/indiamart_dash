# IndiaMART B2B Scraper + EDA Dashboard

4 files. No frameworks. No config layers.

```
indiamart_simple/
├── scraper.py       # crawl IndiaMART or generate mock data → data/listings.csv
├── eda.py           # all EDA logic (importable + runnable standalone)
├── dashboard.py     # Streamlit dashboard powered by eda.py
├── requirements.txt
└── data/
    └── listings.csv # created after running scraper
```

---

## How to run

```bash
# 1. Install
pip install -r requirements.txt

# 2. Get data
python scraper.py --mock       # instant, no network needed
python scraper.py              # live scrape (~2 min, falls back to mock if blocked)

# 3. Optional: view EDA summary in terminal
python eda.py

# 4. Launch dashboard
streamlit run dashboard.py
```

Opens at `http://localhost:8501`

---

## What gets scraped

3 categories: **Industrial Machinery**, **Electronics**, **Textiles**

| Field | Description |
|---|---|
| title | Product name |
| category | industrial_machinery / electronics / textiles |
| price | Raw price string from page |
| price_min / price_max | Parsed numeric bounds |
| supplier | Company name |
| location | City, State |
| rating | Supplier rating (0 if not available) |
| reviews | Review count (0 if not available) |
| url | Source listing URL |
| scraped_at | UTC timestamp |

---

## Dashboard

**KPIs:** Total Listings · Unique Suppliers · Est. Total GMV · Avg Listing Value · Avg Rating

| Tab | Contents |
|---|---|
| 💰 Prices | Price band distribution, avg price by category, price summary table, top 10 highest-priced listings |
| 🗺️ Regional | Top states bar chart, city treemap, category × state heatmap |
| ⭐ Ratings | Rating distribution, rating vs reviews scatter, top rated suppliers |
| 🔍 Data Quality | Null analysis with handling method, duplicate counts, anomaly detection, raw data explorer |

---

## Data Quality Checks

| Check | Method |
|---|---|
| Null values | Prices filled with category median · Rating/reviews filled with 0 |
| Duplicates | Exact, soft (title + supplier + category), and URL duplicates flagged |
| Anomalies | Inverted price ranges, price outliers (>3σ), out-of-range ratings, title length issues |
