import os
import numpy as np
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, ctx, no_update, callback

API_KEY = os.environ.get("FRED_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing FRED_API_KEY environment variable.")
fred_client = Fred(api_key=API_KEY)

series = {
    "Unemployment Ratio": "UNRATE",
    "Disposable Income": "A229RX0",
    "Personal Saving Rate": "PSAVERT",
    "Minimum Wage": "STTMINWGFG",
    "GDP per Capita": "A939RX0Q048SBEA",
    "Household Income": "MEHOINUSA672N",
    "Home Value Index": "USAUCSFRCONDOSMSAMID",
    "30-Year Mortgage Rate": "MORTGAGE30US",
    "GINI Index": "SIPOVGINIUSA",
    "Consumer Price Index (CPI)": "CPIAUCSL",
    "Core CPI": "CPILFESL",
    "Food CPI": "CPIUFDSL",
    "Energy CPI": "CPIENGSL",
    "Household Debt Service Ratio": "TDSP",
    "Federal Funds Rate": "FEDFUNDS",
}

# yearly average of every series
series_data = {}
for name, series_id in series.items():
    values = fred_client.get_series(series_id, observation_end="2025-12-31")
    values = pd.to_numeric(values, errors="coerce").dropna()
    series_data[name] = values.groupby(values.index.year).mean()

heatdata = pd.DataFrame(series_data)
heatdata.index.name = "Year"
heatdata = heatdata.loc[(heatdata.index >= 1995) & (heatdata.index <= 2025)]

YEARS = list(range(1997, 2026))
FIRST, LAST = YEARS[0], YEARS[-1]

PRESETS = {
    "corr-p-first": (FIRST, f"1995–{FIRST}"),
    "corr-p-2008": (2008, "1995–2008"),
    "corr-p-2019": (2019, "1995–2019"),
    "corr-p-last": (LAST, f"1995–{LAST}"),
}


def masking(corr):
    # hide the lower triangle (repeats) and very weak correlations
    mask = corr.values.copy()
    mask[np.tril_indices_from(mask, k=0)] = np.nan
    mask[np.abs(mask) < 0.05] = np.nan
    return mask


def heatmaptext(mask):
    return [
        [f"{value:.2f}" if np.isfinite(value) else "" for value in row]
        for row in mask
    ]


def compute_corr(end_year):
    sub_df = heatdata.loc[heatdata.index <= end_year]
    corr = sub_df.corr(numeric_only=True, min_periods=3)
    return corr.reindex(index=heatdata.columns, columns=heatdata.columns)


def make_heatmap_figure(end_year, show_labels=True):
    corr = compute_corr(end_year)
    masked_values = masking(corr)

    trace = go.Heatmap(
        z=masked_values,
        x=corr.columns,
        y=corr.index,
        text=heatmaptext(masked_values) if show_labels else None,
        texttemplate="%{text}" if show_labels else None,
        textfont=dict(size=10),
        zmin=-1,
        zmax=1,
        zmid=0,
        colorscale="RdYlGn",
        colorbar=dict(
            title=dict(text="Correlation", side="right"),
            thickness=12,
            len=0.78,
            outlinewidth=0,
            ticks="outside",
        ),
        hovertemplate="%{y} - %{x}<br>Correlation: %{z:.3f}<extra></extra>",
        hoverongaps=False,
    )

    fig = go.Figure(data=[trace])
    fig.update_layout(
        template="plotly_white",
        height=640,
        margin=dict(t=10, b=10, l=10, r=10),
        font=dict(family="system-ui, 'Segoe UI', Roboto, sans-serif", size=12, color="#1c1c1a"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickangle=-35),
        yaxis=dict(showgrid=False, autorange="reversed"),
    )
    return fig


def make_corr_stats(end_year):
    corr = compute_corr(end_year)
    masked = masking(corr)
    cols = list(corr.columns)

    pairs = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = masked[i, j]
            if np.isfinite(val):
                pairs.append((cols[i], cols[j], float(val)))

    if pairs:
        strongest_pos = max(pairs, key=lambda x: x[2])
        strongest_neg = min(pairs, key=lambda x: x[2])
        pos_label = f"{strongest_pos[2]:+.2f}"
        pos_sub = f"{strongest_pos[0]} & {strongest_pos[1]}"
        neg_label = f"{strongest_neg[2]:+.2f}"
        neg_sub = f"{strongest_neg[0]} & {strongest_neg[1]}"
    else:
        pos_label, pos_sub = "N/A", "No valid pairs"
        neg_label, neg_sub = "N/A", "No valid pairs"

    n_years = int((heatdata.index <= end_year).sum())
    cards = [
        ("Window", f"1995–{end_year} ({n_years} yrs)"),
        ("Active pairs (|r| >= 0.05)", str(len(pairs))),
        (f"Strongest positive ({pos_sub})", pos_label),
        (f"Strongest negative ({neg_sub})", neg_label),
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
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:14px 0}
.stat{background:#f6f5f1;border-radius:12px;padding:10px 14px}
.stat small{color:#6b6a64;display:block;font-size:12px}
.stat b{font-size:19px}
.small{color:#6b6a64;font-size:12.5px;margin-top:14px}
"""

layout = html.Div(className="panel", children=[
    html.H1(f"Macroeconomic correlation matrix, 1995–{LAST}"),
    html.P(
        "Cumulative pairwise Pearson correlations across 15 U.S. economic indicators. "
        "Weak correlations (|r| < 0.05) and redundant lower-triangle cells are masked.",
        className="sub",
    ),

    html.Div(className="row", children=[
        dcc.RadioItems(
            id="corr-labels",
            value="show",
            className="seg big",
            options=[
                {"label": "Show values", "value": "show"},
                {"label": "Hide values", "value": "hide"},
            ],
        ),
        html.Div(className="grow"),
        html.Div([
            html.Button(label, id=pid, n_clicks=0, className="btn", style={"marginRight": "6px"})
            for pid, (_, label) in PRESETS.items()
        ]),
    ]),

    html.Div(id="corr-stats", className="stats"),
    dcc.Graph(id="corr-heatmap", config={"displaylogo": False}),

    html.Div(style={"padding": "28px 10px 0"}, children=[
        dcc.Slider(
            id="corr-year",
            min=FIRST,
            max=LAST,
            step=1,
            value=LAST,
            marks={y: str(y) for y in range(FIRST, LAST + 1, 4)},
            tooltip={"placement": "top", "always_visible": True},
        ),
    ]),

    html.Div(className="row", style={"marginTop": "18px"}, children=[
        html.Button("< Prev year", id="corr-prev", n_clicks=0, className="btn"),
        html.Button("Next year >", id="corr-next", n_clicks=0, className="btn"),
        html.Button("Reset", id="corr-reset", n_clicks=0, className="btn"),
        html.Div(className="grow"),
        html.Button("Export CSV", id="corr-export", n_clicks=0, className="btn"),
        dcc.Download(id="corr-download"),
    ]),

    html.P(
        "Each step computes cumulative correlations from 1995 through the selected end year "
        "(minimum 3 annual observations per pair).",
        id="corr-text",
    ),
    html.P(
        "Data: Federal Reserve Bank of St. Louis (FRED). Annual values are arithmetic means "
        "of the underlying series. Series: " + ", ".join(series.values()) + ".",
        className="small",
    ),
])


@callback(
    Output("corr-year", "value"),
    [Input(pid, "n_clicks") for pid in PRESETS],
    Input("corr-prev", "n_clicks"),
    Input("corr-next", "n_clicks"),
    Input("corr-reset", "n_clicks"),
    Input("corr-year", "value"),
    prevent_initial_call=True,
)
def change_corr_year(*args):
    current_year = args[-1]
    trigger = ctx.triggered_id

    if trigger in PRESETS:
        yr = PRESETS[trigger][0]
    elif trigger == "corr-prev":
        yr = max(FIRST, current_year - 1)
    elif trigger == "corr-next":
        yr = min(LAST, current_year + 1)
    elif trigger == "corr-reset":
        yr = LAST
    else:
        return no_update

    if yr == current_year:
        return no_update
    return yr


@callback(
    Output("corr-heatmap", "figure"),
    Output("corr-stats", "children"),
    Input("corr-year", "value"),
    Input("corr-labels", "value"),
)
def update_heatmap(end_year, labels_mode):
    return make_heatmap_figure(end_year, labels_mode == "show"), make_corr_stats(end_year)


@callback(
    Output("corr-download", "data"),
    Input("corr-export", "n_clicks"),
    Input("corr-year", "value"),
    prevent_initial_call=True,
)
def export_corr_csv(n_clicks, end_year):
    if ctx.triggered_id != "corr-export":
        return no_update
    corr = compute_corr(end_year)
    return {
        "content": corr.to_csv(),
        "filename": f"macro-correlations-1995-{end_year}.csv",
    }


def get_panel_corr():
    return layout


if __name__ == "__main__":
    app = Dash(__name__, title="Macroeconomic Correlation Matrix")
    app.index_string = (
        "<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}"
        "<style>" + STYLE + "</style></head><body>{%app_entry%}"
        "<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>"
    )
    app.layout = get_panel_corr()
    app.run(debug=True)
