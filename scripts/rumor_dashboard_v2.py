import streamlit as st
import pandas as pd
import altair as alt

# Load data
df = pd.read_csv("data/fabrizio_may_to_june_structured_v1_5.csv")

st.set_page_config(page_title="Transfer Credibility Dashboard (v1.5+)", layout="wide")
st.title("🎯 Transfer Credibility Dashboard (Powered by MITCHARD v1.5)")

# Bin statuses
def bin_status(status):
    s = str(status).lower()
    if any(kw in s for kw in ["here we go", "confirmed", "official"]): return "Confirmed"
    if any(kw in s for kw in ["deal agreed", "agreement", "contract signed"]): return "Deal Agreed"
    if any(kw in s for kw in ["advanced", "closing in", "personal terms"]): return "Advanced Talks"
    if any(kw in s for kw in ["interest", "targeted", "monitoring", "keen", "approached"]): return "Linked / Interest"
    if any(kw in s for kw in ["rejected", "deal off", "collapsed"]): return "Rejected / Off"
    if any(kw in s for kw in ["appointment", "manager", "not staying"]): return "Manager Related"
    if "confirmed exit" in s: return "Confirmed Exit"
    return "Other / Ambiguous"

df["status_bin"] = df["status"].apply(bin_status)

# Sidebar
st.sidebar.header("Filters")
status_bins = sorted(df["status_bin"].dropna().unique())
selected_bins = st.sidebar.multiselect("Status Category", options=status_bins, default=status_bins)
clubs = sorted(set(df["destination_club"].dropna()) | set(df["origin_club"].dropna()))
club_choice = st.sidebar.selectbox("Club (To or From)", ["All"] + clubs)
min_cert, max_cert = df["certainty_score"].min(), df["certainty_score"].max()
score_range = st.sidebar.slider("Certainty Score Range", 0.0, 1.0, (min_cert, max_cert), step=0.05)

# Filter data
filtered = df[df["status_bin"].isin(selected_bins)]
filtered = filtered[filtered["certainty_score"].between(score_range[0], score_range[1])]
if club_choice != "All":
    filtered = filtered[(filtered["destination_club"] == club_choice) | (filtered["origin_club"] == club_choice)]

rumors = filtered[filtered["is_transfer_rumor"] == True].copy()
rumors["Label"] = rumors["player"].fillna("Unknown") + " → " + rumors["destination_club"].fillna("???")
rumors["certainty_score"] = pd.to_numeric(rumors["certainty_score"], errors="coerce")

# Top 10 Chart
st.subheader("🔝 Top 10 Credible Transfer Rumors")
top10 = rumors.sort_values("certainty_score", ascending=False).head(10)
if not top10.empty:
    chart = alt.Chart(top10).mark_bar().encode(
        x=alt.X("certainty_score", title="Certainty Score"),
        y=alt.Y("Label", sort="-x", title="", axis=alt.Axis(labelLimit=300)),
        tooltip=["player", "origin_club", "destination_club", "status", "certainty_score", "reason"]
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No rumors match your filters.")

# Full table
st.subheader(f"📋 {len(rumors)} Matching Transfer Rumors")
st.dataframe(rumors[
    ["player", "origin_club", "destination_club", "status", "status_bin", "certainty_score", "reason", "tweet_text"]
].sort_values("certainty_score", ascending=False), use_container_width=True)

# Download button
csv = rumors.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download filtered rumors as CSV", csv, "filtered_rumors_v1_5.csv", "text/csv")
