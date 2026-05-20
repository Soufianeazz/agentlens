"""
Demo freshness keeper — Tier-2 narrow-scope auto-remediation.

Calls POST /admin/seed-demo on agentlens.one every day. The endpoint is idempotent
(see api/routes/admin.py:_do_seed_demo) and tops up the demo dataset so that every
visitor lands on a dashboard showing recent activity.

Why this exists:
  - seed_demo_on_startup() only runs when the container restarts.
  - Railway can run the same container for a week+ without a deploy.
  - After 24h with no traffic, the demo dashboard shows "0 calls in 24h" → kills conversion.

This agent's blast radius is narrow on purpose:
  - Only one endpoint called (/admin/seed-demo).
  - Endpoint is idempotent — replays don't accumulate spam data.
  - Cannot delete, cannot mutate user data, cannot change billing.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request

logger = logging.getLogger("demo-freshness")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

URL = os.environ.get("AGENTLENS_URL", "https://www.agentlens.one").rstrip("/")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

# Retry transient infrastructure failures (Railway cold-start, 502, connection reset).
# Don't retry on 4xx — those are real bugs in our request, not flakes.
RETRY_HTTP_CODES = {500, 502, 503, 504}
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (5, 20)  # gap before attempt 2, gap before attempt 3


def _attempt() -> tuple[bool, str]:
    req = urllib.request.Request(
        f"{URL}/admin/seed-demo",
        method="POST",
        headers={
            "X-Admin-Token": ADMIN_TOKEN,
            "Content-Type": "application/json",
            "User-Agent": "agentlens-demo-freshness/1.0",
        },
        data=b"{}",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            payload = json.loads(body) if body else {}
            logger.info(
                "Demo refreshed: status=%s requests=%s recent_24h=%s",
                payload.get("status"),
                payload.get("requests_total") or payload.get("requests"),
                payload.get("recent_24h", "?"),
            )
            return True, "ok"
    except urllib.error.HTTPError as e:
        snippet = e.read().decode("utf-8", errors="replace")[:300]
        transient = e.code in RETRY_HTTP_CODES
        logger.warning("HTTP %s (transient=%s): %s", e.code, transient, snippet)
        return False, f"http-{e.code}" if not transient else "transient"
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        logger.warning("Network error (transient): %s", e)
        return False, "transient"
    except Exception:
        logger.exception("Demo refresh failed (non-retryable)")
        return False, "fatal"


def main() -> int:
    if not ADMIN_TOKEN:
        logger.error("ADMIN_TOKEN missing — refusing to proceed")
        return 1

    for attempt in range(1, MAX_ATTEMPTS + 1):
        ok, reason = _attempt()
        if ok:
            return 0
        if reason != "transient" or attempt == MAX_ATTEMPTS:
            logger.error("Demo refresh failed after %d attempt(s); last reason=%s", attempt, reason)
            return 1
        gap = BACKOFF_SECONDS[attempt - 1]
        logger.info("Transient failure — retrying in %ds (attempt %d/%d)", gap, attempt + 1, MAX_ATTEMPTS)
        time.sleep(gap)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
