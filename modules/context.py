"""
Personal context module for Daily Reflections.

Gathers git activity, calendar events, Gmail summary, and open loops
to inject personal context into the morning show script.
"""

import os
import subprocess
from datetime import datetime, timedelta


# Key project directories to scan for git activity
PROJECT_DIRS = [
    os.path.expanduser("~/Projects/KitchenOS/frontend"),
    os.path.expanduser("~/Projects/gusto-data-platform"),
    os.path.expanduser("~/Projects/daily-reflections"),
    os.path.expanduser("~/Projects/forge"),
    os.path.expanduser("~/Projects/claudia"),
    os.path.expanduser("~/Projects/gusto-data"),
]

OPEN_LOOPS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "open_loops.md")


def get_git_activity():
    """Scan key project dirs for yesterday's git commits."""
    results = []
    for project_dir in PROJECT_DIRS:
        if not os.path.isdir(project_dir):
            continue
        project_name = os.path.basename(project_dir)
        # Handle nested dirs like KitchenOS/frontend
        if project_name == "frontend":
            project_name = "KitchenOS"
        try:
            output = subprocess.run(
                ["git", "log", "--oneline", "--since=yesterday", "--no-merges"],
                capture_output=True, text=True, cwd=project_dir, timeout=5,
            )
            lines = [l.strip() for l in output.stdout.strip().split("\n") if l.strip()]
            if lines:
                # Summarize: "KitchenOS (3 commits: auth fix, sync update, ...)"
                summaries = [l.split(" ", 1)[1] if " " in l else l for l in lines[:5]]
                results.append(f"{project_name} ({len(lines)} commit{'s' if len(lines) != 1 else ''}): {', '.join(summaries[:3])}")
        except Exception:
            pass
    return results


def get_calendar_events():
    """Fetch today's calendar events via Google Calendar API (ADC)."""
    try:
        from google.auth import default
        from googleapiclient.discovery import build

        creds, _ = default(scopes=["https://www.googleapis.com/auth/calendar.readonly"])
        service = build("calendar", "v3", credentials=creds)

        from datetime import timezone
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        result = []
        for event in events[:8]:
            start = event["start"].get("dateTime", event["start"].get("date", ""))
            summary = event.get("summary", "Untitled")
            if "T" in start:
                time_str = datetime.fromisoformat(start.replace("Z", "+00:00")).strftime("%-I:%M %p")
            else:
                time_str = "All day"
            result.append({"time": time_str, "summary": summary})
        return result
    except Exception as e:
        print(f"Calendar fetch failed (expected if ADC scope not configured): {e}")
        return []


def get_gmail_summary():
    """Fetch recent email subjects via Gmail API (ADC). Fails gracefully."""
    try:
        from google.auth import default
        from googleapiclient.discovery import build

        creds, _ = default(scopes=["https://www.googleapis.com/auth/gmail.readonly"])
        service = build("gmail", "v1", credentials=creds)

        # Get messages from yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")
        results = service.users().messages().list(
            userId="me", q=f"after:{yesterday}", maxResults=5
        ).execute()

        messages = results.get("messages", [])
        summaries = []
        for msg in messages[:5]:
            msg_data = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["Subject", "From"],
            ).execute()
            headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject", "No subject")
            sender = headers.get("From", "Unknown")
            # Clean sender to just name
            if "<" in sender:
                sender = sender.split("<")[0].strip().strip('"')
            summaries.append({"subject": subject, "from": sender})
        return summaries
    except Exception as e:
        print(f"Gmail fetch failed (expected if scope not configured): {e}")
        return []


def get_open_loops():
    """Read open loops from data/open_loops.md."""
    if not os.path.exists(OPEN_LOOPS_PATH):
        return []
    try:
        with open(OPEN_LOOPS_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        # Parse simple markdown — look for lines starting with - or numbered items
        loops = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                loops.append(line[2:].strip())
            elif len(line) > 3 and line[0].isdigit() and ". " in line[:4]:
                loops.append(line.split(". ", 1)[1].strip())
        return loops[:10]
    except Exception:
        return []


def gather_all_context():
    """
    Gather all personal context and return a formatted prompt section.

    Returns dict with:
        - formatted_prompt_section: str ready for injection into LLM prompt
        - raw: dict with individual data sources
    """
    git = get_git_activity()
    calendar = get_calendar_events()
    gmail = get_gmail_summary()
    loops = get_open_loops()

    parts = ["## YOUR DAY"]

    if calendar:
        cal_items = [f"{e['time']} {e['summary']}" for e in calendar]
        parts.append(f"- Calendar: {', '.join(cal_items)}")

    if git:
        parts.append(f"- Yesterday's work: {'; '.join(git)}")

    if loops:
        parts.append(f"- Open loops: {', '.join(loops[:5])}")

    if gmail:
        mail_items = [f"{e['from']} re: {e['subject']}" for e in gmail[:3]]
        parts.append(f"- Recent email: {', '.join(mail_items)}")

    if len(parts) == 1:
        # Only the header, no data
        formatted = ""
    else:
        formatted = "\n".join(parts)

    return {
        "formatted_prompt_section": formatted,
        "raw": {
            "git": git,
            "calendar": calendar,
            "gmail": gmail,
            "open_loops": loops,
        }
    }


if __name__ == "__main__":
    result = gather_all_context()
    print(result["formatted_prompt_section"] or "No context data available.")
    print("\n--- Raw ---")
    for k, v in result["raw"].items():
        print(f"{k}: {v}")
