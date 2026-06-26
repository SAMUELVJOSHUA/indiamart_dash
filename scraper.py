import argparse
import csv
import random
import time
import uuid
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

OUTPUT = "data/listings.csv"

CATEGORIES = {
    "industrial_machinery": "industrial-machinery",
    "electronics":          "electronic-components-supplies",
    "textiles":             "textile",
}

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.indiamart.com/",
}

FIELDNAMES = ["id", "title", "category", "price", "price_min", "price_max",
              "supplier", "location", "rating", "reviews", "url", "scraped_at"]


def parse_price(raw):
    import re
    vals = [float(n) for n in re.findall(r"[\d]+", raw.replace(",", "")) if n]
    if not vals:
        return "", ""
    return vals[0], vals[-1]

def _txt(tag, selector):
    el = tag.select_one(selector)
    return el.get_text(strip=True) if el else None

def scrape_page(slug, label, page=1):
    url = f"https://dir.indiamart.com/impcat/{slug}.html"
    params = {"page": page} if page > 1 else {}
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Request failed: {e}")
        return []

    soup  = BeautifulSoup(resp.text, "html.parser")
    cards = (soup.select("div.productsearch") or soup.select("div.lpcn") or
             soup.select("div.prd-detail") or soup.select("div.organicList"))
    print(f"  Found {len(cards)} cards on page {page}")

    rows = []
    for card in cards:
        title = _txt(card, "a.productsearch-name") or _txt(card, "div.prd-name") or _txt(card, "a.title")
        if not title:
            continue
        price_raw = _txt(card, "span.prc") or _txt(card, "div.price") or ""
        p_min, p_max = parse_price(price_raw)
        link = card.select_one("a[href*='indiamart']") or card.select_one("a.title")
        rows.append({
            "id":         str(uuid.uuid4())[:8],
            "title":      title.strip(),
            "category":   label,
            "price":      price_raw.strip(),
            "price_min":  p_min,
            "price_max":  p_max,
            "supplier":   (_txt(card, "div.companyname") or _txt(card, "span.lcname") or "").strip(),
            "location":   (_txt(card, "span.location") or _txt(card, "span.locname") or "").strip(),
            "rating":     (_txt(card, "span.rtng-star-val") or "").strip(),
            "reviews":    (_txt(card, "span.rtng-cnt") or "").strip(),
            "url":        link["href"].strip() if link else "",
            "scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        })
    return rows

def run_scraper(pages_per_cat=3):
    rows = []
    for label, slug in CATEGORIES.items():
        print(f"\n── {label} ──")
        for page in range(1, pages_per_cat + 1):
            batch = scrape_page(slug, label, page)
            rows.extend(batch)
            if not batch:
                break
            time.sleep(random.uniform(2.5, 4.5))
    return rows

def generate_mock(n=300, seed=42):
    random.seed(seed)
    products = {
        "industrial_machinery": ["Hydraulic Press", "CNC Milling Machine", "Air Compressor",
                                 "Conveyor Belt", "Lathe Machine", "Industrial Boiler",
                                 "Gear Box", "Submersible Pump", "Packaging Machine"],
        "electronics":          ["PCB Module", "Servo Motor", "SMPS Power Supply",
                                 "LED Driver Board", "PLC Controller", "DC-DC Converter",
                                 "Solar Charge Controller", "VFD Drive", "Touch Panel"],
        "textiles":             ["Polyester Yarn", "Cotton Fabric", "Denim Cloth",
                                 "Silk Fabric", "Jute Cloth", "Linen Fabric",
                                 "Terry Towel", "Viscose Fabric", "Organza Roll"],
    }
    price_ranges = {
        "industrial_machinery": (5000, 500000),
        "electronics":          (200, 25000),
        "textiles":             (50, 2000),
    }
    suppliers = ["Rajesh Industries", "Sharma Enterprises", "Kumar Tech", "Patel Mfg Co",
                 "Singh & Sons", "Verma Traders", "Gupta Exports", "National Works",
                 "Allied Corp", "Sunrise Electronics", "Galaxy Textiles", "Bharat Suppliers"]
    locations = ["Mumbai, Maharashtra", "Delhi, Delhi", "Surat, Gujarat",
                 "Ludhiana, Punjab", "Coimbatore, Tamil Nadu", "Rajkot, Gujarat",
                 "Pune, Maharashtra", "Ahmedabad, Gujarat", "Chennai, Tamil Nadu",
                 "Hyderabad, Telangana", "Bengaluru, Karnataka", "Kolkata, West Bengal"]

    rows = []
    for category, titles in products.items():
        lo, hi = price_ranges[category]
        for _ in range(n // 3):
            base   = random.randint(lo, hi)
            spread = random.choice([0, 0, 0.3])
            p_min  = round(base * (1 - spread / 2))
            p_max  = round(base * (1 + spread / 2))
            has_rating = random.random() > 0.35
            rows.append({
                "id":         str(uuid.uuid4())[:8],
                "title":      random.choice(titles) + random.choice(["", " - Heavy Duty", " Premium", " Automatic"]),
                "category":   category,
                "price":      f"₹{p_min:,}" if spread == 0 else f"₹{p_min:,} - ₹{p_max:,}",
                "price_min":  p_min,
                "price_max":  p_max,
                "supplier":   random.choice(suppliers),
                "location":   random.choice(locations),
                "rating":     round(random.uniform(3.0, 5.0), 1) if has_rating else "",
                "reviews":    random.randint(1, 400) if has_rating else "",
                "url":        f"https://dir.indiamart.com/impcat/sample-{random.randint(10000,99999)}.html",
                "scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            })
    print(f"Generated {len(rows)} mock rows")
    return rows

def save_csv(rows):
    import os
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓ Saved {len(rows)} rows → {OUTPUT}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    rows = generate_mock() if args.mock else run_scraper(pages_per_cat=3)
    if not rows:
        print("No rows scraped — falling back to mock data")
        rows = generate_mock()
    save_csv(rows)
