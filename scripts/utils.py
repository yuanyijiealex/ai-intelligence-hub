import hashlib
import os
from datetime import datetime, timezone
from typing import Optional

import requests


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(key)
    return val if val not in (None, "") else default


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def http_get(url: str, timeout: int = 15, user_agent: Optional[str] = None) -> requests.Response:
    headers = {
        "User-Agent": user_agent or "ai-intelligence-hub/1.0",
        "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp


def normalize_url(url: str) -> str:
    return url.strip()


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

