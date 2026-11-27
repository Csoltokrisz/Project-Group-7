import plotly.graph_objects as go
from dash import dcc, html, Input, Output, ctx, no_update, State

from common import BLUE, TEAL, ORANGE, detail_graph, style_figure

# FRED series for each category
SERIES = {
    "housing": {
        "id": "CUUR0000SAH1",   # CPI shelter
        "label": "Housing (CPI Shelter index)",
        "color": BLUE,
        "text": "Shelter costs climbed steadily, flattened after the 2008 housing crash, "
                "then jumped in 2022-24 as rents and home prices rose.",
    },
    "food": {
        "id": "CPIUFDNS",       # CPI food (not seasonally adjusted)
        "label": "Food (CPI Food index)",
        "color": TEAL,
        "text": "Food prices rose slowly for most of the period, with spikes in 2008 and 2022.",
    },
    "fuel": {
        "id": "GASREGW",        # weekly regular gasoline price, $/gallon
        "label": "Fuel (regular gasoline, $/gal)",
        "color": ORANGE,
        "text": "Fuel is the most volatile of the three, peaking in 2008, 2011-14 and 2022 "
                "and dropping sharply in 2009, 2015-16 and 2020.",
    },
}


def load_data(fred):
    global FIRST, LAST, PRESETS, values
    annual = fred.annual_data(info["id"] for info in SERIES.values()).loc[1995:2025]
    raw = {name: annual[info["id"]].dropna().to_dict() for name, info in SERIES.items()}
    common = sorted(set.intersection(*(set(item) for item in raw.values())))
    if len(common) < 3 or common != list(range(common[0], common[-1] + 1)):
        raise ValueError("Expected at least three consecutive years across all cost series.")
    FIRST, LAST = common[0], common[-1]
    values = {name: [raw[name][year] for year in common] for name in SERIES}
    PRESETS = {
        "p-all": (FIRST, LAST, "All years"),
        "p-1": (1995, 2005, "1995–2005"),
        "p-2": (2005, 2015, "2005–2015"),
        "p-3": (LAST - 10, LAST, f"{LAST - 10}–{LAST}"),
        "p-4": (2019, LAST, "2019 onward"),
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
                            line=dict(color=color, width=3, shape="linear"),
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
        template="plotly_white", height=420, margin=dict(l=64, r=18, t=48, b=42),
        hovermode="x unified", dragmode="pan", showlegend=compare,
        legend=dict(orientation="h", y=1.02), barmode="group",
        xaxis=dict(range=[start - 0.5, end + 0.5], showgrid=False,
                   dtick=1 if end - start <= 15 else None),
        yaxis=y_axis,
    )
    return style_figure(fig)


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


def get_panel_1():
    return html.Div(className="panel", children=[
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
        detail_graph(id="chart", config={"scrollZoom": True, "displaylogo": False}),

        html.Div(className="slider-row", children=[
            dcc.RangeSlider(id="range", min=FIRST, max=LAST, step=1, value=[FIRST, LAST],
                            pushable=2, allowCross=False,
                            marks={y: str(y) for y in range(FIRST, LAST + 1, 5)},
                            tooltip={"placement": "top"}),
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

def register_callbacks(app):
    @app.callback(
        Output("range", "value"),
        [Input(pid, "n_clicks") for pid in PRESETS],
        Input("zoom-in", "n_clicks"), Input("zoom-out", "n_clicks"),
        Input("pan-left", "n_clicks"), Input("pan-right", "n_clicks"),
        Input("reset", "n_clicks"),
        Input("chart", "relayoutData"), State("range", "value"),
        prevent_initial_call=True,
    )
    def change_range(*args):
        relayout, current = args[-2:]
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
        start = min(LAST - 2, max(FIRST, start))
        end = max(FIRST + 2, min(LAST, end))
        if end - start < 2:
            end = min(LAST, start + 2)
            start = end - 2

        if [start, end] == list(current):
            return no_update
        return [start, end]


    @app.callback(
        Output("chart", "figure"), Output("stats", "children"), Output("text", "children"),
        Input("range", "value"), Input("cat", "value"), Input("mode", "value"),
        Input("kind", "value"), Input("compare", "value"),
    )
    def update_chart(year_range, cat, mode, kind, compare):
        start, end = year_range
        fig = make_figure(cat, mode, kind, bool(compare), start, end)
        return fig, make_stats(cat, start, end), SERIES[cat]["text"]


    @app.callback(
        Output("download", "data"),
        Input("export", "n_clicks"), State("range", "value"),
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

def make_preview():
    fig = make_figure("housing", "pct", "bar", True, FIRST, LAST)
    for trace, label in zip(fig.data, ("Housing", "Food", "Fuel")):
        trace.name = label
    fig.update_layout(margin=dict(l=48, r=18, t=30, b=26), yaxis_title=None, xaxis_dtick=5)
    return fig


if __name__ == "__main__":
    from dashboard import run_panel

    run_panel(1)
