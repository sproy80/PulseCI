import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(page_title="News Analytics Dashboard", page_icon="📰", layout="wide")

# ---------------------------
# Demo data
# ---------------------------
np.random.seed(42)

topics = ["AI", "Economy", "Politics", "Health", "Sports", "Tech"]
sources = ["Reuters", "AP", "BBC", "Bloomberg", "NYTimes", "Guardian"]

# Generate mock news items
def make_news(n=60):
    base = datetime.utcnow()
    rows = []
    for i in range(n):
        t = np.random.choice(topics)
        s = np.random.choice(sources)
        published = base - timedelta(hours=np.random.randint(0, 240))
        title = f"{t} headline #{i+1} - {s}"
        summary = f"Short summary for {t} story #{i+1} from {s}."
        sentiment = np.random.normal(loc=0.1 if t == "AI" else 0, scale=0.3)
        rows.append(
            dict(
                title=title,
                summary=summary,
                topic=t,
                source=s,
                published=published,
                sentiment=np.clip(sentiment, -1, 1),
            )
        )
    return pd.DataFrame(rows)

news_df = make_news()

# Build a daily metrics frame (counts and average sentiment)
def make_daily(df):
    d = df.copy()
    d["date"] = d["published"].dt.date
    by_day = d.groupby("date").agg(
        articles=("title", "count"),
        avg_sentiment=("sentiment", "mean")
    ).reset_index().sort_values("date")
    # mock “engagement” metric
    by_day["engagement"] = (by_day["articles"] * (0.5 + np.random.rand(len(by_day)))).round(0)
    return by_day

daily = make_daily(news_df)

# ---------------------------
# Sidebar filters
# ---------------------------
st.sidebar.header("Filters")
topic_sel = st.sidebar.multiselect("Topics", options=topics, default=topics[:3])
source_sel = st.sidebar.multiselect("Sources", options=sources, default=sources[:3])
date_min, date_max = news_df["published"].min().date(), news_df["published"].max().date()
date_range = st.sidebar.date_input("Date range", (date_min, date_max), min_value=date_min, max_value=date_max)

# Apply filters
filt = news_df.copy()
if topic_sel:
    filt = filt[filt["topic"].isin(topic_sel)]
if source_sel:
    filt = filt[filt["source"].isin(source_sel)]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    filt = filt[(filt["published"].dt.date >= start) & (filt["published"].dt.date <= end)]

daily_filt = make_daily(filt)

# ---------------------------
# Header
# ---------------------------
st.title("📰 News Analytics Dashboard")

# ---------------------------
# KPIs
# ---------------------------
# ---------------------------
# KPIs (fixed)
# ---------------------------
# col1, col2, col3, col4 = st.columns(4,border=True)

# ---------------------------
# KPIs (with compact sparklines)
# ---------------------------
col1, col2, col3, col4 = st.columns(4, border=True)

total_articles = int(filt.shape[0])
avg_sent = float(filt["sentiment"].mean()) if not filt.empty else 0.0
latest_day = daily_filt.iloc[-1] if not daily_filt.empty else None
articles_today = int(latest_day["articles"]) if latest_day is not None else 0
engagement_today = int(latest_day["engagement"]) if latest_day is not None else 0

# Guard for previous day values
prev_articles = int(daily_filt["articles"].iloc[-2]) if len(daily_filt) > 1 else 0
prev_engagement = int(daily_filt["engagement"].iloc[-2]) if len(daily_filt) > 1 else 0

def sparkline(data, y, kind="line"):
    """Return a minimalist sparkline chart."""
    if data.empty:
        return None
    chart = (
        alt.Chart(data.reset_index())
        .mark_line() if kind=="line" else alt.Chart(data.reset_index()).mark_bar()
    )
    chart = chart.encode(
        x=alt.X("date:T", axis=None),
        y=alt.Y(f"{y}:Q", axis=None)
    ).properties(height=60).configure_view(strokeWidth=0)
    return chart

with col1:
    st.metric("Total articles", total_articles, delta=articles_today - prev_articles)
    if not daily_filt.empty:
        st.altair_chart(sparkline(daily_filt.set_index("date"), "articles", kind="line"), use_container_width=True)

with col2:
    st.metric("Avg sentiment", f"{avg_sent:.2f}", delta=f"{(avg_sent - 0):.2f}")
    if not daily_filt.empty:
        st.altair_chart(sparkline(daily_filt.set_index("date"), "avg_sentiment", kind="line"), use_container_width=True)

with col3:
    st.metric("Articles (latest day)", articles_today, delta=articles_today - prev_articles)
    if not daily_filt.empty:
        st.altair_chart(sparkline(daily_filt.set_index("date"), "articles", kind="bar"), use_container_width=True)

with col4:
    st.metric("Engagement (latest day)", engagement_today, delta=engagement_today - prev_engagement)
    if not daily_filt.empty:
        st.altair_chart(sparkline(daily_filt.set_index("date"), "engagement", kind="bar"), use_container_width=True)


# ---------------------------
# Layout: News feed (left) and charts (right)
# ---------------------------
def show_news():

    # ---------------------------
# News feed with tabs (compact & details)
# ---------------------------

    # st.subheader("Latest news")

    feed = filt.sort_values("published", ascending=False).reset_index(drop=True).head(20)

    if feed.empty:
        st.info("No news available for selected filters.")
    else:
        # Right-aligned tabs with icons
        tab1, tab2 = st.tabs([":material/view_module: Compact view", ":material/table: Details view"])

        # ---------------------------
        # Compact View (cards grid with scroll)
        # ---------------------------
        with tab1:
            # Scrollable container
            st.markdown(
                """
                <style>
                .news-container {
                    max-height: 400px;
                    overflow-y: auto;
                    padding-right: 5px;
                }
                .news-card {
                    display: flex;
                    flex-direction: column;
                    height: 200px; /* fixed card height */
                    border-radius: 0.75rem;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                    background-color: white;
                    margin-bottom: 1rem;
                    overflow: hidden;
                }
                .news-card img {
                    width: 100%;
                    height: 100px;
                    object-fit: cover;
                }
                .news-body {
                    flex: 1;
                    padding: 0.8rem;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                }
                .news-title {
                    font-weight: 600;
                    font-size: 1.05rem;
                    margin-bottom: 0.3rem;
                }
                .news-title a {
                    text-decoration: none;
                    color: black;
                }
                .news-title a:hover {
                    text-decoration: underline;
                    color: #1a73e8;
                }
                .news-meta {
                    font-size: 0.85rem;
                    color: gray;
                    margin-bottom: 0.5rem;
                }
                .news-summary {
                    font-size: 0.9rem;
                    margin-bottom: 0.5rem;
                    max-height: 60px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .news-footer {
                    font-size: 0.8rem;
                    font-weight: 500;
                    color: #555;
                }
                </style>
                <div class="news-container">
                """,
                unsafe_allow_html=True,
            )

            cols = st.columns(2, gap="large")
            for i, row in feed.iterrows():
                col = cols[i % 2]  # alternate between columns

                # Dummy image + dummy link
                dummy_img = f"https://placehold.co/600x400?text={row['topic']}"
                dummy_url = f"https://example.com/news/{i+1}"

                # Sentiment badge
                if row["sentiment"] > 0.2:
                    sentiment_label = f"🟢 Positive ({row['sentiment']:.2f})"
                elif row["sentiment"] < -0.2:
                    sentiment_label = f"🔴 Negative ({row['sentiment']:.2f})"
                else:
                    sentiment_label = f"⚪ Neutral ({row['sentiment']:.2f})"

                col.markdown(
                    f"""
                    <div class="news-card">
                        <img src="{dummy_img}">
                        <div class="news-body">
                            <div>
                                <div class="news-title"><a href="{dummy_url}" target="_blank">{row['title']}</a></div>
                                <div class="news-meta">{row['source']} • {row['published'].strftime('%Y-%m-%d %H:%M UTC')}</div>
                                <div class="news-summary">{row['summary']}</div>
                            </div>
                            <div class="news-footer">
                                Topic: <span style="background:#eef; padding:2px 6px; border-radius:6px;">{row['topic']}</span>
                                &nbsp; | &nbsp; {sentiment_label}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)  # close scroll container
            st.caption("Showing up to 20 most recent items.")

        # ---------------------------
        # Details View (full table)
        # ---------------------------
        with tab2:
            st.dataframe(
                feed[["title", "summary", "topic", "source", "published", "sentiment"]],
                use_container_width=True,
                hide_index=True
            )


def show_news_analysis_chart():
    st.subheader("Trends and distribution")

    # Trend: Articles by day (Altair)
    if not daily_filt.empty:
        base = alt.Chart(daily_filt).encode(x=alt.X("date:T", title="Date"))
        line_articles = base.mark_line(point=True).encode(
            y=alt.Y("articles:Q", title="Articles")
        ).properties(height=220)
        st.altair_chart(line_articles, use_container_width=True)
    else:
        st.info("No data for selected filters.")

    # Trend: Avg sentiment by day
    if not daily_filt.empty:
        line_sent = alt.Chart(daily_filt).mark_area(opacity=0.3).encode(
            x="date:T", y=alt.Y("avg_sentiment:Q", title="Average sentiment")
        ).properties(height=220)
        st.altair_chart(line_sent, use_container_width=True)

    # Distribution: Articles by topic and source
    agg = (
        filt.groupby(["topic", "source"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    if not agg.empty:
        top_bar = alt.Chart(agg).mark_bar().encode(
            x=alt.X("count:Q", title="Articles"),
            y=alt.Y("topic:N", sort="-x", title="Topic"),
            color="source:N",
            tooltip=["topic", "source", "count"]
        ).properties(height=280)
        st.altair_chart(top_bar, use_container_width=True)

    # Quick native charts (optional examples)
    st.line_chart(daily_filt.set_index("date")["articles"])
    st.area_chart(daily_filt.set_index("date")[["avg_sentiment"]])


# left, right = st.columns([1.3, 1.7])



 

# News feed
# with left:

news_expander = st.expander("Latest News & Analysis")   
with news_expander:

    left, right = st.columns([3, 2],border=True)

    with left:
            
        
        # with news_expander:
            show_news()
            # ---------------------------
            # News feed with tabs (compact & details)
    # ---------------------------  


    # Charts
    with right:
            show_news_analysis_chart()

# ---------------------------
# Raw data (optional)
# ---------------------------
# with st.expander("Show filtered raw data"):
#     st.dataframe(filt.sort_values("published", ascending=False), use_container_width=True)