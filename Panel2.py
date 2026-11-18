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

testinho = pd.DataFrame([unemp, dispinc, minwage, gdp, houseinc, zhvi])
testinho.fillna(0, inplace=True)

corr0 = testinho.corr(numeric_only=True)
print(corr0)


#print(testinho)
#Filter for 1995-2025


#print(testinho)

def panel2fig():
   fig, ax = plt.subplots(figsize=(6, 6))
   corr0 = testinho.corr(numeric_only=True)
   sns.heatmap(corr0, annot=True, fmt=".2f",
               cmap="RdBu",
               vmin=-1, vmax=1,
               center=0,
               square=True, ax=ax)
           
   return fig

#panel2fig()
#
#def makepanel2():
#   records = []
#   for _ in range(100):
#       annual_income = fake.random_int(min=25000, max=150000)
#       monthly_expenses = round(
#           annual_income / 12 * fake.pyfloat(min_value=0.3, max_value=0.7)
#       )
#       records.append({
#           "name": fake.name(),
#           "age": fake.random_int(min=18, max=70),
#           "annual_income": annual_income,
#           "monthly_expenses": monthly_expenses,
#       })
#
#   df = pd.DataFrame(records)
#
#   fig, ax = plt.subplots(figsize=(6, 6))
#   corr = df.corr(numeric_only=True)
#   sns.heatmap(corr, annot=True, fmt=".2f",
#               cmap="RdBu",
#               vmin=-1, vmax=1,
#               center=0,
#               square=True, ax=ax)
#       
#   plt.show()
#   return fig
#
#def hey():
#   heyo = "Heyyo"
#   return heyo
#
# %%
