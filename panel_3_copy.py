import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html

FONT = "system-ui, 'Segoe UI', Roboto, sans-serif"
INK = "#1c1c1a"
MUTED = "#6b6a64"
BORDER = "#e4e2da"
BG = "#f6f5f1"


def load_series(url, cache_path, col):
    try:
        df = pd.read_csv(url)
        if not df.empty and {"observation_date", col}.issubset(df.columns):
            try:
                df.to_csv(cache_path, index=False)
            except OSError:
                pass
        return df
    except Exception:
        return pd.read_csv(cache_path)


def get_economic_data():
    cpi = load_series(
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL",
        "cpi_cache.csv",
        "CPIAUCSL",
    )
    rates = load_series(
        "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS",
        "rates_cache.csv",
        "FEDFUNDS",
    )

    cpi['observation_date'] = pd.to_datetime(cpi['observation_date'], errors='coerce')
    rates['observation_date'] = pd.to_datetime(rates['observation_date'], errors='coerce')
    cpi['CPIAUCSL'] = pd.to_numeric(cpi['CPIAUCSL'], errors='coerce')
    rates['FEDFUNDS'] = pd.to_numeric(rates['FEDFUNDS'], errors='coerce')
    cpi = cpi.dropna(subset=['observation_date', 'CPIAUCSL'])
    rates = rates.dropna(subset=['observation_date', 'FEDFUNDS'])
    cpi['Year'] = cpi['observation_date'].dt.year
    cpi = cpi[(cpi['Year'] >= 1994) & (cpi['Year'] <= 2025)]
    rates['Year'] = rates['observation_date'].dt.year
    rates = rates[(rates['Year'] >= 1995) & (rates['Year'] <= 2025)]

    annual_cpi = cpi.groupby('Year')['CPIAUCSL'].mean().reset_index()
    annual_cpi['Inflation Rate (%)'] = annual_cpi['CPIAUCSL'].pct_change() * 100
    annual_cpi = annual_cpi[annual_cpi['Year'] >= 1995]
    annual_rates = rates.groupby('Year')['FEDFUNDS'].mean().reset_index()
    annual_rates.rename(columns={'FEDFUNDS': 'Interest Rate (%)'}, inplace=True)

    df = pd.merge(annual_cpi[['Year', 'Inflation Rate (%)']],
                  annual_rates[['Year', 'Interest Rate (%)']],
                  on='Year')

    out = df.dropna().reset_index(drop=True)
    out.to_csv("fred_macro_cache.csv", index=False)
    return out


def band(x0, x1, color, fill_alpha, width=1, dash="solid"):
    h = color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return dict(type="rect", xref="x", yref="paper", x0=x0, x1=x1, y0=0, y1=1,
                fillcolor=f"rgba({r}, {g}, {b}, {fill_alpha})",
                line=dict(color=color, width=width, dash=dash), visible=False)


def make_plot(df):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("Inflation rate (%)", "Interest rate (%)"))

    fig.add_trace(go.Scatter(x=df['Year'], y=df['Inflation Rate (%)'], mode='lines+markers',
                             name='Inflation Rate (%)', line=dict(color='#e0782a', width=3, shape="spline"),
                             marker=dict(size=6), showlegend=False,
                             hovertemplate="Inflation: %{y:.2f}%<extra></extra>"), row=1, col=1)

    fig.add_trace(go.Scatter(x=df['Year'], y=df['Interest Rate (%)'], mode='lines+markers',
                             name='Interest Rate (%)', line=dict(color='#2f6fed', width=3, shape="spline"),
                             marker=dict(size=6), showlegend=False,
                             hovertemplate="Interest Rate: %{y:.2f}%<extra></extra>"), row=2, col=1)

    for i, yr in enumerate(range(1995, 2026)):
        c = BG if i % 2 == 0 else "#ffffff"
        fig.add_vrect(x0=yr - 0.5, x1=yr + 0.5, fillcolor=c, line_width=0, layer="below", row=1, col=1)
        fig.add_vrect(x0=yr - 0.5, x1=yr + 0.5, fillcolor=c, line_width=0, layer="below", row=2, col=1)

    bands = [
        band(2007.9, 2009.5, "#d64545", 0.16),                    # Financial crash (Dec 2007 - Jun 2009)
        band(2001.8, 2021.6, "#6b6a64", 0.08, dash="dot"),         # Afghanistan War (Oct 2001 - Aug 2021)
        band(2003.2, 2011.9, "#2f9e5b", 0.10, dash="dash"),        # Iraq War (Mar 2003 - Dec 2011)
        band(2001.5, 2001.9, "#1c1c1a", 0.22, width=1.5),          # 9/11 (Sep 2001)
        band(2020, 2021, "#e0782a", 0.16),                         # COVID (2020)
        band(2008.7, 2009.0, "#2f6fed", 0.28, width=2),            # TARP (Oct 2008)
        band(2022.15, 2025.0, "#0e8a8a", 0.14, dash="dashdot"),    # Ukraine War (Feb 2022 - 2025)
    ]

    base = len(fig.layout.shapes)
    fig.update_layout(shapes=list(fig.layout.shapes) + bands)

    labels = ["Financial Crash", "Afghanistan War", "Iraq War", "9/11", "COVID", "TARP (Oct 2008)", "Ukraine War"]
    btns = [dict(label="Clear", method="relayout",
                 args=[{f"shapes[{base + k}].visible": False for k in range(len(bands))}])]
    for k, label in enumerate(labels):
        btns.append(dict(label=label, method="relayout", args=[{f"shapes[{base + k}].visible": True}]))
    btns.append(dict(label="All", method="relayout",
                     args=[{f"shapes[{base + k}].visible": True for k in range(len(bands))}]))

    fig.update_layout(
        template="plotly_white", height=620, margin=dict(l=70, t=40, r=10, b=115),
        font=dict(family=FONT, color=INK),
        hovermode="x unified",
        xaxis2=dict(
            range=[1995, 2025],
            dtick=2,
            rangeslider=dict(visible=True, range=[1995, 2025], thickness=0.035,
                             bgcolor=BG, bordercolor=BORDER),
        ),
        updatemenus=[dict(
            type="buttons", direction="right", x=0, y=-0.18, xanchor="left", yanchor="top",
            buttons=btns, bgcolor=BG, bordercolor=BORDER, font=dict(color=INK),
        )],
    )

    for ann in fig.layout.annotations:
        ann.update(font=dict(family=FONT, color=MUTED, size=13))

    for row in (1, 2):
        fig.update_yaxes(title_text="%", dtick=1, gridcolor="#eeeeee",
                         zeroline=True, zerolinecolor=BORDER, zerolinewidth=1, row=row, col=1)

    return fig


def get_panel_3():
    df = get_economic_data()
    fig = make_plot(df)
    return html.Div(className="panel", children=[
        html.H1("Inflation and interest rates, 1995-2025"),
        html.P("Annual inflation and federal funds rate. Use the buttons to highlight major events "
               "and the slider below the chart to zoom.", className="sub"),
        dcc.Graph(id="macro-chart", figure=fig, config={"displaylogo": False}),
        html.P("Data: Federal Reserve Bank of St. Louis (FRED), series CPIAUCSL and FEDFUNDS. "
               "Inflation is the yearly change in the annual average CPI.", className="small"),
    ])


STYLE = """
body{margin:0;background:#f6f5f1;color:#1c1c1a;font:15px system-ui,'Segoe UI',Roboto,sans-serif;padding:20px}
.panel{max-width:980px;margin:0 auto;background:#fff;border:1px solid #e4e2da;border-radius:16px;padding:22px}
h1{font-size:22px;margin:0 0 4px}
.sub{color:#6b6a64;margin:0 0 18px;font-size:14px}
.small{color:#6b6a64;font-size:12.5px;margin-top:14px}
"""

if __name__ == "__main__":
    app = Dash(__name__, title="Inflation and Interest Rates")
    app.index_string = (
        "<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}"
        "<style>" + STYLE + "</style></head><body>{%app_entry%}"
        "<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>"
    )
    app.layout = get_panel_3()
    app.run(debug=True)
