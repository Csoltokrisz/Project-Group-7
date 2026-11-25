import requests
import plotly.graph_objects as go
import os
from dash import Dash, dcc, html, Input, Output, ctx, no_update, callback

API_KEY = os.environ.get("FRED_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing FRED_API_KEY environment variable.")
URL = "https://api.stlouisfed.org/fred/series/observations"

# FRED series for each category
SERIES = {
    "housing": {
        "id": "CUUR0000SAH1",   # CPI shelter
        "label": "Housing (CPI Shelter index)",
        "color": "#2f6fed",
        "text": "Shelter costs climbed steadily, flattened after the 2008 housing crash, "
                "then jumped in 2022-24 as rents and home prices rose.",
    },
    "food": {
        "id": "CPIUFDNS",       # CPI food (not seasonally adjusted)
        "label": "Food (CPI Food index)",
        "color": "#2f9e5b",
        "text": "Food prices rose slowly for most of the period, with spikes in 2008 and 2022.",
    },
    "fuel": {
        "id": "GASREGW",        # weekly regular gasoline price, $/gallon
        "label": "Fuel (regular gasoline, $/gal)",
        "color": "#e0782a",
        "text": "Fuel is the most volatile of the three, peaking in 2008, 2011-14 and 2022 "
                "and dropping sharply in 2009, 2015-16 and 2020.",
    },
}


def get_yearly_data(series_id):
    """Ask FRED for the yearly average of a series and return {year: value}."""
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": "1995-01-01",
        "frequency": "a",
        "aggregation_method": "avg",
    }
    response = requests.get(URL, params=params, timeout=20)
    if response.status_code != 200:
        raise RuntimeError(f"FRED error for {series_id}: {response.text}")

    result = {}
    for obs in response.json()["observations"]:
        if obs["value"] != ".":          # FRED uses "." for missing values
            result[int(obs["date"][:4])] = float(obs["value"])
    return result


# download everything once when the app starts
raw = {name: get_yearly_data(info["id"]) for name, info in SERIES.items()}
years = sorted(set(raw["housing"]) & set(raw["food"]) & set(raw["fuel"]))
FIRST, LAST = years[0], years[-1]
values = {name: [raw[name][y] for y in years] for name in SERIES}

PRESETS = {
    "p-all": (FIRST, LAST, "All"),
    "p-1": (FIRST, FIRST + 10, "1995-05"),
    "p-2": (2005, 2015, "2005-15"),
    "p-3": (LAST - 10, LAST, f"{LAST - 10}-{LAST % 100}"),
    "p-4": (2019, LAST, "Post-2019"),
}


def get_window(cat, start, end):
    return values[cat][start - FIRST: end - FIRST + 1]


def show(cat, x):
    if cat == "fuel":
        return f"${x:.2f}"
    return f"{x:.1f}"


def make_figure(cat, mode, kind, compare, start, end):
    as_percent = mode == "pct" or compare
    cats = list(SERIES) if compare else [cat]
    x = list(range(start, end + 1))

    fig = go.Figure()
    for c in cats:
        data = get_window(c, start, end)
        y = [(v / data[0] - 1) * 100 for v in data] if as_percent else data
        name = SERIES[c]["label"]
        color = SERIES[c]["color"]

        if as_percent:
            hover = "%{x}: %{y:+.1f}%<extra>" + name + "</extra>"
        elif c == "fuel":
            hover = "%{x}: $%{y:.2f}<extra>" + name + "</extra>"
        else:
            hover = "%{x}: %{y:.1f}<extra>" + name + "</extra>"

        if kind == "bar":
            fig.add_bar(x=x, y=y, name=name, marker_color=color, hovertemplate=hover)
        else:
            fig.add_scatter(x=x, y=y, name=name, mode="lines+markers",
                            line=dict(color=color, width=3, shape="spline"),
                            marker=dict(size=6),
                            fill=None if compare else "tozeroy",
                            hovertemplate=hover)

    # axis labels depend on what is being shown
    y_axis = dict(gridcolor="#eeeeee", zeroline=False)
    if as_percent:
        y_axis["title"] = f"% change since {start}"
        y_axis["ticksuffix"] = "%"
    elif cat == "fuel":
        y_axis["title"] = "$ per gallon"
        y_axis["tickprefix"] = "$"
    else:
        y_axis["title"] = "Index (1982-84 = 100)"

    fig.update_layout(
        template="plotly_white", height=420, margin=dict(l=10, r=10, t=10, b=10),
        hovermode="x unified", dragmode="pan", showlegend=compare,
        legend=dict(orientation="h", y=1.08), barmode="group",
        xaxis=dict(range=[start - 0.5, end + 0.5], showgrid=False,
                   dtick=1 if end - start <= 15 else None),
        yaxis=y_axis,
    )
    return fig


def make_stats(cat, start, end):
    data = get_window(cat, start, end)
    n_years = len(data) - 1
    change = (data[-1] / data[0] - 1) * 100
    per_year = ((data[-1] / data[0]) ** (1 / n_years) - 1) * 100
    peak_year = start + data.index(max(data))

    cards = [
        (f"{start} value", show(cat, data[0])),
        (f"{end} value", show(cat, data[-1])),
        ("Total change", f"{change:+.1f}%"),
        ("Avg. per year", f"{per_year:+.2f}%"),
        ("Peak year", str(peak_year)),
    ]
    return [html.Div([html.Small(title), html.B(val)], className="stat") for title, val in cards]


STYLE = """
body{margin:0;background:#f6f5f1;color:#1c1c1a;font:15px system-ui,'Segoe UI',Roboto,sans-serif;padding:20px}
.panel{max-width:980px;margin:0 auto;background:#fff;border:1px solid #e4e2da;border-radius:16px;padding:22px}
h1{font-size:22px;margin:0 0 4px}
.sub{color:#6b6a64;margin:0 0 18px;font-size:14px}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:12px}
.grow{flex:1}
.seg{display:inline-flex;border:1px solid #e4e2da;border-radius:10px;overflow:hidden}
.seg label{padding:8px 16px;cursor:pointer;margin:0}
.seg label+label{border-left:1px solid #e4e2da}
.seg input{display:none}
.seg label:has(input:checked){background:#2f6fed;color:#fff}
.seg.big label{padding:10px 20px;font-weight:600}
.btn{font:inherit;background:none;border:1px solid #e4e2da;border-radius:10px;padding:7px 12px;cursor:pointer}
.btn:hover{background:#f6f5f1}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
.stat{background:#f6f5f1;border-radius:12px;padding:10px 14px}
.stat small{color:#6b6a64;display:block;font-size:12px}
.stat b{font-size:19px}
.small{color:#6b6a64;font-size:12.5px;margin-top:14px}
"""

layout = html.Div(className="panel", children=[
    html.H1(f"US cost of living, {FIRST}-{LAST}"),
    html.P("Housing, food and fuel price changes. Scroll on the chart to zoom, drag to pan.",
           className="sub"),

    html.Div(className="row", children=[
        dcc.RadioItems(id="cat", value="housing", className="seg big", options=[
            {"label": "Housing", "value": "housing"},
            {"label": "Food", "value": "food"},
            {"label": "Fuel", "value": "fuel"},
        ]),
        html.Div(className="grow"),
        dcc.RadioItems(id="kind", value="line", className="seg", options=[
            {"label": "Line", "value": "line"},
            {"label": "Bar", "value": "bar"},
        ]),
    ]),

    html.Div(className="row", children=[
        html.Div([html.Button(p[2], id=pid, n_clicks=0, className="btn", style={"marginRight": "6px"})
                  for pid, p in PRESETS.items()]),
        dcc.RadioItems(id="mode", value="raw", className="seg", options=[
            {"label": "Actual values", "value": "raw"},
            {"label": "% change", "value": "pct"},
        ]),
        dcc.Checklist(id="compare", options=[{"label": " Compare all three", "value": "yes"}], value=[]),
    ]),

    html.Div(id="stats", className="stats"),
    dcc.Graph(id="chart", config={"scrollZoom": True, "displaylogo": False}),

    html.Div(style={"padding": "28px 10px 0"}, children=[
        dcc.RangeSlider(id="range", min=FIRST, max=LAST, step=1, value=[FIRST, LAST],
                        pushable=2, allowCross=False,
                        marks={y: str(y) for y in range(FIRST, LAST + 1, 5)},
                        tooltip={"placement": "top", "always_visible": True}),
    ]),

    html.Div(className="row", style={"marginTop": "18px"}, children=[
        html.Button("+ Zoom in", id="zoom-in", n_clicks=0, className="btn"),
        html.Button("- Zoom out", id="zoom-out", n_clicks=0, className="btn"),
        html.Button("< Pan", id="pan-left", n_clicks=0, className="btn"),
        html.Button("Pan >", id="pan-right", n_clicks=0, className="btn"),
        html.Button("Reset", id="reset", n_clicks=0, className="btn"),
        html.Div(className="grow"),
        html.Button("Export CSV", id="export", n_clicks=0, className="btn"),
        dcc.Download(id="download"),
    ]),

    html.P(id="text"),
    html.P("Data: Federal Reserve Bank of St. Louis (FRED). Yearly values are averages of the "
           "monthly/weekly data, so the most recent year may be incomplete. Series: "
           + ", ".join(s["id"] for s in SERIES.values()) + ".", className="small"),
])


@callback(
    Output("range", "value"),
    [Input(pid, "n_clicks") for pid in PRESETS],
    Input("zoom-in", "n_clicks"), Input("zoom-out", "n_clicks"),
    Input("pan-left", "n_clicks"), Input("pan-right", "n_clicks"),
    Input("reset", "n_clicks"),
    Input("range", "value"), Input("chart", "relayoutData"),
    prevent_initial_call=True,
)
def change_range(*args):
    current = args[-2]
    relayout = args[-1]
    start, end = current
    width = end - start
    trigger = ctx.triggered_id

    if trigger in PRESETS:
        start, end = PRESETS[trigger][0], PRESETS[trigger][1]
    elif trigger in ("zoom-in", "zoom-out"):
        middle = (start + end) / 2
        factor = 0.6 if trigger == "zoom-in" else 1 / 0.6
        half = width / 2 * factor
        start, end = round(middle - half), round(middle + half)
    elif trigger in ("pan-left", "pan-right"):
        step = max(1, round(width / 4))
        if trigger == "pan-left":
            step = -step
        start, end = start + step, end + step
        if start < FIRST:
            start, end = FIRST, FIRST + width
        if end > LAST:
            start, end = LAST - width, LAST
    elif trigger == "reset":
        start, end = FIRST, LAST
    elif trigger == "chart":
        # the user zoomed or panned directly on the chart
        relayout = relayout or {}
        if "xaxis.range[0]" in relayout and "xaxis.range[1]" in relayout:
            start = round(relayout["xaxis.range[0]"])
            end = round(relayout["xaxis.range[1]"])
        elif relayout.get("xaxis.autorange"):
            start, end = FIRST, LAST
        else:
            return no_update

    # keep the window inside the data and at least 3 years wide
    start = max(FIRST, start)
    end = min(LAST, end)
    if end - start < 2:
        end = min(LAST, start + 2)
        start = end - 2

    if [start, end] == list(current):
        return no_update
    return [start, end]


@callback(
    Output("chart", "figure"), Output("stats", "children"), Output("text", "children"),
    Input("range", "value"), Input("cat", "value"), Input("mode", "value"),
    Input("kind", "value"), Input("compare", "value"),
)
def update_chart(year_range, cat, mode, kind, compare):
    start, end = year_range
    fig = make_figure(cat, mode, kind, bool(compare), start, end)
    return fig, make_stats(cat, start, end), SERIES[cat]["text"]


@callback(
    Output("download", "data"),
    Input("export", "n_clicks"), Input("range", "value"),
    prevent_initial_call=True,
)
def export_csv(n_clicks, year_range):
    if ctx.triggered_id != "export":
        return no_update
    start, end = year_range
    rows = ["Year,Housing index,Food index,Fuel $/gal"]
    for year in range(start, end + 1):
        i = year - FIRST
        rows.append(f"{year},{values['housing'][i]},{values['food'][i]},{values['fuel'][i]}")
    return {"content": "\n".join(rows) + "\n", "filename": "cost-of-living.csv"}


def get_panel_4():
    return layout


if __name__ == "__main__":
    app = Dash(__name__, title="US Cost of Living")
    app.index_string = (
        "<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}"
        "<style>" + STYLE + "</style></head><body>{%app_entry%}"
        "<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>"
    )
    app.layout = get_panel_4()
    app.run(debug=True)
