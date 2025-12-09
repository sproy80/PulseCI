#topics_pg.py

import streamlit as st
import httpx
import asyncio
import pandas as pd
import json
from handler import topics_handler as th

st.set_page_config(page_title="Topics", layout="wide")

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
