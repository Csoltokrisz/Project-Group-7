import os
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import plotly.express as px
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dash import Dash, dcc, html, Input, Output, ctx, no_update, callback

fred_api_key = os.getenv("FRED_API_KEY")
FRED_BASE = "https://api.stlouisfed.org/fred/"
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rental_affordability_cache.csv")

states = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
    "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
    "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

if not fred_api_key:
    raise ValueError("FRED_API_KEY is not set.")


def create_fred_session():
    """Create a pooled HTTP session with automatic retries for transient timeouts."""
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


session = create_fred_session()


def fetch_series(series_id, start_date=None, end_date=None):
    params = {
        "series_id": series_id,
        "file_type": "json",
        "api_key": fred_api_key,
    }
    if start_date:
        params["observation_start"] = start_date
    if end_date:
        params["observation_end"] = end_date

    resp = session.get(FRED_BASE + "series/observations", params=params, timeout=(10, 30))
    resp.raise_for_status()
    return resp.json().get("observations", [])


def affordability_evaluation(
    data: pd.DataFrame, high_threshold: float = 1.10, low_threshold: float = 0.90
):
    output = data.copy()
    relative_income = output["median_household_income"] / output["year_median_income"]
    relative_rent = output["rent_rpp"] / 100.00

    output["affordability_ratio"] = relative_income / relative_rent
    output["affordability_pct_rank_year"] = (
        output.groupby("year")["affordability_ratio"].rank(pct=True, method="average") * 100
    )
    output["affordability"] = np.select(
        [
            output["affordability_ratio"] >= high_threshold,
            output["affordability_ratio"] <= low_threshold,
        ],
        [
            "More Affordable",
            "Less Affordable",
        ],
        default="Moderate",
    )
    return output


def load_affordability_data():
    if os.path.exists(CACHE_FILE):
        print(f"Loading cached data from {CACHE_FILE}")
        return pd.read_csv(CACHE_FILE)

    print("Fetching state RPP and Median Household Income from FRED...")

    def fetch_state_pair(state):
        rpp_obs = fetch_series(f"{state}RPPSERVERENT")
        mhi_obs = fetch_series(f"MEHOINUS{state}A672N")
        rpp = [
            {"state": state, "date": o["date"], "value": o["value"]}
            for o in rpp_obs
        ]
        mhi = [
            {"state": state, "date": o["date"], "value": o["value"]}
            for o in mhi_obs
        ]
        return rpp, mhi

    rpp_rows, mhi_rows = [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for rpp, mhi in pool.map(fetch_state_pair, states):
            rpp_rows.extend(rpp)
            mhi_rows.extend(mhi)

    rpp_df = pd.DataFrame(rpp_rows)
    mhi_df = pd.DataFrame(mhi_rows)

    rpp_df["year"] = pd.to_datetime(rpp_df["date"]).dt.year
    mhi_df["year"] = pd.to_datetime(mhi_df["date"]).dt.year

    rpp_df["rent_rpp"] = pd.to_numeric(rpp_df["value"], errors="coerce")
    mhi_df["median_household_income"] = pd.to_numeric(mhi_df["value"], errors="coerce")

    merged = pd.merge(
        rpp_df[["state", "year", "rent_rpp"]].dropna(),
        mhi_df[["state", "year", "median_household_income"]].dropna(),
        on=["state", "year"],
        how="inner",
    )

    merged["year_median_income"] = merged.groupby("year")["median_household_income"].transform("median")
    merged = affordability_evaluation(merged)
    merged.to_csv(CACHE_FILE, index=False)
    print(f"Saved cache to {CACHE_FILE}")
    return merged


df = load_affordability_data()


def get_fred_inflation(start_year=2008, end_year=2024):
    obs = fetch_series(
        "FPCPITOTLZGUSA",
        start_date=f"{start_year}-01-01",
        end_date=f"{end_year}-12-31",
    )
    inflation_by_year = {}
    for row in obs:
        yr = int(row["date"][:4])
        val = row["value"]
        if val != ".":
            inflation_by_year[yr] = float(val)
    return inflation_by_year


YEARS = sorted(df["year"].unique().astype(int).tolist())
FIRST, LAST = YEARS[0], YEARS[-1]
inflation_by_year = get_fred_inflation(start_year=FIRST, end_year=LAST)

PRESETS = {
    "aff-p-first": (FIRST, str(FIRST)),
    "aff-p-2012": (2012, "2012"),
    "aff-p-2019": (2019, "Pre-COVID (2019)"),
    "aff-p-last": (LAST, f"Latest ({LAST})"),
}


def make_map_figure(yr, metric):
    sub = df[df["year"] == yr]
    is_pct = metric == "pct"

    fig = px.choropleth(
        sub,
        locations="state",
        locationmode="USA-states",
        scope="usa",
        color="affordability_pct_rank_year" if is_pct else "affordability_ratio",
        range_color=[0, 100] if is_pct else [0.70, 1.35],
        color_continuous_scale="RdYlGn",
        hover_name="state",
        hover_data={
            "state": False,
            "affordability_pct_rank_year": ":.1f",
            "affordability_ratio": ":.2f",
            "affordability": True,
            "rent_rpp": ":.1f",
            "median_household_income": ":$,.0f",
        },
        labels={
            "affordability_pct_rank_year": "Percentile",
            "affordability_ratio": "Ratio",
            "affordability": "Category",
            "rent_rpp": "Rent RPP",
            "median_household_income": "Median Income",
        },
    )

    fig.update_traces(
        marker_line_color="#ffffff",
        marker_line_width=0.8,
    )

    fig.update_layout(
        template="plotly_white",
        height=450,
        margin=dict(t=10, b=10, l=10, r=10),
        font=dict(family="system-ui, 'Segoe UI', Roboto, sans-serif", size=13, color="#1c1c1a"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        geo=dict(
            scope="usa",
            showlakes=True,
            lakecolor="#f6f5f1",
            bgcolor="rgba(0,0,0,0)",
        ),
        coloraxis_colorbar=dict(
            title=dict(text="Percentile" if is_pct else "Ratio", side="right"),
            thickness=12,
            len=0.72,
            outlinewidth=0,
            ticks="outside",
        ),
    )
    return fig


def make_map_stats(yr):
    sub = df[df["year"] == yr]
    most_aff = sub.loc[sub["affordability_ratio"].idxmax()]
    least_aff = sub.loc[sub["affordability_ratio"].idxmin()]
    nat_med_inc = sub["year_median_income"].iloc[0]
    inf_rate = inflation_by_year.get(yr)
    inf_str = f"{inf_rate:.1f}%" if inf_rate is not None else "N/A"
    n_more = int((sub["affordability"] == "More Affordable").sum())

    cards = [
        ("Selected year", str(yr)),
        ("U.S. inflation rate", inf_str),
        ("National median income", f"${nat_med_inc:,.0f}"),
        ("Most affordable", f"{most_aff['state']} ({most_aff['affordability_ratio']:.2f}x)"),
        ("Least affordable", f"{least_aff['state']} ({least_aff['affordability_ratio']:.2f}x)"),
        ("More affordable states", f"{n_more} of {len(sub)}"),
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
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px;margin:14px 0}
.stat{background:#f6f5f1;border-radius:12px;padding:10px 14px}
.stat small{color:#6b6a64;display:block;font-size:12px}
.stat b{font-size:19px}
.small{color:#6b6a64;font-size:12.5px;margin-top:14px}
"""

layout = html.Div(className="panel", children=[
    html.H1(f"U.S. rental affordability, {FIRST}-{LAST}"),
    html.P(
        "State median household income relative to local Regional Price Parity (RPP) for rents.",
        className="sub",
    ),

    html.Div(className="row", children=[
        dcc.RadioItems(
            id="aff-metric",
            value="pct",
            className="seg big",
            options=[
                {"label": "Affordability Percentile", "value": "pct"},
                {"label": "Affordability Ratio", "value": "ratio"},
            ],
        ),
        html.Div(className="grow"),
        html.Div([
            html.Button(label, id=pid, n_clicks=0, className="btn", style={"marginRight": "6px"})
            for pid, (_, label) in PRESETS.items()
        ]),
    ]),

    html.Div(id="aff-stats", className="stats"),
    dcc.Graph(id="aff-map", config={"displaylogo": False}),

    html.Div(style={"padding": "28px 10px 0"}, children=[
        dcc.Slider(
            id="aff-year",
            min=FIRST,
            max=LAST,
            step=1,
            value=LAST,
            marks={y: str(y) for y in range(FIRST, LAST + 1, 2)},
            tooltip={"placement": "top", "always_visible": True},
        ),
    ]),

    html.Div(className="row", style={"marginTop": "18px"}, children=[
        html.Button("< Prev year", id="aff-prev", n_clicks=0, className="btn"),
        html.Button("Next year >", id="aff-next", n_clicks=0, className="btn"),
        html.Button("Reset", id="aff-reset", n_clicks=0, className="btn"),
        html.Div(className="grow"),
        html.Button("Export CSV", id="aff-export", n_clicks=0, className="btn"),
        dcc.Download(id="aff-download"),
    ]),

    html.P(
        "Affordability Ratio = (State Median Income / National Median Income) / (Rent RPP / 100). "
        "Values above 1.10 indicate stronger local purchasing power relative to rent costs.",
        id="aff-text",
    ),
    html.P(
        "Data: Federal Reserve Bank of St. Louis (FRED) — Regional Price Parities (RPPSERVERENT), "
        "Median Household Income (MEHOINUSA672N), and U.S. Inflation (FPCPITOTLZGUSA).",
        className="small",
    ),
])


@callback(
    Output("aff-year", "value"),
    [Input(pid, "n_clicks") for pid in PRESETS],
    Input("aff-prev", "n_clicks"),
    Input("aff-next", "n_clicks"),
    Input("aff-reset", "n_clicks"),
    Input("aff-year", "value"),
    prevent_initial_call=True,
)
def change_year(*args):
    current_year = args[-1]
    trigger = ctx.triggered_id

    if trigger in PRESETS:
        yr = PRESETS[trigger][0]
    elif trigger == "aff-prev":
        yr = max(FIRST, current_year - 1)
    elif trigger == "aff-next":
        yr = min(LAST, current_year + 1)
    elif trigger == "aff-reset":
        yr = LAST
    else:
        return no_update

    if yr == current_year:
        return no_update
    return yr


@callback(
    Output("aff-map", "figure"),
    Output("aff-stats", "children"),
    Input("aff-year", "value"),
    Input("aff-metric", "value"),
)
def update_map(yr, metric):
    return make_map_figure(yr, metric), make_map_stats(yr)


@callback(
    Output("aff-download", "data"),
    Input("aff-export", "n_clicks"),
    Input("aff-year", "value"),
    prevent_initial_call=True,
)
def export_aff_csv(n_clicks, yr):
    if ctx.triggered_id != "aff-export":
        return no_update
    sub = df[df["year"] == yr].sort_values("affordability_pct_rank_year", ascending=False)
    return {
        "content": sub.to_csv(index=False),
        "filename": f"rental-affordability-{yr}.csv",
    }


def get_panel_map():
    return layout


if __name__ == "__main__":
    app = Dash(__name__, title="U.S. Rental Affordability")
    app.index_string = (
        "<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}"
        "<style>" + STYLE + "</style></head><body>{%app_entry%}"
        "<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>"
    )
    app.layout = get_panel_map()
    app.run(debug=True)
