"""UFCStats HTTP client: rate limit, retries, cache."""

from __future__ import annotations

import random
import time
from pathlib import Path

import requests

from fightmatch.cache import DiskCache, cache_key
from fightmatch.config import ScrapeConfig
from fightmatch.utils.log import log


class RateLimiter:
    """Sleep + jitter between requests."""

    def __init__(self, interval: float = 1.0, jitter: float = 0.3):
        self.interval = interval
        self.jitter = jitter
        self._last = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last
        delay = max(0, self.interval - elapsed)
        if self.jitter:
            delay += random.uniform(0, self.jitter)
        if delay > 0:
            time.sleep(delay)
        self._last = time.monotonic()


def fetch(
    url: str,
    config: ScrapeConfig,
    cache: DiskCache | None,
    rate_limiter: RateLimiter | None,
) -> bytes:
    """Fetch URL with cache, rate limit, retries. Returns response body bytes."""
    if cache:
        cached = cache.get_or_none(url)
        if cached is not None:
            return cached
    if rate_limiter:
        rate_limiter.wait()
    headers = {"User-Agent": config.user_agent}
    last_error: Exception | None = None
    for attempt in range(config.max_retries):
        try:
            r = requests.get(
                url,
                headers=headers,
                timeout=config.request_timeout,
            )
            r.raise_for_status()
            body = r.content
            if cache:
                cache.set(url, body)
            return body
        except requests.RequestException as e:
            last_error = e
            if attempt < config.max_retries - 1:
                backoff = config.retry_backoff_base ** attempt
                time.sleep(backoff)
    raise last_error or RuntimeError("fetch failed")


def discover_events_since(
    since_date: str,
    config: ScrapeConfig,
    cache: DiskCache | None,
    rate_limiter: RateLimiter | None,
) -> list[dict]:
    """Load events list page and return events on or after since_date (YYYY-MM-DD)."""
    from .parse import parse_events_list

    url = f"{config.base_url}/statistics/events/completed?page=all"
    html = fetch(url, config, cache, rate_limiter).decode("utf-8", errors="replace")
    events = parse_events_list(html, config.base_url)
    out = []
    for e in events:
        d = e.get("date")
        if not d:
            out.append(e)
            continue
        # Normalize date: YYYY-MM-DD or "Mon DD, YYYY"
        import re
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", d)
        if not m:
            # try "Jan 1, 2024"
            from datetime import datetime
            try:
                dt = datetime.strptime(d.strip(), "%B %d, %Y")
                d = dt.strftime("%Y-%m-%d")
            except ValueError:
                try:
                    dt = datetime.strptime(d.strip(), "%b %d, %Y")
                    d = dt.strftime("%Y-%m-%d")
                except ValueError:
                    out.append(e)
                    continue
        else:
            d = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        if d >= since_date:
            e["date"] = d
            out.append(e)
    return out


def scrape_since(
    since_date: str,
    raw_dir: Path,
    config: ScrapeConfig | None = None,
) -> None:
    """
    Scrape events since date; save raw HTML under raw_dir/ufcstats/.
    Structure: raw_dir/ufcstats/events.html, raw_dir/ufcstats/events/<id>.html,
    raw_dir/ufcstats/fights/<bout_id>.html.
    """
    config = config or ScrapeConfig()
    cache = DiskCache(Path(raw_dir) / "ufcstats", ttl_seconds=config.rate_limit_seconds * 0 + 86400 * 7)
    rate_limiter = RateLimiter(config.rate_limit_seconds, config.rate_limit_jitter)

    events = discover_events_since(since_date, config, cache, rate_limiter)
    log(f"Found {len(events)} events since {since_date}")

    events_dir = Path(raw_dir) / "ufcstats" / "events"
    fights_dir = Path(raw_dir) / "ufcstats" / "fights"
    events_dir.mkdir(parents=True, exist_ok=True)
    fights_dir.mkdir(parents=True, exist_ok=True)

    from .parse import parse_event_page, parse_fight_details

    for ev in events:
        event_id = ev.get("event_id")
        url = ev.get("url")
        if not url:
            continue
        log(f"Event: {event_id}")
        html = fetch(url, config, cache, rate_limiter).decode("utf-8", errors="replace")
        (events_dir / f"{event_id}.html").write_text(html, encoding="utf-8")
        event_info, bouts, fight_links = parse_event_page(html, event_id, config.base_url)
        for fl in fight_links:
            bout_id = fl.get("bout_id")
            u = fl.get("url")
            if not u:
                continue
            try:
                body = fetch(u, config, cache, rate_limiter)
                (fights_dir / f"{bout_id}.html").write_bytes(body)
            except Exception as e:
                log(f"Skip fight {bout_id}: {e}")
