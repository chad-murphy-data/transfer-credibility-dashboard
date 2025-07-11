import streamlit as st
import pandas as pd
import altair as alt

# Load structured file (you can update the path to the new dataset)
df = pd.read_csv("data/transfer_rumors_with_tags_and_bins.csv")

st.set_page_config(page_title="Transfer Credibility Dashboard (v2)", layout="wide")
st.title("🎯 Transfer Credibility Dashboard (Powered by MITCHARD v2)")

# 🧠 Helper: Bin messy statuses into categories
def bin_status(status):
    s = str(status).lower()

    if any(kw in s for kw in ["here we go", "confirmed", "official"]):
        return "Confirmed"
    if any(kw in s for kw in ["deal agreed", "agreement", "contract signed"]):
        return "Deal Agreed"
    if any(kw in s for kw in ["advanced", "closing in", "personal terms"]):
        return "Advanced Talks"
    if any(kw in s for kw in ["interest", "targeted", "monitoring", "keen", "approached"]):
        return "Linked / Interest"
    if any(kw in s for kw in ["rejected", "deal off", "collapsed"]):
        return "Rejected / Off"
    if any(kw in s for kw in ["appointment", "manager", "not staying"]):
        return "Manager Related"
    if "confirmed exit" in s:
        return "Confirmed Exit"
    return "Other / Ambiguous"

df["status_bin"] = df["status"].apply(bin_status)

# Sidebar filters
st.sidebar.header("Filters")

# Status bin filter
status_bins = sorted(df["status_bin"].dropna().unique())
selected_bins = st.sidebar.multiselect("Status Category", options=status_bins, default=status_bins)

# Club filter
clubs = sorted(set(df["destination_club"].dropna().unique()) | set(df["origin_club"].dropna().unique()))
club_choice = st.sidebar.selectbox("Club (To or From)", options=["All"] + clubs)

# Certainty score filter
min_cert, max_cert = float(df["certainty_score"].min()), float(df["certainty_score"].max())
score_range = st.sidebar.slider("Certainty Score Range", min_value=0.0, max_value=1.0, value=(min_cert, max_cert), step=0.05)

# Apply filters with proper logic
filtered = df[
    (df["status_bin"].isin(selected_bins)) &
    (df["certainty_score"].between(score_range[0], score_range[1]))
]

if club_choice != "All":
    filtered = filtered[
        (filtered["destination_club"] == club_choice) | (filtered["origin_club"] == club_choice)
    ]

# Hide completed transfers toggle
hide_completed = st.sidebar.checkbox("Hide completed transfers (Confirmed / Deal Agreed / Exit)", value=False)
if hide_completed:
    filtered = filtered[~filtered["status_bin"].isin(["Confirmed", "Deal Agreed", "Confirmed Exit"])]

# Certainty bin toggle
if "certainty_bin_label" in filtered.columns:
    show_certainty_bins = st.sidebar.checkbox("Show MITCHARD bins (e.g. 'Ghosted', 'No Shot')", value=False)
    if show_certainty_bins:
        available_bins = sorted(filtered["certainty_bin_label"].dropna().unique())
        selected_certainty_bins = st.sidebar.multiselect("Certainty Category (MITCHARD)", options=available_bins, default=available_bins)
        filtered = filtered[filtered["certainty_bin_label"].isin(selected_certainty_bins)]

# Speculation flag toggle
show_speculation_filter = st.sidebar.checkbox("Show narrative speculation filters (Laporta, Galactico, etc.)", value=False)
if show_speculation_filter and "speculation_flag" in filtered.columns:
    available_flags = sorted(filtered["speculation_flag"].dropna().unique())
    selected_flags = st.sidebar.multiselect("Speculation Tags", options=available_flags, default=available_flags)
    filtered = filtered[filtered["speculation_flag"].isin(selected_flags)]

# Filter only rumors
rumors = filtered[filtered["is_transfer_rumor"] == True].copy()

# Prepare for display
rumors["Label"] = rumors["player"].fillna("Unknown") + " → " + rumors["destination_club"].fillna("???")
rumors["certainty_score"] = pd.to_numeric(rumors["certainty_score"], errors="coerce").clip(upper=1.0)

# Highest-value rumors (deduplicated) by probability
st.subheader("💸 Top 10 Highest-Value Rumors (by Transfer Probability)")

# Deduplicate: keep highest-probability rumor per player → destination
deduped = (
    rumors
    .sort_values("certainty_score", ascending=False)
    .drop_duplicates(subset=["player", "destination_club"])
    .copy()
)

# Fill missing values
deduped["player"] = deduped["player"].fillna("Unknown")
deduped["destination_club"] = deduped["destination_club"].fillna("???")
deduped["Label"] = deduped["player"] + " → " + deduped["destination_club"]

# Sort by player value to highlight high-value targets
top10_prob = deduped.sort_values("market_value_eur", ascending=False).head(10)

if top10_prob.empty:
    st.info("No rumors match your filters.")
else:
    chart = alt.Chart(top10_prob).mark_bar().encode(
        x=alt.X("certainty_score", title="Probability of Transfer", scale=alt.Scale(domain=[0,1])),
        y=alt.Y("Label", sort="-x", title="", axis=alt.Axis(labelLimit=300)),
        tooltip=["player", "certainty_score", "market_value_eur", "origin_club", "destination_club", "status"]
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

# Full table
st.subheader(f"📋 {len(rumors)} Matching Transfer Rumors")
st.dataframe(rumors[
    ["player", "origin_club", "destination_club", "status", "status_bin", "certainty_score", "market_value_eur", "reason", "tweet_text"]
].sort_values("certainty_score", ascending=False), use_container_width=True)

# Download
csv = rumors.to_csv(index=False).encode("utf-8")
st.download_button("📅 Download filtered rumors as CSV", csv, "filtered_rumors_v2.csv", "text/csv")
