#%% 
import numpy as np
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
import os 

#Getting the data
fred = Fred(api_key=os.environ.get("FRED_API_KEY"))

series = {"Unemployment ratio": "UNRATE",
        "Disposable income": "A229RX0",
        "Minimum wage": "STTMINWGFG",
        "GDP p.c.": "A939RX0Q048SBEA",
        "Household income": "MEHOINUSA672N",
        "Home value index": "USAUCSFRCONDOSMSAMID"
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
heatdata = heatdata.loc[(heatdata.index >= 1995) & (heatdata.index <= 2025)]


#Checking data ------------------------------ delete
#print(heatdata)


#Creating heatmap
#Masking redundant data
def masking(corr):
      mask = corr.values.copy()
      mask[np.tril_indices_from(mask, k=0)] = np.nan
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
years = list(range(1995, 2026))
frames = []

for end_year in years:
        corr = heatdata.loc[heatdata.index <= end_year].corr(numeric_only=True)
        masked_values = masking(corr)
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
                    colorbar={"title": "Correlation"},
                    hovertemplate="%{y} vs %{x}<br>Correlation: %{z:.3f}<extra></extra>", 
              )],
              layout={"title": f"Correlation Through Year {end_year}"}
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
        colorbar={"title": "Correlation"},
        hovertemplate="%{y} vs %{x}<br>Correlation: %{z:.3f}<extra></extra>", 
        hoverongaps=False
        )

#Layout

layout = go.Layout(title="Correlation Through Year 2025",
                xaxis_showgrid=False, 
                yaxis_showgrid=False, 
                yaxis_autorange="reversed")


#Heatmap itself

heatmap = go.Figure(data=[heat], layout=layout, frames=frames)

#Updating heatmap

heatmap.update_layout(
      sliders=[{
            "active": len(years) - 1,
            "currentvalue": {"prefix": "Correlation Through Year "},
            "pad": {"t": 100},
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

heatmap.show()

# %%
