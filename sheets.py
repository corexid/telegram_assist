import json
import logging
import os
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_CREDENTIALS, GOOGLE_CREDENTIALS_JSON, GOOGLE_SHEETS_ID


def _get_credentials() -> Optional[Credentials]:
    if GOOGLE_CREDENTIALS_JSON and os.path.exists(GOOGLE_CREDENTIALS_JSON):
        return Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_JSON,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
    if GOOGLE_CREDENTIALS:
        data = json.loads(GOOGLE_CREDENTIALS)
        return Credentials.from_service_account_info(
            data,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
    return None


def append_lead(name: str, phone: str, budget: str, user_id: int) -> bool:
    if not GOOGLE_SHEETS_ID:
        logging.warning("GOOGLE_SHEETS_ID is not set; lead not sent to Sheets")
        return False

    creds = _get_credentials()
    if not creds:
        logging.warning("Google credentials are not set; lead not sent to Sheets")
        return False

    try:
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEETS_ID).sheet1
        sheet.append_row([name, phone, budget, str(user_id)], value_input_option="RAW")
        return True
    except Exception as exc:
        logging.error("Failed to append lead to Google Sheets: %s", exc)
        return False
