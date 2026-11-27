import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, ctx, dcc, html, no_update

from common import DIVERGING, detail_graph, style_figure

SERIES = {
    "Unemployment Rate": "UNRATE",
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

FIRST, LAST = 1997, 2025
PRESETS = {f"corr-p-{year}": year for year in (FIRST, 2008, 2019, LAST)}


def load_data(fred):
    global heatdata
    indicators = {series_id: name for name, series_id in SERIES.items()}
    heatdata = (fred.annual_data(indicators).loc[1995:LAST]
                .rename(columns=indicators).dropna(how="all"))
    if heatdata.empty:
        raise ValueError("No observations for the correlation window.")


def compute_corr(end_year):
    return heatdata.loc[:end_year].corr(min_periods=3)


def masking(corr):
    mask = corr.to_numpy(copy=True)
    mask[np.tril_indices_from(mask)] = np.nan
    mask[np.abs(mask) < 0.05] = np.nan
    return mask


def make_heatmap_figure(end_year, show_labels=True, preview=False):
    corr = compute_corr(end_year)
    mask = masking(corr)
    text = [[f"{v:.2f}" if np.isfinite(v) else "" for v in row] for row in mask] if show_labels else None
    fig = go.Figure(go.Heatmap(
        z=mask, x=corr.columns, y=corr.index, text=text,
        texttemplate="%{text}" if show_labels else None, textfont=dict(size=10),
        zmin=-1, zmax=1, colorscale=DIVERGING, showscale=not preview,
        colorbar=dict(title="Pearson r", thickness=12, len=0.8, outlinewidth=0),
        xgap=1, ygap=1, hoverongaps=False,
        hovertemplate="%{y} / %{x}<br>Pearson r: %{z:.3f}<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(t=8, b=8, l=8, r=8),
        xaxis=dict(showgrid=False, tickangle=-40, showticklabels=not preview, side="bottom"),
        yaxis=dict(showgrid=False, autorange="reversed", showticklabels=not preview),
    )
    return style_figure(fig)


def make_corr_stats(end_year):
    corr = compute_corr(end_year)
    mask = masking(corr)
    rows, cols = np.where(np.isfinite(mask))
    pairs = [(corr.index[i], corr.columns[j], mask[i, j]) for i, j in zip(rows, cols)]
    stats = [("Window", f"1995–{end_year}"), ("Active pairs (|r| ≥ 0.05)", str(len(pairs)))]
    for title, eligible, select in (
        ("Strongest positive", [pair for pair in pairs if pair[2] > 0], max),
        ("Strongest negative", [pair for pair in pairs if pair[2] < 0], min),
    ):
        if eligible:
            a, b, val = select(eligible, key=lambda pair: pair[2])
            stats.append((f"{title} · {a} & {b}", f"{val:+.2f}"))
        else:
            stats.append((title, "N/A"))
    return [html.Div([html.Small(title), html.B(value)], className="stat") for title, value in stats]


def make_preview():
    return make_heatmap_figure(LAST, show_labels=False, preview=True)


def get_panel_4():
    return html.Div([
        html.P("Cumulative Pearson correlations across 15 U.S. indicators. Each pair needs at least three annual observations.",
               className="sub"),
        html.Div([
            dcc.RadioItems(id="corr-labels", value="show", className="seg",
                           options=[{"label": "Show values", "value": "show"},
                                    {"label": "Hide values", "value": "hide"}]),
            *[html.Button(f"1995–{year}", id=key, n_clicks=0, className="btn")
              for key, year in PRESETS.items()],
        ], className="row"),
        html.Div(id="corr-stats", className="stats"),
        detail_graph(id="corr-heatmap", tall=True,
                  config={"displaylogo": False}),
        html.Div(dcc.Slider(id="corr-year", min=FIRST, max=LAST, step=1, value=LAST,
                            marks={y: str(y) for y in range(FIRST, LAST + 1, 4)},
                            tooltip={"placement": "top"}), className="slider-row"),
        html.Div([
            html.Button("Previous year", id="corr-prev", n_clicks=0, className="btn"),
            html.Button("Next year", id="corr-next", n_clicks=0, className="btn"),
            html.Button("Reset", id="corr-reset", n_clicks=0, className="btn"),
            html.Div(className="grow"),
            html.Button("Export CSV", id="corr-export", n_clicks=0, className="btn"),
            dcc.Download(id="corr-download"),
        ], className="row"),
        html.P("Annual means from FRED. The chart hides duplicate pairs and correlations below 0.05 in absolute value. "
               "Series IDs: " + ", ".join(SERIES.values()) + ".", className="small"),
    ], className="panel")


def register_callbacks(app):
    @app.callback(Output("corr-year", "value"),
                  *[Input(key, "n_clicks") for key in PRESETS],
                  Input("corr-prev", "n_clicks"), Input("corr-next", "n_clicks"),
                  Input("corr-reset", "n_clicks"), State("corr-year", "value"),
                  prevent_initial_call=True)
    def change_year(*args):
        year = args[-1]
        target = {
            **PRESETS, "corr-prev": max(FIRST, year - 1),
            "corr-next": min(LAST, year + 1), "corr-reset": LAST,
        }.get(ctx.triggered_id, year)
        return target if target != year else no_update

    @app.callback(Output("corr-heatmap", "figure"), Output("corr-stats", "children"),
                  Input("corr-year", "value"), Input("corr-labels", "value"))
    def update_heatmap(end_year, labels):
        return make_heatmap_figure(end_year, labels == "show"), make_corr_stats(end_year)

    @app.callback(Output("corr-download", "data"), Input("corr-export", "n_clicks"),
                  State("corr-year", "value"), prevent_initial_call=True)
    def export_csv(_, end_year):
        return {"content": compute_corr(end_year).to_csv(),
                "filename": f"macro-correlations-1995-{end_year}.csv"}


if __name__ == "__main__":
    from dashboard import run_panel

    run_panel(4)
