import os, datetime as dt
from dotenv import load_dotenv

load_dotenv()

CST_OFFSET = 8

def now_utc():
    return dt.datetime.utcnow().replace(microsecond=0)

def utc_to_cst(d):
    return d + dt.timedelta(hours=CST_OFFSET)

def today_strings():
    u = now_utc()
    c = utc_to_cst(u)
    return u.strftime('%Y-%m-%d'), c.strftime('%Y-%m-%d')

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
