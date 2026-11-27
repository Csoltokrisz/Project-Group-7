import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, Patch, dcc, html
from plotly.subplots import make_subplots

from common import BLUE, MUTED, ORANGE, TEAL, detail_graph, style_figure

FIRST, LAST = 1995, 2025
EVENTS = {
    "Financial crash": (2007.9, 2009.5, "#ad4d4d"),
    "Afghanistan War": (2001.8, 2021.6, "#657383"),
    "Iraq War": (2003.2, 2011.9, TEAL),
    "9/11": (2001.5, 2001.9, "#394857"),
    "COVID": (2020, 2021, ORANGE),
    "TARP (Oct 2008)": (2008.7, 2009.0, BLUE),
    "Ukraine War": (2022.15, 2025.0, "#4f6096"),
}


def load_data(fred):
    global data
    annual = fred.annual_data(["CPIAUCSL", "FEDFUNDS"]).reindex(range(FIRST - 1, LAST + 1))
    data = pd.DataFrame({
        "Inflation Rate (%)": annual["CPIAUCSL"].pct_change(fill_method=None) * 100,
        "Interest Rate (%)": annual["FEDFUNDS"],
    }).loc[FIRST:LAST].dropna().rename_axis("Year").reset_index()
    if data.empty:
        raise ValueError("No overlapping annual observations for inflation and interest rates.")


def make_plot(preview=False):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.16,
                        subplot_titles=("Inflation rate", "Federal funds rate"))
    for row, (column, color) in enumerate(
        [("Inflation Rate (%)", ORANGE), ("Interest Rate (%)", BLUE)], start=1
    ):
        fig.add_trace(go.Scatter(
            x=data["Year"], y=data[column], mode="lines+markers",
            line=dict(color=color, width=2.5), marker=dict(size=4),
            hovertemplate="%{y:.2f}%<extra></extra>", showlegend=False,
        ), row=row, col=1)
    if not preview:
        for x0, x1, color in EVENTS.values():
            fig.add_shape(type="rect", xref="x2", yref="paper", y0=0, y1=1,
                          x0=x0, x1=x1, line=dict(color=color, width=1),
                          fillcolor=color, opacity=0.19, layer="below", visible=False)
    fig.update_layout(
        margin=dict(l=46, r=14, t=26, b=26 if preview else 42),
        xaxis2=dict(range=[FIRST - 0.5, LAST + 0.5], dtick=10 if preview else 5,
                    rangeslider=dict(visible=not preview, thickness=0.07)),
        hovermode="x unified",
    )
    fig.update_yaxes(ticksuffix="%", zeroline=True)
    fig.update_annotations(font=dict(color=MUTED, size=11 if preview else 13))
    return style_figure(fig)


def make_preview():
    return make_plot(preview=True)


def get_panel_3():
    return html.Div([
        html.P("Select events to highlight them. Drag the slider handles to change the time window.", className="sub"),
        dcc.Checklist(id="macro-events", options=list(EVENTS), value=[], className="event-list"),
        html.Button("Clear events", id="macro-clear", n_clicks=0, className="btn"),
        detail_graph(id="macro-chart", figure=make_plot(),
                  config={"displaylogo": False}),
        html.P("FRED series CPIAUCSL and FEDFUNDS. Inflation is the year-over-year change in the annual average CPI.",
               className="small"),
    ], className="panel")


def register_callbacks(app):
    @app.callback(Output("macro-events", "value"), Input("macro-clear", "n_clicks"),
                  prevent_initial_call=True)
    def clear_events(_):
        return []

    @app.callback(Output("macro-chart", "figure"), Input("macro-events", "value"),
                  prevent_initial_call=True)
    def highlight_events(selected):
        update = Patch()
        for i, label in enumerate(EVENTS):
            update["layout"]["shapes"][i]["visible"] = label in selected
        return update


if __name__ == "__main__":
    from dashboard import run_panel

    run_panel(3)
