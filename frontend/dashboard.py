# dashboard.py
"""
PulseCI News Analytics Dashboard — Neumorphic Dark (Style A)
- Category-first analytics
- Fixed top nav with logo & name
- Left sidebar (category filter replaces topics)
- News cards: Category header, truncated topic w/ tooltip, sentiment dot + score
- Charts: KPI sparklines, bar, donut/pie, scatter, heatmap (category vs day)
- Dark theme + neumorphic card styles via CSS
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

# handlers (assumes available)
from handler.news_handler import get_all_news

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="PulseCI News Analytics", page_icon="📰", layout="wide")
# avoid experimental memo references; use cache_data / cache_resource

# ---------------------------
# UI constants & thresholds
# ---------------------------
NAV_LOGO = "https://placehold.co/48x48?text=P"  # replace later
NAV_TITLE = "PulseCI"
CARD_LIMIT = 20
S_POS = 0.2
S_NEG = -0.2


st.markdown("""
<style>

/* Hide Streamlit's default MainMenu */
div[data-testid="stMainMenu"] {visibility: hidden !important;}
header {visibility: hidden;}

/* Hide Streamlit's Toolbar */
div[data-testid="stToolbar"] {visibility: hidden !important;}

/* Hide Streamlit's footer */
footer {visibility: hidden !important;}
div[data-testid="stStatusWidget"] {visibility: hidden !important;}

</style>
""", unsafe_allow_html=True)




# ---------------------------
# Dark neumorphic CSS
# ---------------------------
st.markdown(
    f"""
    <style>
    /* Page background */
    :root {{
        --bg: #0b1020;
        --panel: #0f1724;
        --muted: #94a3b8;
        --accent: #7c3aed;
        --card: #0b1220;
        --glass: rgba(255,255,255,0.02);
    }}
    html, body, .stApp {{
        background: linear-gradient(180deg, var(--bg), #07090f) !important;
        color: #e6eef8;
    }}

    /* Top nav */
    .top-nav {{
        position: fixed;
        top: 8px;
        left: 16px;
        right: 16px;
        height: 64px;
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        backdrop-filter: blur(6px);
        border-radius: 14px;
        display:flex;
        align-items:center;
        padding: 8px 16px;
        gap:12px;
        z-index:9999;
        box-shadow: 0 6px 20px rgba(12,14,20,0.6), inset 0 1px 0 rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.03);
    }}
    .top-nav img {{
        width:48px; height:48px; border-radius:8px;
    }}
    .top-nav .title {{
        font-weight:700; font-size:18px; color: #e6eef8;
    }}

    /* ensure main content starts below navbar */
    .main-content {{
        padding-top: 90px;
    }}

    /* Sidebar adjustments (keep sticky feel) */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 12px;
        padding: 12px 12px 18px 12px;
    }}

    /* News card neumorphic */
    .news-container {{ max-height: 780px; overflow-y: auto; padding-right:8px; }}
    .news-card {{
        border-radius: 12px;
        background: linear-gradient(180deg, rgba(255,255,255,0.012), rgba(255,255,255,0.008));
        box-shadow:
            8px 8px 18px rgba(3,6,15,0.6),
            -6px -6px 12px rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.03);
        padding: 0;
        margin-bottom: 14px;
        overflow:hidden;
    }}
    .card-header {{
        padding:10px 14px;
        background: linear-gradient(180deg, rgb(34 22 121 / 15%), rgb(20 61 208 / 36%));
        border-bottom: 1px solid rgba(255,255,255,0.02);
        font-weight:700;color:#e6eef8;
    }}
    .card-body {{ padding:12px 14px; display:flex; gap:12px; }}
    .news-title {{ font-weight:700; font-size:1.02rem; color:#f8fafc; margin-bottom:6px; }}
    .news-meta {{ color:var(--muted); font-size:0.85rem; margin-bottom:8px; }}
    .news-summary {{ color:#dfe9ff; font-size:0.95rem; max-height:76px; overflow:hidden; }}
    .card-footer {{
        padding:10px 14px;
        display:flex; justify-content:space-between; align-items:center;
        border-top:1px solid rgba(255,255,255,0.01);
        background: linear-gradient(180deg, rgba(255,255,255,0.012), rgba(255,255,255,0.006));
    }}
    .topic-pill {{
        display:inline-block; padding:6px 10px; border-radius:999px; background: rgba(124,58,237,0.12);
        color:#c7b7ff; font-weight:600; font-size:0.9rem;
    }}
    .truncate {{ display:inline-block; max-width:120px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; vertical-align:middle; }}
    .sentiment-badge {{ display:flex; gap:8px; align-items:center; font-weight:700; color:#e6eef8; }}
    .sent-dot {{ width:12px; height:12px; border-radius:50%; display:inline-block; box-shadow:0 2px 6px rgba(0,0,0,0.6); }}
    .st-emotion-cache-ujm5ma{{color:white;visibility:visible;}}

    # button:not(:disabled), [role="button"]:not(:disabled) {{
    # cursor: pointer;
    # background: rgb(25 102 202);
    # }}

    /* small responsive tweaks */
    @media (max-width: 800px) {{
        .news-card {{ margin-bottom:10px; }}
    }}

    /* Ensure streamlit text contrasts */
    .stApp, .st-b7 {{ color: #e6eef8; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Top nav (fixed)
st.markdown(
    f"""
    <div class="top-nav">
        <img src="{NAV_LOGO}" alt="PulseCI"/>
        <div class="title">{NAV_TITLE}</div>
    </div>
    <div class="main-content"></div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# Data loading helpers (cached)
# ---------------------------
@st.cache_data(ttl=60)
def load_news() -> pd.DataFrame:
    """Load news from handler and normalize into DataFrame."""
    raw = asyncio.run(get_all_news())
    if not raw:
        return pd.DataFrame(columns=[
            "news_id","title","link","published","summary","source",
            "sentiment","sentiment_score","topic","category"
        ])
    rows = []
    for it in raw:
        nid = it.get("news_id")
        title = it.get("title","") or ""
        link = it.get("link","") or ""
        summary = it.get("summary","") or ""
        source = it.get("source","") or ""
        topic = it.get("topic") or "Unknown"
        category = it.get("category") or "other"
        s_score = it.get("sentiment_score")
        try:
            s_score = float(s_score)
        except Exception:
            s_score = 0.0
        s_label = it.get("sentiment")
        if not s_label:
            if s_score > S_POS:
                s_label = "positive"
            elif s_score < S_NEG:
                s_label = "negative"
            else:
                s_label = "neutral"
        # published robust parsing
        published_raw = it.get("published")
        published_dt = pd.NaT
        if published_raw is not None:
            s = str(published_raw)
            # MMDDYYYY numeric like 12102025
            if s.isdigit() and len(s)==8:
                try:
                    published_dt = datetime.strptime(s,"%m%d%Y")
                except Exception:
                    published_dt = pd.to_datetime(s, errors="coerce")
            else:
                published_dt = pd.to_datetime(s, errors="coerce")
        rows.append({
            "news_id": nid,
            "title": title,
            "link": link,
            "published": published_dt,
            "summary": summary,
            "source": source,
            "sentiment": s_label,
            "sentiment_score": s_score,
            "topic": topic,
            "category": category
        })
    df = pd.DataFrame(rows)
    if "published" in df.columns:
        df["published"] = pd.to_datetime(df["published"], errors="coerce")
    return df

# categories derived from news
@st.cache_data(ttl=300)
def get_categories(df: pd.DataFrame) -> List[str]:
    if df.empty:
        return []
    cats = sorted(df["category"].fillna("other").unique().tolist())
    return cats

news_df = load_news()
categories = get_categories(news_df)

# date defaults
if not news_df.empty and news_df["published"].notna().any():
    date_min = news_df["published"].min().date()
    date_max = news_df["published"].max().date()
else:
    date_max = datetime.utcnow().date()
    date_min = date_max - timedelta(days=30)

# ---------------------------
# Sidebar (category filter replaces topics)
# ---------------------------
with st.sidebar:
    st.header("Filters")
    # st.caption("Category-first view")
    with st.expander("Category Filter"):
        category_sel = st.multiselect("Categories", options=categories, default=categories if categories else [])
    st.divider()
    # sources
    with st.expander("Source Filter"):
        sources = sorted(news_df["source"].fillna("").unique().tolist())
        sources = [s for s in sources if s]
        source_sel = st.multiselect("Sources", options=sources, default=sources if sources else [])

    st.divider()
    with st.expander("Date Filter"):
        date_range = st.date_input("Date range", (date_min, date_max), min_value=date_min, max_value=date_max)
    st.divider()
    st.write("Display")
    show_negative = st.checkbox("Show only negative", value=False)
    st.button("Refresh data")

# ---------------------------
# Apply filters
# ---------------------------
filt = news_df.copy()
# date filter
if isinstance(date_range, tuple) and len(date_range)==2:
    start, end = date_range
    filt = filt[filt["published"].notna()]
    filt = filt[(filt["published"].dt.date >= start) & (filt["published"].dt.date <= end)]

# category filter
if category_sel:
    filt = filt[filt["category"].isin(category_sel)]
# source filter
if source_sel:
    filt = filt[filt["source"].isin(source_sel)]
# negative quick toggle
if show_negative:
    filt = filt[filt["sentiment"]=="negative"]

# ensure columns
if "sentiment_score" not in filt.columns:
    filt["sentiment_score"] = 0.0
if "topic" not in filt.columns:
    filt["topic"] = "Unknown"
if "category" not in filt.columns:
    filt["category"] = "other"

# ---------------------------
# Derived aggregations (category-centric)
# ---------------------------
def daily_by_category(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or df["published"].isna().all():
        return pd.DataFrame(columns=["date","category","articles","avg_sentiment"])
    d = df.copy()
    d["date"] = d["published"].dt.date
    g = d.groupby(["date","category"]).agg(articles=("news_id","count"), avg_sentiment=("sentiment_score","mean")).reset_index().sort_values(["date","category"])
    return g

daily_cat = daily_by_category(news_df)
daily_cat_filt = daily_by_category(filt)

cat_agg = filt.groupby("category").agg(articles=("news_id","count"), avg_sentiment=("sentiment_score","mean")).reset_index().sort_values("articles",ascending=False)

# ---------------------------
# KPI row (neumorphic small charts)
# ---------------------------
st.markdown("<br>", unsafe_allow_html=True)  # spacing after navbar
st.header("📰 PulseCI - News Analytics")

k1,k2,k3,k4 = st.columns([1.2,1,1,1], gap="small", border=True)
total_articles = int(filt.shape[0])
avg_sent = float(filt["sentiment_score"].mean()) if not filt.empty else 0.0
top_cat = cat_agg.iloc[0]["category"] if not cat_agg.empty else "—"
top_cat_count = int(cat_agg.iloc[0]["articles"]) if not cat_agg.empty else 0
positive_pct = (filt["sentiment"]=="positive").mean()*100 if not filt.empty else 0.0

# helper sparkline generator for dark theme
def sparkline_series(df_series: pd.DataFrame, y_col: str):
    if df_series.empty:
        return None
    s = df_series.groupby("date").agg({y_col:"sum"}).reset_index()
    chart = alt.Chart(s).mark_line(point=False, interpolate="monotone").encode(
        x=alt.X("date:T", axis=None),
        y=alt.Y(f"{y_col}:Q", axis=None)
    ).properties(height=60).configure_view(strokeWidth=0).configure_axis(labelColor="#cbd5e1")
    return chart

with k1:
    st.metric("Total Articles", total_articles)
    if not daily_cat_filt.empty:
        s = daily_cat_filt.groupby("date").agg(articles=("articles","sum")).reset_index()
        st.altair_chart(alt.Chart(s).mark_line().encode(x="date:T",y="articles:Q").properties(height=120), use_container_width=True)

with k2:
    st.metric("Avg sentiment", f"{avg_sent:.2f}")
    if not daily_cat_filt.empty:
        s = daily_cat_filt.groupby("date").agg(avg_sentiment=("avg_sentiment","mean")).reset_index()
        st.altair_chart(alt.Chart(s).mark_line().encode(x="date:T",y="avg_sentiment:Q").properties(height=120), use_container_width=True)

with k3:
    st.metric("Top category", f"{top_cat} ({top_cat_count})")
    if not cat_agg.empty:
        snap = cat_agg.head(6)
        bar = alt.Chart(snap).mark_bar().encode(x="articles:Q", y=alt.Y("category:N", sort="-x"))
        st.altair_chart(bar.properties(height=120), use_container_width=True)

with k4:
    # st.metric("Positive %", f"{positive_pct:.0f}%")
    if not filt.empty:
        # Normalize sentiment labels (lowercase, strip spaces)
        filt["sentiment"] = filt["sentiment"].str.lower().str.strip()

        # Count all categories
        pos = int((filt["sentiment"] == "positive").sum())
        neg = int((filt["sentiment"] == "negative").sum())
        neu = int((filt["sentiment"] == "neutral").sum())

        total = pos + neg + neu

        # Avoid divide-by-zero
        positive_pct = (pos / total * 100) if total > 0 else 0

        st.metric("Positive %", f"{positive_pct:.0f}%")

        # Prepare donut data
        donut_df = pd.DataFrame({
            "label": ["positive", "negative", "neutral"],
            "value": [pos, neg, neu]
        })

        # Donut chart
        donut = (
            alt.Chart(donut_df)
            .mark_arc(innerRadius=40)
            .encode(
                theta="value:Q",
                color=alt.Color("label:N", legend=alt.Legend(title="Sentiment")),
                tooltip=["label", "value"]
            )
            .properties(height=180)
            .configure_view(fill="transparent")
            # .configure_background(fill="transparent")
        )


        # # pos = int((filt["sentiment"]=="positive").sum())
        # # oth = max(0, total_articles-pos)
        # donut_df = pd.DataFrame({"label":["positive","others"], "value":[pos,oth]})
        # donut = alt.Chart(donut_df).mark_arc(innerRadius=30).encode(theta="value:Q", color=alt.Color("label:N", legend=None)).configure_view(fill="transparent")
        st.altair_chart(donut.properties(height=120), use_container_width=True)

st.markdown("---")

# ---------------------------
# Main layout — left news feed, right charts
# ---------------------------
with st.expander("News & Analysis",expanded=False):
    left, right = st.columns([3,2], gap="large")

# helper for sentiment color
def sentiment_color(score: float) -> str:
    if score > S_POS:
        return "#16a34a"  # green
    if score < S_NEG:
        return "#ef4444"  # red
    return "#2563eb"  # blue

def truncate(text: str, n: int=10) -> str:
    if not isinstance(text, str):
        return ""
    return text if len(text) <= n else text[:n] + "..."

def render_card_html(row: pd.Series):
    cat = row.get("category","other")
    title = row.get("title","")
    link = row.get("link","#")
    summary = row.get("summary","")
    source = row.get("source","Unknown")
    pub = row.get("published")
    pubstr = pub.strftime("%Y-%m-%d %H:%M UTC") if pd.notna(pub) else "Unknown"
    topic = row.get("topic","Unknown")
    score = row.get("sentiment_score",0.0)
    label = row.get("sentiment","neutral")
    color = sentiment_color(score)
    topic_trunc = truncate(topic,10)
    html = f'''
    <div class="news-card">
      <div class="card-header">{cat.title()}</div>
      <div class="card-body">
        <div class="text">
          <div class="news-title"><a href="{link}" target="_blank" style="color:#e6eef8;text-decoration:none;">{title}</a></div>
          <div class="news-meta">{source} • {pubstr}</div>
          <div class="news-summary">{summary}</div>
        </div>
      </div>
      <div class="card-footer">
         <div title="{topic}">Topic: <span class="topic-pill"><span class="truncate">{topic_trunc}</span></span></div>
         <div class="sentiment-badge"><span class="sent-dot" style="background:{color};"></span> {label.title()} ({score:.2f})</div>
      </div>
    </div>
    '''
    return html

# Left feed
with left:
    st.subheader("Latest News")
    st.markdown('<div class="news-container">', unsafe_allow_html=True)
    feed = filt.sort_values("published", ascending=False).reset_index(drop=True).head(CARD_LIMIT)
    if feed.empty:
        st.info("No news for selected filters.")
    else:
        cols = st.columns(2, gap="large")
        for i, r in feed.iterrows():
            col = cols[i % 2]
            col.markdown(render_card_html(r), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption(f"Showing up to {CARD_LIMIT} items — header shows category, footer shows topic & sentiment.")

# Right charts
with right:
    st.subheader("Category Insights")

    # Bar chart: articles per category
    if not cat_agg.empty:
        bar = alt.Chart(cat_agg).mark_bar().encode(
            x=alt.X("articles:Q", title="Articles"),
            y=alt.Y("category:N", sort="-x", title="Category"),
            color=alt.Color("avg_sentiment:Q", title="Avg sentiment score", scale=alt.Scale(scheme="redyellowgreen")),
            tooltip=["category","articles", alt.Tooltip("avg_sentiment:Q", format=".2f")]
        ).properties(height=240)
        st.altair_chart(bar, use_container_width=True)
    else:
        st.info("No category data")

    st.markdown("---")

    # Donut: category distribution
    if not cat_agg.empty:
        pie = alt.Chart(cat_agg).mark_arc(innerRadius=50).encode(
            theta=alt.Theta("articles:Q"),
            color=alt.Color("category:N", title="Category"),
            tooltip=["category","articles"]
        ).properties(height=220, title="Category distribution (donut)")
        st.altair_chart(pie, use_container_width=True)

    st.markdown("---")

    # Scatter: sentiment_score vs published date
    if not filt.empty and filt["published"].notna().any():
        sc = filt.dropna(subset=["published"]).copy()
        # alt requires numeric x; use epoch seconds
        sc["ts"] = sc["published"].astype("int64")//10**9
        scatter = alt.Chart(sc).mark_circle(opacity=0.8).encode(
            x=alt.X("ts:Q", title="Published (epoch)"),
            y=alt.Y("sentiment_score:Q", title="Sentiment score"),
            size=alt.Size("news_id:Q", legend=None, scale=alt.Scale(range=[10,200])),
            color=alt.Color("category:N", title="Category"),
            tooltip=["title","category","topic", alt.Tooltip("sentiment_score:Q", format=".2f"), "source"]
        ).properties(height=240)
        st.altair_chart(scatter, use_container_width=True)
    else:
        st.info("Insufficient data for scatter")

    st.markdown("---")

    # Heatmap: categories over time (pivot)
    if not daily_cat_filt.empty:
        # pivot to matrix: date x category with articles
        heat = daily_cat_filt.copy()
        # convert date back to datetime for altair
        heat["date_dt"] = pd.to_datetime(heat["date"])
        heat_chart = alt.Chart(heat).mark_rect().encode(
            x=alt.X("date_dt:T", title="Date"),
            y=alt.Y("category:N", title="Category"),
            color=alt.Color("articles:Q", title="Articles"),
            tooltip=["date","category","articles"]
        ).properties(height=300)
        st.altair_chart(heat_chart, use_container_width=True)
    else:
        st.info("No timeline data")

# Raw data (expand)
with st.expander("Show Filtered Raw data"):
    cols = ["news_id","title","published","category","topic","source","sentiment","sentiment_score","link"]
    cols = [c for c in cols if c in filt.columns]
    st.dataframe(filt[cols].sort_values("published", ascending=False), use_container_width=True)
