import pandas as pd

def load_series(url,cache_path, col):
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
    
    cpi['observation_date'] = pd.to_datetime(cpi['observation_date'],errors='coerce')
    rates['observation_date'] = pd.to_datetime(rates['observation_date'],errors='coerce')
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

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def make_plot(df):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("<b>Inflation Rate (%)</b>", "<b>Interest Rate (%)</b>"))

    for i, yr in enumerate(range(1995, 2026)):
        c = "rgba(180, 155, 130, 0.10)" if i % 2 == 0 else "rgba(180, 155, 130, 0.03)"
        fig.add_vrect(x0=yr - 0.5, x1=yr + 0.5, fillcolor=c, line_width=0, layer="below", row=1, col=1)
        fig.add_vrect(x0=yr - 0.5, x1=yr + 0.5, fillcolor=c, line_width=0, layer="below", row=2, col=1)

    fig.add_trace(go.Scatter(x=df['Year'], y=df['Inflation Rate (%)'], mode='lines+markers',
                             name='Inflation Rate (%)', line=dict(color='#9E2A2B', width=2.5),
                             marker=dict(color='#6B1819', size=6)), row=1, col=1)

    fig.add_trace(go.Scatter(x=df['Year'], y=df['Interest Rate (%)'], mode='lines+markers',
                             name='Interest Rate (%)', line=dict(color='#1D4E89', width=2.5),
                             marker=dict(color='#102A43', size=6)), row=2, col=1)

    bands = [
        # 0: Financial Crash (Great Recession: Dec 2007 – Jun 2009)
        dict(type="rect", xref="x", yref="paper", x0=2007.9, x1=2009.5, y0=0, y1=1,
             fillcolor="rgba(158, 42, 43, 0.16)", line=dict(color="#9E2A2B", width=1), visible=False),
        # 1: Afghanistan War (Oct 2001 – Aug 2021)
        dict(type="rect", xref="x", yref="paper", x0=2001.8, x1=2021.6, y0=0, y1=1,
             fillcolor="rgba(29, 78, 137, 0.08)", line=dict(color="#1D4E89", width=1, dash="dot"), visible=False),
        # 2: Iraq War (Mar 2003 – Dec 2011)
        dict(type="rect", xref="x", yref="paper", x0=2003.2, x1=2011.9, y0=0, y1=1,
             fillcolor="rgba(44, 110, 73, 0.10)", line=dict(color="#2C6E49", width=1, dash="dash"), visible=False),
        # 3: 9/11 (Sep 2001)
        dict(type="rect", xref="x", yref="paper", x0=2001.5, x1=2001.9, y0=0, y1=1,
             fillcolor="rgba(107, 24, 25, 0.22)", line=dict(color="#6B1819", width=1.5), visible=False),
        # 4: COVID (2020)
        dict(type="rect", xref="x", yref="paper", x0=2020, x1=2021, y0=0, y1=1,
             fillcolor="rgba(217, 119, 6, 0.16)", line=dict(color="#B45309", width=1), visible=False),
        # 5: Emergency Economic Stabilization Act / TARP (Oct 2008)
        dict(type="rect", xref="x", yref="paper", x0=2008.7, x1=2009.0, y0=0, y1=1,
             fillcolor="rgba(16, 42, 67, 0.28)", line=dict(color="#102A43", width=2), visible=False),
    ]

    base = len(fig.layout.shapes)
    fig.update_layout(shapes=list(fig.layout.shapes) + bands)

    btns = [
        dict(label="Clear", method="relayout", args=[{f"shapes[{base + k}].visible": False for k in range(len(bands))}]),
        dict(label="Financial Crash", method="relayout", args=[{f"shapes[{base + 0}].visible": True}]),
        dict(label="Afghanistan War", method="relayout", args=[{f"shapes[{base + 1}].visible": True}]),
        dict(label="Iraq War", method="relayout", args=[{f"shapes[{base + 2}].visible": True}]),
        dict(label="9/11", method="relayout", args=[{f"shapes[{base + 3}].visible": True}]),
        dict(label="COVID", method="relayout", args=[{f"shapes[{base + 4}].visible": True}]),
        dict(label="TARP (Oct 2008)", method="relayout", args=[{f"shapes[{base + 5}].visible": True}]),
        dict(label="All", method="relayout", args=[{f"shapes[{base + k}].visible": True for k in range(len(bands))}]),
    ]
    fig.update_layout(
        title="<b>Inflation and Interest Rates (1995-2025)</b>",
        plot_bgcolor="#FAF0E6",
        paper_bgcolor="#FFF8F0",
        font=dict(color="#1F2933"),
        hovermode="x unified",
        xaxis2=dict(range=[1995, 2025], dtick=2, rangeslider=dict(visible=True, range=[1995, 2025], bgcolor="#FAF0E6")),
        updatemenus=[dict(type="buttons", direction="right", x=0, y=1.15, xanchor="left", buttons=btns,
                          bgcolor="#F2E5D7", bordercolor="#8C7A6B", font=dict(color="#1F2933"))],
    )

    fig.update_yaxes(title_text="%", row=1, col=1, gridcolor="#E2D6C8")
    fig.update_yaxes(title_text="%", row=2, col=1, gridcolor="#E2D6C8")
    fig.update_xaxes(gridcolor="#E2D6C8")

    return fig


df = get_economic_data()
fig = make_plot(df)
fig.show()


    
   
        

