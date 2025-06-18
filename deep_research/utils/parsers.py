import re
import datetime
from dateutil import parser as date_parser


def clean_text(text):
    if text is None:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def parse_date(text):
    if not text:
        return None
    try:
        return date_parser.parse(text, fuzzy=True).date()
    except Exception:
        return None


def parse_amount(text):
    if not text:
        return None
    # Simple extraction of numbers (EUR/XOF amounts etc.)
    match = re.search(r"([\d\.,]+)", text.replace('\xa0', ' '))
    if match:
        try:
            amt = match.group(1).replace(",", ".").replace(" ", "")
            return float(amt)
        except Exception:
            return None
    return None


def derive_sector(title, description):
    # Dummy sector tagging; to be improved with NLP
    sectors = {
        "agri": ["agriculture", "agro", "farm"],
        "tech": ["tech", "numérique", "digital", "informatique"],
        "health": ["santé", "health", "medical"],
    }
    text = (title or "") + " " + (description or "")
    text = text.lower()
    for sector, keywords in sectors.items():
        if any(k in text for k in keywords):
            return sector
    return None