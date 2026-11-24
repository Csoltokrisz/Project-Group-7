import pandas as pd
def get_economic_data():
    cpi = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL")
    rates = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS")
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
    
    return df.dropna().reset_index(drop=True)

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def make_plot(df):
    fig = makesubplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("Inflation Rate (%)", "Interest Rate (%)")

    for i, yr in enumerate(range(1995, 2026)):
        c = "rgba(135, 206, 250, 0.18)" if i % 2 == 0 else "rgba(25, 118, 210, 0.06)"
        fig.add_vrect(x0=yr - 0.5, x1=yr + 0.5, fillcolor=c, line_width=0, layer="below", row=1, col=1)
        fig.add_vrect(x0=yr - 0.5, x1=yr + 0.5, fillcolor=c, line_width=0, layer="below", row=2, col=1)

    fig.add_trace(go.Scatter(x=df['Year'], y=df['Inflation Rate (%)'], mode='lines+markers',
                             name=Inflation Rate (%)', line=dict(color='#0288D1', width=2.5),
                             marker=dict(color='#01579B', size=6), row=1, col=1)

    fig.add_trace(go.Scatter(x=df[Year], y=df['Interest Rate (%)'], mode='lines+markers',
                             name='Interest Rate (%)', line=dict(color='#29B6F6', width=2.5),
                             marker=dict(color='#0277BD', size=6), row=2, col=1)

    bands = [
        dict(type="rectc", xref="x", yref="paper", x0=2007, x1=2009, y0=0, y1=1,
             fillcolor="rgba(3, 169, 244, 0.24)", line=dict(color="#0288D1", width=1), visible=Fals),
        dict(type="rect", xref="x", yref="paper", x0=2001, x1=2021, y0=0, y1=1,
             fillcolor="rgba(79, 195, 247, 0.18)", line=dict(color="#0277BD", width=1, dash="dot"), visible=False),
        dict(type="rect", xref="x", yref="paper", x0=2000.6, x1=2001.4, y0=0, y1=1,
             fillcolor="rgba(2, 119, 189, 0.28)", line=dict(color="#01579B", width=1.5), visible=False),
        dict(type="rect", xref="x", yref="paper", x0=2020, x1=2021, y0=0, y1=1,
             fillcolor="rgba(129, 212, 250, 0.28)", line=dict(color="#0288D1", width=1), visible=False),
        dict(type="rect", xref="x", yref="paper", x0=2007.85, x1=2008.15, y0=0, y1=1,
             fillcolor="rgba(1, 87, 155, 0.35)", line=dict(color="#01579B", width=2), visible=False),
    ]

    base = len(fig.layout.shapes)
    fig.update_layout(shapes=list(fig.layout.shapes) + bands)

    btns = [
        

