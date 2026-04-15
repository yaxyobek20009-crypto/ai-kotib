import os
import json
import logging
from datetime import datetime, timedelta, date
import pytz
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")
SCOPES = ["https://www.googleapis.com/auth/calendar"]

CATEGORY_COLORS = {"uchrashuv": "1", "ish": "9", "shaxsiy": "2"}


class CalendarService:
    def __init__(self):
        self.service = self._build_service()
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    def _build_service(self):
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not creds_json:
            raise ValueError("GOOGLE_CREDENTIALS_JSON topilmadi!")
        creds_data = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
        return build("calendar", "v3", credentials=creds)

    def add_event(self, event_data: dict) -> bool:
        try:
            date_str = event_data["date_iso"]
            time_str = event_data.get("time_iso")
            urgent = event_data.get("urgent", False)
            category = event_data.get("category", "ish")
            color_id = "11" if urgent else CATEGORY_COLORS.get(category, "1")

            if time_str:
                start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                start_dt = TASHKENT_TZ.localize(start_dt)
                end_dt = start_dt + timedelta(hours=1)
                event_body = {
                    "summary": event_data["title"],
                    "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Tashkent"},
                    "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Tashkent"},
                    "colorId": color_id,
                }
            else:
                event_body = {
                    "summary": event_data["title"],
                    "start": {"date": date_str},
                    "end": {"date": date_str},
                    "colorId": color_id,
                }

            note_parts = []
            if event_data.get("note"):
                note_parts.append(event_data["note"])
            cat_labels = {"ish": "Ish", "shaxsiy": "Shaxsiy", "uchrashuv": "Uchrashuv"}
            note_parts.append(cat_labels.get(category, ""))
            if urgent:
                note_parts.append("Shoshilinch")
            event_body["description"] = "\n".join(note_parts)

            self.service.events().insert(calendarId=self.calendar_id, body=event_body).execute()
            return True
        except Exception as e:
            logger.error(f"Xato: {e}")
            return False

    def get_today_events(self) -> list:
        today = date.today()
        return self._get_events(today, today)

    def get_week_events(self) -> list:
        today = date.today()
        end = today + timedelta(days=6 - today.weekday())
        return self._get_events(today, end)

    def _get_events(self, start_date: date, end_date: date) -> list:
        try:
            start = TASHKENT_TZ.localize(datetime.combine(start_date, datetime.min.time()))
            end = TASHKENT_TZ.localize(datetime.combine(end_date, datetime.max.time()))
            result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            return [self._parse_event(i) for i in result.get("items", []) if self._parse_event(i)]
        except Exception as e:
            logger.error(f"Xato: {e}")
            return []

    def _parse_event(self, item: dict) -> dict | None:
        try:
            desc = item.get("description", "")
            urgent = "Shoshilinch" in desc
            category = "shaxsiy" if "Shaxsiy" in desc else "uchrashuv" if "Uchrashuv" in desc else "ish"
            start = item.get("start", {})
            time_str = ""
            if "dateTime" in start:
                dt = datetime.fromisoformat(start["dateTime"])
                time_str = dt.strftime("soat %H:%M")
            return {"title": item.get("summary", "Nomsiz"), "time_str": time_str, "category": category, "urgent": urgent}
        except Exception:
            return None
