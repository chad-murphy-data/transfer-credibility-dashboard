import streamlit as st
import pandas as pd
import altair as alt

# Load structured file
df = pd.read_csv("data/fabrizio_may_to_june_structured_v1_5.csv")

st.set_page_config(page_title="Transfer Credibility Dashboard (v1.5+)", layout="wide")
st.title("🎯 Transfer Credibility Dashboard (Powered by MITCHARD v1.5)")

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

# Apply filters
filtered = df[
    (df["status_bin"].isin(selected_bins)) &
    (df["certainty_score"].between(score_range[0], score_range[1]))
]

if club_choice != "All":
    filtered = filtered[
        (filtered["destination_club"] == club_choice) | (filtered["origin_club"] == club_choice)
    ]

# Rumor logic — temporarily include everything
st.write("🧪 Filtered rows before rumor filter:", len(filtered))

if "is_transfer_rumor" in filtered.columns:
    st.write("🧪 Rows where is_transfer_rumor == True:", filtered["is_transfer_rumor"].sum())
else:
    st.write("⚠️ 'is_transfer_rumor' column missing from filtered DataFrame!")

rumors = filtered.copy()

# Prep for chart
rumors["Label"] = rumors["player"].fillna("Unknown") + " → " + rumors["destination_club"].fillna("???")
rumors["certainty_score"] = pd.to_numeric(rumors["certainty_score"], errors="coerce").clip(upper=1.0)

# 🔝 Top 10 chart
st.subheader("🔝 Top 10 Credible Transfer Rumors")
top10 = rumors.sort_values("certainty_score", ascending=False).head(10).copy()

# Debug block
st.write("🧪 TOP 10 RAW", top10)
st.write("✅ Top 10 shape:", top10.shape)
st.write("✅ Columns:", top10.columns.tolist())
st.write("✅ Certainty Score Dtype:", top10["certainty_score"].dtype)
st.write("✅ Certainty Score values:", top10["certainty_score"].tolist())

# Chart rendering
top10["player"] = top10["player"].fillna("Unknown")
top10["destination_club"] = top10["destination_club"].fillna("???")
top10["Label"] = top10["player"] + " → " + top10["destination_club"]

if top10.empty:
    st.info("No rumors match your filters.")
else:
    chart = alt.Chart(top10).mark_bar().encode(
        x=alt.X("certainty_score", title="Certainty Score"),
        y=alt.Y("Label", sort="-x", title="", axis=alt.Axis(labelLimit=300)),
        tooltip=["player", "origin_club", "destination_club", "status", "certainty_score", "reason"]
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

# Full table
st.subheader(f"📋 {len(rumors)} Matching Transfer Rumors")
st.dataframe(rumors[
    ["player", "origin_club", "destination_club", "status", "status_bin", "certainty_score", "reason", "tweet_text"]
].sort_values("certainty_score", ascending=False), use_container_width=True)

# Download
csv = rumors.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download filtered rumors as CSV", csv, "filtered_rumors_v1_5.csv", "text/csv")
