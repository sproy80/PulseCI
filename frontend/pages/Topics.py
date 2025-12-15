#topics_pg.py

import streamlit as st
import httpx
import asyncio
import pandas as pd
import json
from handler import topics_handler as th

st.set_page_config(page_title="Topics", layout="wide")

#=============================================================


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






#=================================================================================================================







API_BASE = "http://127.0.0.1:8000/topics/api/topics"

# ---- Async API helpers ---- #
async def fetch_topics():
    # async with httpx.AsyncClient() as client:
    #     r = await client.get(API_BASE + "/")
    #     return r.json()
    r = await th.get_all_topics()
    return r

async def add_topic(topic_name):
    # async with httpx.AsyncClient() as client:
    #     r = await client.post(API_BASE + "/", params={"topic_name": topic_name})
    #     return r.json()
    r = await th.add_topic(topic_name=topic_name)
    # print(r)
    # st.success(f"{str(r)} Topics added")
    # st.toast("Topic added successfully!")
    # asyncio.sleep(5)
    # return r

# async def update_topic_flag(topic_id, flag):
#     async with httpx.AsyncClient() as client:
#         r = await client.put(f"{API_BASE}/{topic_id}", params={"active_flag": flag})
#         r.raise_for_status()  # raise HTTPError if response is not 2xx
#         return r.json()        # now r.json() will succeed
       

# async def delete_topic(topic_id):
#     async with httpx.AsyncClient() as client:
#         r = await client.delete(f"{API_BASE}/{topic_id}")
#         return r.json()

# ---------------------------- #

st.title("🗂️ Topic Management (DataTable Mode)")

st.subheader("➕ Add New Topic")
# st.divider()

colA, colB = st.columns(2, gap="small")

colText, colButton = colA.columns(2)



topic_name = colText.text_input(label="", placeholder='Write new Topics here')

if colText.button("Add Topic", use_container_width=False):
    if topic_name.strip():
        asyncio.run(add_topic(topic_name.strip()))
        st.toast("Topic Added!")
        # st.rerun()
    else:
        st.error("Topic name cannot be empty.")



# ======================================================
# SHOW TOPICS IN A DATATABLE WITH BUTTONS IN EACH ROW
# ======================================================

st.subheader("📋 Existing Topics")

topics_list = asyncio.run(fetch_topics())



if not topics_list:
    st.info("No topics found.")
else:
    # Convert to DataFrame
    df = pd.DataFrame(list(topics_list)) # wrap in list

    # st.write("RAW topics_list:", topics_list)
    # st.write("DF columns:", df.columns.tolist())
    # st.write(df)



    # Action columns for UI display
    # df["Toggle Active"] = df["active_flag"].apply(lambda x: "Deactivate" if x == "Y" else "Activate")
    # # df["Toggle Active"] = df["is_active"].apply(lambda x: "Deactivate" if x == "Y" else "Activate")

    # df["Delete"] = "Delete"

    # st.write("Click buttons inside the table to modify topics:")

    # edited_df = st.data_editor(
    #     df,
    #     hide_index=True,
    #     column_config={
    #         "topic_id": st.column_config.NumberColumn("ID", disabled=True),
    #         "topic_name": st.column_config.TextColumn("Topic", disabled=True),
    #         "active_flag": st.column_config.TextColumn("Active", disabled=True),
    #         "Toggle Active": st.column_config.ButtonColumn("Toggle Active"),
    #         "Delete": st.column_config.ButtonColumn("Delete")
    #     },
    #     use_container_width=True,
    # )

    # Action column
    df["Action"] = "None"

    edited_df = st.data_editor(
        df,
        hide_index=True,
        column_config={
            "topic_id": st.column_config.NumberColumn("ID", disabled=True),
            "topic_name": st.column_config.TextColumn("Topic", disabled=True),
            "active_flag": st.column_config.TextColumn("Active", disabled=True),
            "Action": st.column_config.SelectboxColumn(
                "Action",
                options=["None", "Activate", "Deactivate", "Delete"],
            )
        },
        use_container_width=True,
        )
    
    for i, row in edited_df.iterrows():

        action = row["Action"]
        topic_id = int(row["topic_id"])

        if action == "Activate":
            # asyncio.run(update_topic_flag(topic_id, "Y"))
            asyncio.run(th.update_topic_flag(topic_id,"Y"))
            st.success(f"Topic {topic_id} activated.")
            st.rerun()

        if action == "Deactivate":
            # asyncio.run(update_topic_flag(topic_id, "N"))
            asyncio.run(th.update_topic_flag(topic_id,"N"))
            st.success(f"Topic {topic_id} deactivated.")
            st.rerun()

        if action == "Delete":
            # asyncio.run(delete_topic(topic_id))
            asyncio.run(th.delete_topic(topic_id))
            st.warning(f"Topic {topic_id} deleted.")
            st.rerun()



    # # Detect button clicks row by row
    # for i, row in edited_df.iterrows():

    #     # Handle Toggle Active
    #     if row["Toggle Active"] != df.loc[i, "Toggle Active"]:
    #         new_flag = "N" if row["active_flag"] == "Y" else "Y"
    #         asyncio.run(update_topic_flag(int(row["topic_id"]), new_flag))
    #         st.success(f"Topic {row['topic_id']} updated.")
    #         st.rerun()

    #     # Handle DELETE button
    #     if row["Delete"] != df.loc[i, "Delete"]:
    #         asyncio.run(delete_topic(int(row["topic_id"])))
    #         st.warning(f"Topic {row['topic_id']} deleted.")
    #         st.rerun()
