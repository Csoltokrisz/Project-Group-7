#%% 
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import scipy as sc
from fredapi import Fred
import plotly.graph_objects as go
import plotly.express as px
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
print(heatdata)



'''
#Creataing correlation matrix
#corr0 = heatdata.corr(numeric_only=True)
#print(corr0)

#Slider


#Creating heatmap        addd layout thinggggg!!!
heat = go.Heatmap(z=corr0.values,
        x=corr0.columns,
        y=corr0.index,
        zmin=-1,
        zmax=1,
        zmid=0, 
        )

layout = go.Layout(xaxis_showgrid=False, yaxis_showgrid=False, yaxis_autorange="reversed")

heatmap = go.Figure(data=[heat], layout=layout)

heatmap.show()

#Can we do 2000-2025 instead of 1995?






#def panel2fig():
#  fig, ax = plt.subplots(figsize=(6, 6))
#  corr0 = heatdata.corr(numeric_only=True)
#  sns.heatmap(corr0, annot=True, fmt=".2f",
#              cmap="RdBu",
#              vmin=-1, vmax=1,
#              center=0,
#              square=True, ax=ax)
#          
#  return fig

'''

# %%
