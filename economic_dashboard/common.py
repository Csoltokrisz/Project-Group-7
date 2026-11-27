import os
from concurrent.futures import Future
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from threading import Lock
from time import monotonic, sleep

import pandas as pd
import requests
from dash import dcc, html

INK = "#172c3a"
MUTED = "#526572"
BORDER = "#dce5ea"
BG = "#f1f5f7"
FONT = "system-ui, 'Segoe UI', sans-serif"
BLUE = "#24589a"
TEAL = "#177c70"
ORANGE = "#b85c2d"
SEQUENTIAL = ["#e7f0f7", "#92bad4", "#24589a", "#122c50"]
DIVERGING = ["#ac4c27", "#f1d0ba", "#f8fafb", "#a2c8dc", "#24589a"]


def read_fred_key():
    key = os.getenv("FRED_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "FRED_API_KEY is missing in the terminal that started Python.\n"
            'In PowerShell, run: $env:FRED_API_KEY = "your-real-key"\n'
            'On macOS or Linux, run: export FRED_API_KEY="your-real-key"\n'
            "Then run python dashboard.py in that same terminal."
        )
    if len(key) != 32 or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789" for c in key):
        raise SystemExit("FRED_API_KEY must be your 32-character FRED key. Check the value in this terminal.")
    return key


def retry_delay(response, attempt):
    value = response.headers.get("Retry-After", "").strip()
    if value.isascii() and value.isdecimal():
        return max(1, int(value))
    if value:
        try:
            deadline = parsedate_to_datetime(value)
            return max(1, (deadline - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            pass
    return (15 if response.status_code == 429 else 2) * 2 ** attempt


class FredClient:
    URL = "https://api.stlouisfed.org/fred/series/observations"
    # The documented limit is 120 requests per minute. Leave some headroom.
    REQUEST_INTERVAL = 0.6

    def __init__(self, api_key):
        self.api_key = api_key
        self._lock = Lock()
        self._next_request = 0.0
        self._series = {}

    def _wait_for_slot(self):
        while True:
            with self._lock:
                now = monotonic()
                delay = self._next_request - now
                if delay <= 0:
                    self._next_request = now + self.REQUEST_INTERVAL
                    return
            sleep(delay)

    def _fetch(self, series_id):
        for attempt in range(4):
            self._wait_for_slot()
            try:
                response = requests.get(self.URL, params={
                    "series_id": series_id, "api_key": self.api_key, "file_type": "json",
                    "observation_start": "1994-01-01", "observation_end": "2025-12-31",
                    "limit": 100000,
                }, timeout=(8, 25))
            except requests.RequestException:
                if attempt == 3:
                    raise RuntimeError(f"Could not reach the FRED API for {series_id}. Check your connection.") from None
                sleep(2 ** attempt)
                continue
            status = response.status_code
            if response.ok:
                try:
                    return response.json()["observations"]
                except (ValueError, KeyError):
                    raise RuntimeError(f"FRED returned an invalid response for {series_id}.") from None
            if status == 429 or 500 <= status <= 599:
                delay = retry_delay(response, attempt)
                if status == 429:
                    with self._lock:
                        self._next_request = max(self._next_request, monotonic() + min(delay, 120))
                if attempt < 3 and delay <= 120:
                    if status != 429:
                        sleep(delay)
                    continue
            if status in (400, 401, 403):
                raise RuntimeError(f"FRED rejected the request for {series_id}. Check your API key and series access.")
            if status == 429:
                raise RuntimeError(f"FRED is still rate-limiting {series_id}. Wait a few minutes and restart.")
            raise RuntimeError(f"FRED returned HTTP {status} for {series_id}.")

    def annual_series(self, series_id):
        # Share a single in-flight request for any series used by multiple panels.
        with self._lock:
            pending = self._series.get(series_id)
            if pending is None:
                pending = self._series[series_id] = Future()
                owner = True
            else:
                owner = False
        if owner:
            try:
                rows = self._fetch(series_id)
                values = pd.to_numeric(pd.Series([row["value"] for row in rows], dtype=object), errors="coerce")
                years = pd.Index([int(row["date"][:4]) for row in rows], dtype=int, name="Year")
                pending.set_result(values.groupby(years).mean())
            except BaseException as error:
                pending.set_exception(error)
                raise
        return pending.result()

    def annual_data(self, series_ids):
        return pd.DataFrame({series_id: self.annual_series(series_id) for series_id in series_ids}).sort_index()


def detail_graph(*, tall=False, **props):
    # Dash gives responsive graphs an inline 100% height. Give that percentage
    # a parent with a definite height so controls never share the plot's space.
    frame = "chart-frame chart-frame-tall" if tall else "chart-frame"
    return html.Div(dcc.Graph(responsive=True, **props), className=frame)


def style_figure(fig):
    fig.update_layout(template="plotly_white", font=dict(family=FONT, color=INK),
                      paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
    fig.update_xaxes(gridcolor=BG, automargin=True)
    fig.update_yaxes(gridcolor=BG, automargin=True)
    return fig
