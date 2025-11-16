
def h2m(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def h2hhmm(m: int) -> str:
    m = int(m)
    return f"{m//60:02d}:{m%60:02d}"