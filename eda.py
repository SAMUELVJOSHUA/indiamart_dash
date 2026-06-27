import re
from collections import Counter
import pandas as pd

CSV = "data/listings.csv"

def load(path=CSV):
    df = pd.read_csv(path)
    df["price_min"] = pd.to_numeric(df["price_min"], errors="coerce")
    df["price_max"] = pd.to_numeric(df["price_max"], errors="coerce")
    df["rating"]    = pd.to_numeric(df["rating"],    errors="coerce")
    df["reviews"]   = pd.to_numeric(df["reviews"],   errors="coerce")
    df["price_mid"] = (df["price_min"] + df["price_max"]) / 2
    df[["city", "state"]] = (
        df["location"].str.split(",", n=1, expand=True).apply(lambda c: c.str.strip())
    )
    return df

def null_analysis(df):
    nulls = df.isnull().sum()
    pct   = (nulls / len(df) * 100).round(2)
    result = pd.DataFrame({"null_count": nulls, "null_pct": pct})
    return result[result["null_count"] > 0].sort_values("null_pct", ascending=False)

def after_null_handling(df):
    df  = df.copy()
    log = []
    for col in ["price_min", "price_max", "price_mid"]:
        n = df[col].isna().sum()
        df[col] = df.groupby("category")[col].transform(lambda x: x.fillna(x.median()))
        if n:
            log.append(f"{col}: filled {n} nulls with category median")
    for col in ["rating", "reviews"]:
        n = df[col].isna().sum()
        df[col] = df[col].fillna(0)
        if n:
            log.append(f"{col}: filled {n} nulls with 0")
    for col in ["supplier", "location", "city", "state"]:
        n = df[col].isna().sum()
        df[col] = df[col].fillna("Unknown")
        if n:
            log.append(f"{col}: filled {n} nulls with 'Unknown'")
    return df, log

def duplicate_analysis(df):
    return {
        "exact_duplicates": int(df.duplicated().sum()),
        "soft_duplicates":  int(df.duplicated(subset=["title", "supplier", "category"]).sum()),
        "url_duplicates":   int(df.duplicated(subset=["url"]).sum()) if "url" in df.columns else 0,
        "rows_after_dedup": int(len(df) - df.duplicated(subset=["title", "supplier", "category"]).sum()),
    }

def anomaly_report(df):
    mean_p, std_p = df["price_mid"].mean(), df["price_mid"].std()
    flags = {
        "Inverted price range (min > max)":  int(((df["price_min"] > df["price_max"]) & df["price_min"].notna() & df["price_max"].notna()).sum()),
        "Price outliers (> 3 std devs)":     int((df["price_mid"] > mean_p + 3 * std_p).sum()),
        "Rating out of range (> 5)":         int((df["rating"] > 5).sum()),
        "Review count above 99th percentile":int((df["reviews"] > df["reviews"].quantile(0.99)).sum()),
        "Title too short (< 3 chars)":       int((df["title"].str.len() < 3).sum()),
        "Title too long (> 150 chars)":      int((df["title"].str.len() > 150).sum()),
    }
    result = pd.DataFrame(list(flags.items()), columns=["anomaly_check", "count"])
    result["pct_of_total"] = (result["count"] / len(df) * 100).round(2)
    return result

def get_price_outliers(df, threshold=3):
    mean_p, std_p = df["price_mid"].mean(), df["price_mid"].std()
    return df[df["price_mid"] > mean_p + threshold * std_p].copy()

def price_stats(df):
    return (
        df.groupby("category")["price_mid"]
        .agg(count="count", mean="mean", median="median", min="min", max="max", std="std")
        .round(2).reset_index()
    )

def price_band_dist(df):
    bins   = [0, 500, 2000, 10000, 50000, float("inf")]
    labels = ["<₹500", "₹500–2K", "₹2K–10K", "₹10K–50K", "₹50K+"]
    df = df.copy()
    df["price_band"] = pd.cut(df["price_mid"], bins=bins, labels=labels, right=False)
    return (
        df.groupby(["category", "price_band"], observed=True)
        .size().reset_index(name="count")
    )

def listings_by_state(df, top_n=15):
    return (
        df.dropna(subset=["state"]).groupby("state")["id"].count()
        .reset_index(name="count").sort_values("count", ascending=False).head(top_n)
    )

def listings_by_city(df, top_n=15):
    return (
        df.dropna(subset=["city"]).groupby("city")["id"].count()
        .reset_index(name="count").sort_values("count", ascending=False).head(top_n)
    )

def category_by_state(df):
    if "state" not in df.columns:
        return pd.DataFrame()
    pivot = (
        df.dropna(subset=["state"]).groupby(["state", "category"])["id"].count()
        .unstack(fill_value=0)
    )
    return pivot.loc[pivot.sum(axis=1).nlargest(12).index]

def rating_stats(df):
    rated = df[df["rating"] > 0]
    return {
        "listings_with_rating":    int(len(rated)),
        "pct_with_rating":         round(len(rated) / len(df) * 100, 2),
        "avg_rating":              round(rated["rating"].mean(), 2),
        "avg_reviews_per_listing": round(rated["reviews"].mean(), 2),
    }

def top_rated_suppliers(df, min_listings=2, top_n=10):
    grp = df[df["rating"] > 0].groupby("supplier")
    result = grp.agg(
        avg_rating=("rating", "mean"),
        listing_count=("id", "count"),
        avg_reviews=("reviews", "mean"),
    ).reset_index()
    return (
        result[result["listing_count"] >= min_listings]
        .sort_values("avg_rating", ascending=False)
        .head(top_n).round(2).reset_index(drop=True)
    )

STOP = {"and","the","of","for","with","in","a","an","to","or","by","at","on",
        "heavy","duty","grade","quality","automatic","premium","standard"}

def top_keywords(df, n=20):
    words = []
    for title in df["title"].dropna():
        tokens = re.findall(r"[a-zA-Z]+", title.lower())
        words.extend([t for t in tokens if t not in STOP and len(t) > 2])
    return pd.DataFrame(Counter(words).most_common(n), columns=["keyword", "frequency"])


if __name__ == "__main__":
    df = load()
    print(f"Rows: {len(df)} | Columns: {len(df.columns)}")
    print("\nNulls:\n", null_analysis(df))
    print("\nDuplicates:", duplicate_analysis(df))
    print("\nAnomalies:\n", anomaly_report(df).to_string(index=False))
    print("\nPrice Stats:\n", price_stats(df).to_string(index=False))
    print("\nTop States:\n", listings_by_state(df).head(5).to_string(index=False))
    print("\nRating Stats:", rating_stats(df))
