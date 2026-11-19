#%% 
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
#from faker import Faker
#fake = Faker()
import seaborn as sns
import scipy as sc
from fredapi import Fred
import plotly.graph_objects as go
import plotly.express as px

#Getting the data
fred = Fred(api_key="8b4335685fcbc8639c71573ea4708762")

unemp = fred.get_series("UNRATE", observation_start="1995-01-01", observation_end="2025-12-31")
dispinc = fred.get_series("A229RX0", observation_start="1995-01-01", observation_end="2025-12-31")
minwage = fred.get_series("STTMINWGFG", observation_start="1995-01-01", observation_end="2025-12-31")
gdp = fred.get_series("A939RX0Q048SBEA", observation_start="1995-01-01", observation_end="2025-12-31")
houseinc = fred.get_series("MEHOINUSA672N", observation_start="1995-01-01", observation_end="2025-12-31")
zhvi = fred.get_series("USAUCSFRCONDOSMSAMID", observation_start="1995-01-01", observation_end="2025-12-31")

#Creating dataframe from the data
heatdata = pd.DataFrame({"Unemployment ratio": unemp, 
                         "Disposable income": dispinc, 
                         "Minimum wage": minwage, 
                         "GDP": gdp, 
                         "Household income": houseinc, 
                         "Home value index": zhvi}, 
                         )

#Creataing correlation matrix
corr0 = heatdata.corr(numeric_only=True)
print(corr0)

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



# %%
