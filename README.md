# IndiaMART B2B Scraper + EDA Dashboard

3 files. No frameworks. No config layers.

```
indiamart_simple/
├── scraper.py       # crawl IndiaMART (or generate mock data)
├── dashboard.py     # Streamlit EDA dashboard
├── requirements.txt
└── data/
    └── listings.csv # created after running scraper
```

---

## How to run

### Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Get data

**Option A: Mock data (instant, no network needed)**
```bash
python scraper.py --mock
```

**Option B: Live scrape from IndiaMART**
```bash
python scraper.py
```
> Scrapes 3 categories × 3 pages each (~90–240 listings). Takes ~2 min due to polite delays.
> Automatically falls back to mock data if the site is unreachable.

### Step 3 — Launch the dashboard

```bash
streamlit run dashboard.py
```

Opens at `http://localhost:8501` in your browser.

---

## What gets scraped

3 categories: **Industrial Machinery**, **Electronics**, **Textiles**

Fields collected per listing:

| Field | Description |
|---|---|
| title | Product name |
| category | industrial_machinery / electronics / textiles |
| price | Raw price string from page |
| price_min / price_max | Parsed numeric bounds |
| supplier | Company name |
| location | City, State |
| rating | Supplier rating (if shown) |
| reviews | Review count |
| url | Source listing URL |
| scraped_at | Timestamp |

---

## Dashboard tabs

| Tab | What's in it |
|---|---|
| Categories | Listing count + supplier count per category |
| Prices | Box plot (log scale) + top 10 highest-priced |
| Regional | Top states bar chart + city treemap |
| Ratings | Rating histogram + rating vs reviews scatter |
| Data | Searchable table + CSV download |
