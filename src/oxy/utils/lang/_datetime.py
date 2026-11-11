from datetime import datetime


def timestamp_millis(t: datetime | None = None) -> int:
    if t is None:
        t = datetime.now()
    return int(t.timestamp() * 1000)


def datetime_format(t: datetime | None = None) -> str:
    if t is None:
        t = datetime.now()
    return t.strftime("%Y-%m-%d %H:%M:%S")
