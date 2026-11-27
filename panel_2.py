from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import plotly.express as px
from dash import dcc, html, Input, Output, ctx, no_update, State

from common import SEQUENTIAL, detail_graph, style_figure

states = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
    "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
    "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

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


def load_affordability_data(fred):
    def load_state(state):
        state_data = fred.annual_data([f"{state}RPPSERVERENT", f"MEHOINUS{state}A672N"]).dropna()
        state_data.columns = ["rent_rpp", "median_household_income"]
        return state_data.assign(state=state).rename_axis("year").reset_index()

    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(load_state, state) for state in states]
        try:
            merged = pd.concat([job.result() for job in jobs], ignore_index=True)
        finally:
            for job in jobs:
                job.cancel()
    merged["year_median_income"] = merged.groupby("year")["median_household_income"].transform("median")
    return affordability_evaluation(merged)


def load_data(fred):
    global df, YEARS, FIRST, LAST, inflation_by_year, PRESETS
    df = load_affordability_data(fred)
    YEARS = sorted(df["year"].unique().astype(int).tolist())
    if not YEARS:
        raise ValueError("No matching state income and rent observations.")
    FIRST, LAST = YEARS[0], YEARS[-1]
    try:
        inflation_by_year = fred.annual_series("FPCPITOTLZGUSA").dropna().to_dict()
    except RuntimeError:
        inflation_by_year = {}
    PRESETS = {
        "aff-p-first": (FIRST, str(FIRST)),
        **({"aff-p-2012": (2012, "2012")} if 2012 in YEARS else {}),
        **({"aff-p-2019": (2019, "2019")} if 2019 in YEARS else {}),
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
        color_continuous_scale=SEQUENTIAL,
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
    return style_figure(fig)


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
        ("Median of state incomes", f"${nat_med_inc:,.0f}"),
        ("Most affordable", f"{most_aff['state']} ({most_aff['affordability_ratio']:.2f}x)"),
        ("Least affordable", f"{least_aff['state']} ({least_aff['affordability_ratio']:.2f}x)"),
        ("More affordable states", f"{n_more} of {len(sub)}"),
    ]
    return [html.Div([html.Small(title), html.B(val)], className="stat") for title, val in cards]


def get_panel_2(topology_url="/assets/"):
    return html.Div(className="panel", children=[
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
        detail_graph(id="aff-map", config={"displaylogo": False, "topojsonURL": topology_url}),

        html.Div(className="slider-row", children=[
            dcc.Slider(
                id="aff-year",
                min=FIRST,
                max=LAST,
                step=None,
                value=LAST,
                marks={y: str(y) if i % 2 == 0 or y == LAST else "" for i, y in enumerate(YEARS)},
                tooltip={"placement": "top"},
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
            "Affordability Ratio = (State Median Income / Median of State Incomes) / (Rent RPP / 100). "
            "Values above 1.10 indicate stronger local purchasing power relative to rent costs.",
            id="aff-text",
        ),
        html.P(
            "Data: Federal Reserve Bank of St. Louis (FRED) — Regional Price Parities (RPPSERVERENT), "
            "Median Household Income (MEHOINUSA672N), and U.S. Inflation (FPCPITOTLZGUSA).",
            className="small",
        ),
    ])

def register_callbacks(app):
    @app.callback(
        Output("aff-year", "value"),
        [Input(pid, "n_clicks") for pid in PRESETS],
        Input("aff-prev", "n_clicks"),
        Input("aff-next", "n_clicks"),
        Input("aff-reset", "n_clicks"),
        State("aff-year", "value"),
        prevent_initial_call=True,
    )
    def change_year(*args):
        current_year = args[-1]
        trigger = ctx.triggered_id

        if trigger in PRESETS:
            yr = PRESETS[trigger][0]
        elif trigger == "aff-prev":
            yr = YEARS[max(0, YEARS.index(current_year) - 1)]
        elif trigger == "aff-next":
            yr = YEARS[min(len(YEARS) - 1, YEARS.index(current_year) + 1)]
        elif trigger == "aff-reset":
            yr = LAST
        else:
            return no_update

        if yr == current_year:
            return no_update
        return yr


    @app.callback(
        Output("aff-map", "figure"),
        Output("aff-stats", "children"),
        Input("aff-year", "value"),
        Input("aff-metric", "value"),
    )
    def update_map(yr, metric):
        return make_map_figure(yr, metric), make_map_stats(yr)


    @app.callback(
        Output("aff-download", "data"),
        Input("aff-export", "n_clicks"),
        State("aff-year", "value"),
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

def make_preview():
    fig = make_map_figure(LAST, "pct")
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False)
    return fig


if __name__ == "__main__":
    from dashboard import run_panel

    run_panel(2)
