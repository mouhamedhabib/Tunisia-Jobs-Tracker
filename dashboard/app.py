import streamlit as st
import pandas as pd
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "./data/jobs.db")

st.set_page_config(
    page_title="Tunisia Jobs Tracker",
    page_icon="🇹🇳",
    layout="wide"
)


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    """Load jobs from database."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM jobs", conn)
    conn.close()
    return df


def main():
    st.title("🇹🇳 Tunisia Jobs Tracker")
    st.caption("Job listings scraped from farojob.net · keejob.com · offre-emploi.tn")

    df = load_data()

    if df.empty:
        st.warning("No data found. Run the scraper first.")
        return

    # ── Metrics ─────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Listings", len(df))
    col2.metric("Companies", df["company"].nunique())
    col3.metric("Cities", df["city"].dropna().nunique())
    col4.metric("Sources", df["source"].nunique())

    st.divider()

    # ── Charts Row 1 ─────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Contract Types")
        contract_counts = (
            df["contract"]
            .fillna("Not specified")
            .value_counts()
            .reset_index()
        )
        contract_counts.columns = ["Contract", "Count"]
        st.bar_chart(contract_counts.set_index("Contract"))

    with col_right:
        st.subheader("Top 10 Cities")
        city_counts = (
            df["city"]
            .dropna()
            .value_counts()
            .head(10)
            .reset_index()
        )
        city_counts.columns = ["City", "Listings"]
        st.bar_chart(city_counts.set_index("City"))

    st.divider()

    # ── Charts Row 2 ─────────────────────────────────────────────
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.subheader("Top 15 Hiring Companies")
        company_counts = (
            df["company"]
            .dropna()
            .value_counts()
            .head(15)
            .reset_index()
        )
        company_counts.columns = ["Company", "Listings"]
        st.bar_chart(company_counts.set_index("Company"))

    with col_right2:
        st.subheader("Listings by Source")
        source_counts = (
            df["source"]
            .value_counts()
            .reset_index()
        )
        source_counts.columns = ["Source", "Listings"]
        st.bar_chart(source_counts.set_index("Source"))

    st.divider()

    # ── Filters + Table ──────────────────────────────────────────
    st.subheader("Browse All Listings")

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        contracts = ["All"] + sorted(df["contract"].dropna().unique().tolist())
        selected_contract = st.selectbox("Contract Type", contracts)

    with f2:
        cities = ["All"] + sorted(df["city"].dropna().unique().tolist())
        selected_city = st.selectbox("City", cities)

    with f3:
        sources = ["All"] + sorted(df["source"].unique().tolist())
        selected_source = st.selectbox("Source", sources)

    with f4:
        search = st.text_input("Search title or company")

    # Apply filters
    filtered = df.copy()

    if selected_contract != "All":
        filtered = filtered[filtered["contract"] == selected_contract]
    if selected_city != "All":
        filtered = filtered[filtered["city"] == selected_city]
    if selected_source != "All":
        filtered = filtered[filtered["source"] == selected_source]
    if search:
        mask = (
            filtered["title"].str.contains(search, case=False, na=False) |
            filtered["company"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    st.dataframe(
        filtered[["title", "company", "city", "contract", "source", "posted_at", "url"]]
        .rename(columns={
            "title":     "Title",
            "company":   "Company",
            "city":      "City",
            "contract":  "Contract",
            "source":    "Source",
            "posted_at": "Posted",
            "url":       "Link",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(f"Showing {len(filtered)} of {len(df)} listings")


if __name__ == "__main__":
    main()
