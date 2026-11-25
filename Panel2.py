#%% 
import numpy as np
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
import os 

#Getting the data
fred = Fred(api_key=os.environ.get("FRED_API_KEY"))

series = {"Unemployment Ratio": "UNRATE",
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
        "Federal Funds Rate": "FEDFUNDS"
        }

series_data = {}
for serio, series_id in series.items():
    values = fred.get_series(series_id, observation_end="2025-12-31")
    values = pd.to_numeric(values, errors="coerce").dropna()
    annual_values = values.resample("YE").mean()
    annual_values.index = annual_values.index.year
    series_data[serio] = annual_values


#Creating dataframe from the data
heatdata = pd.DataFrame(series_data)
heatdata.index.name = "Year"
heatdata = heatdata.loc[(heatdata.index >= 2000) & (heatdata.index <= 2025)]


#Creating heatmap
#Masking redundant data
def masking(corr):
      mask = corr.values.copy()
      mask[np.tril_indices_from(mask, k=0)] = np.nan
      mask[np.abs(mask) < 0.05] = np.nan
      return mask


#Heatmap text
def heatmaptext(mask):
      return [
        [
            f"{value:.2f}" if np.isfinite(value) else ""
            for value in row
        ]
        for row in mask
    ]


#Frames
years = list(range(2000, 2026))
frames = []

for end_year in years:
        corr = heatdata.loc[heatdata.index <= end_year].corr(numeric_only=True)
        masked_values = masking(corr)
        hasheat = np.isfinite(masked_values).any()
        frames.append(go.Frame(
              name=str(end_year),
              data=[go.Heatmap(
                    z=masked_values,
                    x=corr.columns,
                    y=corr.index,
                    text=heatmaptext(masked_values),
                    texttemplate="%{text}",
                    zmin=-1,
                    zmax=1,
                    zmid=0,
                    colorscale="RdYlGn",
                    colorbar={"title": "Correlation"},
                    hovertemplate="%{y} - %{x}<br>Correlation: %{z:.3f}<extra></extra>", 
              )],
              layout={"title": f"Correlation Heatmap - {end_year}",
                      "annotations": [{
                            "text": f"No heatmap to display for {end_year}",
                            "showarrow": False,
                            "visible": not hasheat
                      }]}
        ))

#Starting heatmap
startingcorr = heatdata.corr(numeric_only=True)
maskedstart = masking(startingcorr)
heat = go.Heatmap(
        z=maskedstart,
        x=startingcorr.columns,
        y=startingcorr.index,
        text=heatmaptext(maskedstart),
        texttemplate="%{text}",
        zmin=-1,
        zmax=1,
        zmid=0, 
        colorscale="RdYlGn",
        colorbar={"title": "Correlation"},
        hovertemplate="%{y} - %{x}<br>Correlation: %{z:.3f}<extra></extra>", 
        hoverongaps=False
        )


#Layout
layout = go.Layout(title="Correlation Heatmap - 2025",
                xaxis_showgrid=False, 
                xaxis_tickangle=-45,
                xaxis_automargin=True,
                yaxis_showgrid=False, 
                yaxis_autorange="reversed",
                )


#Heatmap itself
def buildfig2():
     
      heatmap = go.Figure(data=[heat], layout=layout, frames=frames)
      
      heatmap.update_layout(
            sliders=[{
                  "active": len(years) - 1,
                  "currentvalue": {"prefix": "Correlation Through Year "},
                  "pad": {"t": 100},
                  "y": -0.35,
                  "x": 0.5,
                  "xanchor": "center",
                  "len": 500,
                  "lenmode": "pixels",
                  "steps": [{
                        "label": str(year),
                        "method": "animate",
                        "args": [[str(year)], {
                                    "mode": "immediate",
                                    "frame": {"duration": 0, "redraw": True},
                                    "transition": {"duration": 0},
                              }],
                              }
                        for year in years
                  ],
            }],
            plot_bgcolor="rgba(0,0,0,0)",
      )
      
      return heatmap

if __name__ == "__main__":
      buildfig2().show()


# %%
