# U.S. Economic Dashboard

| File | Chart |
| --- | --- |
| `panel_1.py` | Cost of living |
| `panel_2.py` | Rental affordability |
| `panel_3.py` | Inflation and interest rates |
| `panel_4.py` | Macroeconomic correlations |

Extract the whole ZIP into a new folder. Open PowerShell inside the extracted
`economic_dashboard` folder. With Python 3.10 or newer, run these commands
one at a time in the same window.

```powershell
python -m pip install -r requirements.txt
$env:FRED_API_KEY = "your-real-key"
python dashboard.py
```

Replace `your-real-key` with your FRED API key before running the second
command. If you've already set it in this PowerShell window, skip that
command. On macOS or Linux use `export FRED_API_KEY="your-real-key"` instead.

When Dash prints its address, open <http://127.0.0.1:8050/>. Select a card
for the full-page chart and use **All panels** to return. To open one panel
on its own, run its numbered script, for example `python panel_3.py`.

All four panels load observations through the [FRED API](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)
on startup. A valid key and an internet connection are required. The first
load usually takes 1–2 minutes because the map requests rent and income for
every state and D.C. The app spaces requests, reuses series shared by panels,
and retries rate limits and transient failures. Data stays in memory for the
session. Restart the app to refresh observations within the chart windows,
which extend through 2025 where available. Open the browser once the terminal
shows that Dash is running. The state outlines are bundled from the
[Plotly USA topology](https://cdn.plot.ly/un/usa_110m.json).

The map compares each state's household income with the median of the available
state and D.C. incomes and adjusts for local rent price parity. It shows years
for which matched rent and income observations are available.
