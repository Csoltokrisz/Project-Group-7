import os

if not os.getenv("FRED_API_KEY"):
    raise SystemExit("FRED_API_KEY is not set. Set it in your terminal, then run this again.")

import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, ctx, callback

import panel_corr
import panel_cost
import panel_3
import panel_map

# each panel file is imported as a module; importing it downloads its data and registers its callbacks
macro_panel = panel_3.get_panel_3()


def thumbnail(fig, **layout):
    """Copy a panel's figure and strip it down to a small, non-interactive preview."""
    fig = go.Figure(fig)
    fig.update_layout(height=None, autosize=True, **layout)
    return fig


cost_thumb = thumbnail(
    panel_cost.make_figure("housing", "pct", "line", True, panel_cost.FIRST, panel_cost.LAST),
    margin=dict(l=45, r=10, t=35, b=25), font=dict(size=10),
    legend=dict(orientation="h", y=1.14, font=dict(size=10)),
)

macro_thumb = thumbnail(
    macro_panel.children[2].figure,
    margin=dict(l=45, r=10, t=25, b=25), font=dict(size=10),
    xaxis2=dict(rangeslider=dict(visible=False)),
)
macro_thumb.layout.updatemenus = []
macro_thumb.update_annotations(font_size=11)

corr_thumb = thumbnail(
    panel_corr.make_heatmap_figure(panel_corr.LAST, show_labels=False),
    margin=dict(l=5, r=5, t=5, b=5),
    xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False),
)
corr_thumb.update_traces(showscale=False)

map_thumb = thumbnail(
    panel_map.make_map_figure(panel_map.LAST, "pct"),
    margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False,
)

PANELS = {
    "cost": dict(title="Cost of living",
                 blurb="Housing, food and fuel prices since 1995, as % change",
                 thumb=cost_thumb, layout=panel_cost.get_panel_4),
    "macro": dict(title="Inflation and interest rates",
                  blurb="Annual inflation and the federal funds rate, with major events",
                  thumb=macro_thumb, layout=lambda: macro_panel),
    "corr": dict(title="Macroeconomic correlations",
                 blurb="How 15 economic indicators move together",
                 thumb=corr_thumb, layout=panel_corr.get_panel_corr),
    "rent": dict(title="Rental affordability",
                 blurb="Income relative to rent costs, by state",
                 thumb=map_thumb, layout=panel_map.get_panel_map),
}

STYLE = panel_cost.STYLE + """
.page-head,.grid,.page-foot{max-width:1500px;margin-left:auto;margin-right:auto}
.page-head{margin-bottom:14px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.tile{background:#fff;border:1px solid #e4e2da;border-radius:16px;padding:16px 18px;cursor:pointer;
display:flex;flex-direction:column;height:calc((100vh - 190px) / 2);min-height:300px;
transition:border-color .15s,box-shadow .15s}
.tile:hover{border-color:#2f6fed;box-shadow:0 4px 16px rgba(28,28,26,.08)}
.tile-head{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
.tile h2{font-size:16px;margin:0}
.tile p{color:#6b6a64;font-size:13px;margin:2px 0 8px}
.hint{color:#6b6a64;font-size:12px}
.tile:hover .hint{color:#2f6fed}
.thumb{flex:1;min-height:0;pointer-events:none}
.thumb-graph,.thumb-graph .js-plotly-plot,.thumb-graph .plot-container{height:100%}
.detail{display:none}
.detail-bar{display:flex;align-items:center;gap:14px;margin-bottom:14px}
.detail-bar h2{font-size:18px;margin:0}
.detail .panel{max-width:none}
.detail .stats{grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}
.detail-mode .detail{display:block;animation:fade .2s ease}
.detail-mode .home{visibility:hidden;height:0;overflow:hidden}
@keyframes fade{from{opacity:0}to{opacity:1}}
@media(max-width:900px){.grid{grid-template-columns:1fr}.tile{height:340px}}
"""

app = Dash(__name__, title="US Economic Dashboard", suppress_callback_exceptions=True)
app.index_string = (
    "<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}"
    "<style>" + STYLE + "</style></head><body>{%app_entry%}"
    "<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>"
)


def make_tile(key, spec):
    return html.Div(id=f"tile-{key}", n_clicks=0, className="tile", children=[
        html.Div(className="tile-head", children=[
            html.H2(spec["title"]),
            html.Span("Click to expand", className="hint"),
        ]),
        html.P(spec["blurb"]),
        html.Div(className="thumb", children=dcc.Graph(
            figure=spec["thumb"], className="thumb-graph", style={"height": "100%"},
            config={"staticPlot": True, "displayModeBar": False},
        )),
    ])


app.layout = html.Div(id="shell", children=[
    html.Div(className="home", children=[
        html.Div(className="page-head", children=[
            html.H1("US economic dashboard, 1995-2025"),
            html.P("Prices, rates and affordability across the US economy. "
                   "Select a panel to expand it.", className="sub"),
        ]),
        html.Div(className="grid", children=[make_tile(k, s) for k, s in PANELS.items()]),
        html.P("Data: Federal Reserve Bank of St. Louis (FRED).", className="small page-foot"),
    ]),
    html.Div(className="detail", children=[
        html.Div(className="detail-bar", children=[
            html.Button("< All panels", id="back", n_clicks=0, className="btn"),
            html.H2(id="detail-title"),
        ]),
        html.Div(id="detail-body"),
    ]),
])


@callback(
    Output("shell", "className"),
    Output("detail-body", "children"),
    Output("detail-title", "children"),
    [Input(f"tile-{k}", "n_clicks") for k in PANELS],
    Input("back", "n_clicks"),
    prevent_initial_call=True,
)
def switch_view(*clicks):
    trigger = ctx.triggered_id
    if trigger and trigger.startswith("tile-"):
        spec = PANELS[trigger[len("tile-"):]]
        return "detail-mode", spec["layout"](), spec["title"]
    return "", None, ""


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
