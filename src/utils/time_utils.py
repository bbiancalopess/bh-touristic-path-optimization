from datetime import datetime


def hhmm_to_minutes(hhmm: str) -> int:
    hhmm = hhmm.strip()
    dt = datetime.strptime(hhmm, "%H:%M")
    return dt.hour * 60 + dt.minute


def minutes_to_hhmm(minutes: int) -> str:
    minutes = int(minutes) % (24 * 60)
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"