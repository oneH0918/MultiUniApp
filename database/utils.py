from datetime import datetime


def format_date(date_str):
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y/%m/%d")
        except ValueError:
            return None
    return None
