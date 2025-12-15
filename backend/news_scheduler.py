# news_scheduler.py

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
import pandas as pd

from news_parser import get_all_topics, parse_google

console = Console()

EXCEL_FILE = r"C:\Projects\ml\PulseCI\news_analysis.xlsx"
NEWS_SHEET = "news"


# -------------------------------------------------------------------------
# SAFE EXCEL WRITERS  (DO NOT DELETE OTHER SHEETS)
# -------------------------------------------------------------------------

async def clear_news_sheet():
    """Clears only the 'news' sheet without touching other sheets."""

    empty_df = pd.DataFrame(columns=["news_id", "title", "link", "published", "summary"])

    def _write():
        with pd.ExcelWriter(
            EXCEL_FILE,
            mode="a",
            if_sheet_exists="replace",   # replaces ONLY this sheet
            engine="openpyxl"
        ) as writer:
            empty_df.to_excel(writer, sheet_name=NEWS_SHEET, index=False)

    await asyncio.to_thread(_write)
    return True


async def save_news_sheet(df: pd.DataFrame):
    """Safely writes the news data back to Excel."""

    def _write():
        with pd.ExcelWriter(
            EXCEL_FILE,
            mode="a",
            if_sheet_exists="replace",
            engine="openpyxl"
        ) as writer:
            df.to_excel(writer, sheet_name=NEWS_SHEET, index=False)

    await asyncio.to_thread(_write)
    return True


# -------------------------------------------------------------------------
# MAIN JOB
# -------------------------------------------------------------------------

async def run_news_job():
    console.rule("[bold blue]🚀 NEWS PARSER JOB STARTED")

    console.print(
        Panel.fit(
            Text("🔍 Fetching Topics & Parsing Google News...\nPlease wait...", style="bold magenta"),
            border_style="bright_blue"
        )
    )

    # Step 1 — Clear sheet
    await clear_news_sheet()

    # Step 2 — Get topics
    topics = await get_all_topics()

    # Step 3 — Parse news
    today = datetime.today().strftime("%m-%d-%Y")
    one_month_ago = (datetime.today() - timedelta(days=30)).strftime("%m-%d-%Y")

    news_df = await parse_google(
        topics,
        start_dt=one_month_ago,
        end_dt=today
    )

    # Step 4 — Assign auto IDs
    # news_df.insert(0, "news_id", range(1, len(news_df) + 1))

    # Step 4 — Assign auto IDs safely
    if "news_id" not in news_df.columns:
        news_df.insert(0, "news_id", range(1, len(news_df) + 1))
    else:
        news_df["news_id"] = range(1, len(news_df) + 1)


    # Step 5 — Save data
    await save_news_sheet(news_df)

    # Completion Panel
    console.print(
        Panel(
            f"[bold green]✔ Completed fresh run\n"
            f"[white]Fetched: [cyan]{len(news_df)}[/cyan] articles\n"
            f"[white]Saved successfully into Excel",
            border_style="green",
        )
    )

    next_run_time = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M:%S")
    # console.print(
    #     Panel(
    #         Text(
    #             f"⏭ Next run at [bold yellow]{next_run_time}[/bold yellow]",
    #             style="bold blue"
    #         ),
    #         border_style="bright_magenta"
    #     )
    # )

    console.print(
    Panel(
        Text.from_markup(f"⏭ Next run at [bold yellow]{next_run_time}[/bold yellow]"),
        border_style="bright_magenta"
        )
    )


    console.rule("")


def job_wrapper():
    asyncio.run(run_news_job())


# -------------------------------------------------------------------------
# STARTUP BANNER
# -------------------------------------------------------------------------

def show_start_banner():
    table = Table(title="NEWS PARSER SCHEDULER", box=box.DOUBLE_EDGE, style="bold blue")

    table.add_column("Info", style="bold yellow")
    table.add_row("Runs every 5 minutes")
    table.add_row("Fetches Google RSS news for topics")
    table.add_row("Clears only 'news' sheet each time (SAFE)")
    table.add_row("Beautiful UI with rich console")
    table.add_row("Does NOT delete other Excel sheets")

    console.print(table)
    console.print()


# -------------------------------------------------------------------------
# MAIN LOOP
# -------------------------------------------------------------------------

if __name__ == "__main__":
    console.clear()
    show_start_banner()

    # Schedule to run every 5 minutes
    schedule.every(5).minutes.do(job_wrapper)

    # Run immediately on startup
    job_wrapper()

    # Infinite scheduler loop
    while True:
        schedule.run_pending()
        time.sleep(1)
