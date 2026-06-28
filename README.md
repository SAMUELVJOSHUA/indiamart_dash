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
| 💰 Prices | Price band distribution, avg price by category, price summary table, top 10 highest-priced listings, top keywords in listing titles, insights |
| 🗺️ Regional | Top states bar chart, city treemap, category × state heatmap, listing collection trend over time, insights |
| ⭐ Ratings | Rating distribution, rating vs reviews scatter, top rated suppliers, insights |
| 🔍 Data Quality | Null analysis with handling method, duplicate counts, anomaly detection, raw data explorer with CSV download |

---

## Data Quality Checks

| Check | Method |
|---|---|
| Null values | Prices filled with category median · Rating/reviews filled with 0 (no rating available) |
| Duplicates | Exact, soft (title + supplier + category), and URL duplicates flagged |
| Anomalies | Inverted price ranges, price outliers (>3σ), out-of-range ratings, title length issues |

---

## Key Insights

### 💰 Prices
- **Industrial Machinery** shows the highest price spread, suggesting a wide range of product complexity and scale — from small components to large capital equipment
- **Electronics** listings cluster heavily in the ₹2K–10K band, pointing to strong mid-market component demand
- **Textiles** are concentrated at lower price points, consistent with bulk commodity pricing where volume drives value

### 🗺️ Regional
- **Gujarat and Maharashtra** consistently appear across all three categories, making them the most active B2B supplier hubs on the platform
- **Coimbatore (Tamil Nadu)** dominates Textile listings, aligning with its established reputation as India's textile manufacturing capital
- **Delhi and Ludhiana** show strong presence in Industrial Machinery, reflecting Punjab and NCR's manufacturing corridors

### ⭐ Ratings
- A large share of listings carry no rating, indicating that review adoption on IndiaMART is still low — a potential trust gap for buyers evaluating suppliers
- Among rated suppliers, most cluster between **4.0–4.5**, suggesting generally positive sentiment but limited differentiation at the top end
- No strong correlation observed between review count and rating score — high review volume does not necessarily mean higher ratings

### 🔍 Data Quality
- **Rating and review nulls** are the most common quality gap, affecting roughly 35–40% of listings — these were filled with 0 to preserve the dataset without introducing bias
- **Soft duplicates** (same product listed by the same supplier across pages) are present, suggesting suppliers re-list products across categories for visibility
- **Price outliers** beyond 3 standard deviations are rare but exist, likely representing custom or enterprise-grade machinery quoted on a per-unit basis
