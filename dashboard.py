import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.express as px
import streamlit as st

from eda import (
    load, null_analysis, after_null_handling,
    duplicate_analysis, anomaly_report, get_price_outliers,
    price_stats, price_band_dist, listings_by_state, listings_by_city,
    category_by_state, rating_stats, top_rated_suppliers,
)

def centered(df):
    return {col: st.column_config.TextColumn(col, width="medium") for col in df.columns}

st.set_page_config(page_title="IndiaMART EDA", page_icon="🏭", layout="wide")
st.title("🏭 IndiaMART B2B — EDA Dashboard")

@st.cache_data
def get_data():
    if not os.path.exists("data/listings.csv"):
        st.error("Run `python scraper.py --mock` first.")
        st.stop()
    return load()

df_raw = get_data()

st.sidebar.header("Filters")
cats = sorted(df_raw["category"].dropna().unique())
sel_cats = st.sidebar.multiselect("Category", cats, default=cats,
                                   format_func=lambda x: x.replace("_", " ").title())
states = sorted(df_raw["state"].dropna().unique())
sel_states = st.sidebar.multiselect("State", states, default=states)
max_p = int(df_raw["price_mid"].dropna().max()) if df_raw["price_mid"].notna().any() else 500000
price_range = st.sidebar.slider("Price midpoint (₹)", 0, max_p, (0, max_p), step=500)

df = df_raw[
    df_raw["category"].isin(sel_cats) &
    df_raw["state"].isin(sel_states) &
    (df_raw["price_mid"].between(*price_range) | df_raw["price_mid"].isna())
].copy()

total_rev = df["price_mid"].sum()
avg_rev   = df["price_mid"].mean()
avg_r     = df[df["rating"] > 0]["rating"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Listings",       f"{len(df):,}")
k2.metric("Unique Suppliers",     f"{df['supplier'].nunique():,}")
k3.metric("Est. Total GMV (₹)",   f"₹{total_rev/1e6:.1f}M" if total_rev > 1e6 else f"₹{total_rev:,.0f}")
k4.metric("Avg Listing Value (₹)",f"₹{avg_rev:,.0f}" if pd.notna(avg_rev) else "—")
k5.metric("Avg Rating",           f"{avg_r:.2f} ★" if pd.notna(avg_r) else "—")

st.markdown("---")

tabs = st.tabs(["💰 Prices", "🗺️ Regional", "⭐ Ratings", "🔍 Data Quality"])

with tabs[0]:
    st.subheader("Price Analysis")

    raw_stats = price_stats(df)
    raw_stats.columns = ["Category", "# Listings", "Avg Price (₹)", "Typical Price (₹)",
                         "Lowest Price (₹)", "Highest Price (₹)", "Price Spread (₹)"]
    raw_stats["Category"] = raw_stats["Category"].str.replace("_", " ").str.title()
    for col in ["Avg Price (₹)", "Typical Price (₹)", "Lowest Price (₹)", "Highest Price (₹)", "Price Spread (₹)"]:
        raw_stats[col] = raw_stats[col].apply(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "—")

    c1, c2 = st.columns(2)
    with c1:
        bd = price_band_dist(df)
        if not bd.empty:
            bd["category"] = bd["category"].str.replace("_", " ").str.title()
            fig = px.bar(bd, x="price_band", y="count", color="category", barmode="group",
                         title="How Listings Are Distributed Across Price Ranges",
                         labels={"price_band": "Price Range", "count": "# Listings", "category": "Category"})
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        avg_price = df.groupby("category")["price_mid"].mean().reset_index()
        avg_price["category"] = avg_price["category"].str.replace("_", " ").str.title()
        fig2 = px.bar(avg_price, x="category", y="price_mid", color="category",
                      title="Average Listing Price by Category",
                      labels={"category": "Category", "price_mid": "Avg Price (₹)"},
                      text=avg_price["price_mid"].apply(lambda x: f"₹{x:,.0f}"))
        fig2.update_traces(textposition="outside")
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Price Summary by Category**")
        st.dataframe(raw_stats, use_container_width=True, hide_index=True, column_config=centered(raw_stats))
        st.caption("Typical Price = median | Price Spread = std deviation across listings")
    with c2:
        st.markdown("**Top 10 Highest-Priced Listings**")
        top10 = df.dropna(subset=["price_mid"]).nlargest(10, "price_mid")[
            ["title", "category", "price", "supplier"]].reset_index(drop=True)
        top10["title"]    = top10["title"].str.title()
        top10["category"] = top10["category"].str.replace("_", " ").str.title()
        top10["supplier"] = top10["supplier"].str.title()
        top10.columns     = ["Product", "Category", "Listed Price", "Supplier"]
        st.dataframe(top10, use_container_width=True, hide_index=True, column_config=centered(top10))

with tabs[1]:
    st.subheader("Regional Patterns")
    c1, c2 = st.columns(2)
    with c1:
        by_state = listings_by_state(df)
        fig = px.bar(by_state, x="count", y="state", orientation="h",
                     title="Which States Have the Most Listings",
                     labels={"count": "Listings", "state": ""},
                     color="count", color_continuous_scale="Blues")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        by_city = listings_by_city(df)
        fig2 = px.treemap(by_city, path=["city"], values="count",
                          title="Top Cities by Listing Volume",
                          color="count", color_continuous_scale="Oranges")
        st.plotly_chart(fig2, use_container_width=True)

    pivot = category_by_state(df)
    if not pivot.empty:
        fig3 = px.imshow(pivot, aspect="auto", color_continuous_scale="YlOrRd",
                         title="Which Categories Dominate Each State",
                         labels={"x": "Category", "y": "State", "color": "Listings"})
        st.plotly_chart(fig3, use_container_width=True)

with tabs[2]:
    st.subheader("Ratings & Reviews")
    rs = rating_stats(df)
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Listings with Rating",   rs["listings_with_rating"])
    r2.metric("% Rated",                f"{rs['pct_with_rating']}%")
    r3.metric("Avg Rating",             rs["avg_rating"])
    r4.metric("Avg Reviews / Listing",  rs["avg_reviews_per_listing"])

    c1, c2 = st.columns(2)
    rated = df[df["rating"] > 0]
    with c1:
        if not rated.empty:
            fig = px.histogram(rated, x="rating", nbins=10, color="category",
                               title="Rating Distribution",
                               labels={"category": "Category"})
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        sub = rated.dropna(subset=["reviews"])
        if not sub.empty:
            fig2 = px.scatter(sub, x="reviews", y="rating", color="category",
                              title="Do More Reviews Mean Higher Ratings?",
                              log_x=True, opacity=0.65,
                              labels={"reviews": "Review Count", "rating": "Rating", "category": "Category"})
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Top Rated Suppliers**")
    trs = top_rated_suppliers(df)
    st.dataframe(trs, use_container_width=True, hide_index=True, column_config=centered(trs))

with tabs[3]:
    st.subheader("Data Quality Report")

    st.markdown("#### Nulls")
    na = null_analysis(df)
    if na.empty:
        st.success("No nulls found.")
    else:
        df_filled, log = after_null_handling(df)
        handled = {}
        for entry in log:
            field, rest = entry.split(":", 1)
            field = field.strip()
            rest  = rest.strip()
            if field in ("rating", "reviews"):
                rest = "filled with 0 (no rating available)"
            handled[field] = rest
        na["Handled"] = na.index.map(lambda col: handled.get(col, "—"))
        na["null_pct"] = na["null_pct"].apply(lambda x: f"{x}%")
        st.dataframe(na, use_container_width=True, column_config=centered(na))

    st.markdown("---")
    st.markdown("#### Duplicates")
    dup = duplicate_analysis(df)
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Exact Duplicates",  dup["exact_duplicates"])
    d2.metric("Soft Duplicates",   dup["soft_duplicates"])
    d3.metric("URL Duplicates",    dup["url_duplicates"])
    d4.metric("Clean Row Count",   dup["rows_after_dedup"])
    if dup["soft_duplicates"] > 0:
        if st.button("Show duplicate rows"):
            dupes = df[df.duplicated(subset=["title", "supplier", "category"], keep=False)]
            st.dataframe(dupes.sort_values(["title", "supplier"]), use_container_width=True)

    st.markdown("---")
    st.markdown("#### Anomalies")
    ar = anomaly_report(df)
    ar["pct_of_total"] = ar["pct_of_total"].apply(lambda x: f"{x}%")
    st.dataframe(ar, use_container_width=True, hide_index=True, column_config=centered(ar))

    outliers = get_price_outliers(df)
    if not outliers.empty:
        st.markdown(f"**Price outliers (>3σ) — {len(outliers)} rows:**")
        st.dataframe(outliers[["title", "category", "price", "price_mid", "supplier", "location"]],
                     use_container_width=True, hide_index=True,
                     column_config=centered(outliers[["title", "category", "price", "price_mid", "supplier", "location"]]))
    else:
        st.success("No price outliers detected.")

    st.markdown("---")
    st.markdown("#### Raw Data")
    search = st.text_input("Search title / supplier", "")
    view = df.copy()
    if search:
        view = view[view["title"].str.contains(search, case=False, na=False) |
                    view["supplier"].str.contains(search, case=False, na=False)]
    st.caption(f"{len(view):,} rows")
    st.dataframe(view, use_container_width=True, height=380, hide_index=True)
    st.download_button("⬇ Download CSV", view.to_csv(index=False).encode(),
                       "indiamart_filtered.csv", "text/csv")
