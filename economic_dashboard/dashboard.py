import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dash import Dash, Input, Output, dcc, html

from common import FredClient, read_fred_key

import panel_1
import panel_2
import panel_3
import panel_4

PANELS = (
    (1, panel_1, "Cost of living", "Annual changes in shelter, food and gasoline prices."),
    (2, panel_2, "Rental affordability", "Household income relative to local rents, by state."),
    (3, panel_3, "Inflation and interest rates", "Annual CPI inflation and the federal funds rate."),
    (4, panel_4, "Macroeconomic correlations", "How 15 U.S. economic indicators move together."),
)


def prepare_panel(spec, topology_url, fred):
    number, module, title, description = spec
    try:
        module.load_data(fred)
        layout = getattr(module, f"get_panel_{number}")
        body = layout(topology_url) if number == 2 else layout()
        preview = module.make_preview()
        print(f"Panel {number} loaded: {title}", flush=True)
        return preview, body, True
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        logging.warning("Panel %s (%s): %s", number, title, error)
        explanation = html.P(str(error), className="panel-error")
        return None, explanation, False


def make_tile(number, title, description, preview, topology_url):
    chart = dcc.Graph(
        figure=preview, responsive=True, className="preview-graph",
        config={"staticPlot": True, "displayModeBar": False, "topojsonURL": topology_url},
    ) if preview is not None else html.P("Data unavailable", className="panel-error")
    return html.Article([
        html.H2(html.Button([
            html.Span(f"Panel {number}", className="panel-number"),
            html.Span(title, className="tile-title"),
            html.Span("↗", className="tile-arrow", **{"aria-hidden": "true"}),
        ], id=f"open-{number}", className="tile-button", n_clicks=0)),
        html.P(description, className="tile-description"),
        html.Div(chart, className="preview", **{"aria-hidden": "true"}),
    ], className="tile")


def make_detail(number, title, body, standalone=False):
    return html.Section([
        html.Header([
            None if standalone else html.Button("← All panels", id=f"back-{number}",
                                                n_clicks=0, className="btn back"),
            html.P(f"Panel {number}", className="panel-number"),
            html.H1(title),
        ], className="detail-header"),
        body,
    ], id=f"detail-{number}", className="detail", hidden=not standalone)


def create_app(only_panel=None, *, fred=None):
    if fred is None:
        fred = FredClient(read_fred_key())
        print("Loading data from FRED. The complete dashboard usually takes 1–2 minutes to start.", flush=True)
    app = Dash(__name__, title="U.S. Economic Dashboard",
               assets_folder=str(Path(__file__).resolve().parent / "assets"))
    specs = [spec for spec in PANELS if only_panel is None or spec[0] == only_panel]
    topology_url = app.get_asset_url("usa_110m.json").removesuffix("usa_110m.json")
    with ThreadPoolExecutor(max_workers=len(specs)) as pool:
        jobs = [pool.submit(prepare_panel, spec, topology_url, fred) for spec in specs]
        results = [job.result() for job in jobs]
    tiles, details = [], []
    for (number, module, title, description), (preview, body, ready) in zip(specs, results):
        if ready:
            module.register_callbacks(app)
        tiles.append(make_tile(number, title, description, preview, topology_url))
        details.append(make_detail(number, title, body, standalone=only_panel is not None))

    if only_panel is not None:
        app.layout = html.Main(details, className="shell")
        return app

    app.layout = html.Main([
        html.Div([
            html.Header([
                html.H1("U.S. Economic Dashboard"),
                html.P("Explore prices, rates and affordability. Select a panel to expand it.", className="sub"),
            ], className="page-header"),
            html.Div(tiles, className="grid"),
            html.Footer("Source: Federal Reserve Bank of St. Louis (FRED API).", className="small"),
        ], id="overview"),
        *details,
    ], className="shell")

    # Keep all graphs mounted so a trip to the overview preserves control and zoom state.
    numbers = [spec[0] for spec in specs]
    app.clientside_callback(
        """
        function () {
            const id = dash_clientside.callback_context.triggered_id
                || dash_clientside.callback_context.triggered[0].prop_id.split(".")[0];
            const [action, number] = id.split("-");
            const opening = action === "open";
            requestAnimationFrame(() => requestAnimationFrame(() => {
                window.scrollTo(0, 0);
                document.getElementById((opening ? "back-" : "open-") + number).focus();
                window.dispatchEvent(new Event("resize"));
            }));
            return [opening, ...[1, 2, 3, 4].map(i => !opening || i !== Number(number))];
        }
        """,
        Output("overview", "hidden"),
        *[Output(f"detail-{number}", "hidden") for number in numbers],
        *[Input(f"{action}-{number}", "n_clicks") for action in ("open", "back") for number in numbers],
        prevent_initial_call=True,
    )
    return app


def run_panel(number):
    create_app(only_panel=number).run()


if __name__ == "__main__":
    create_app().run()
