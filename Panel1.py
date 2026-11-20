import pandas as pd 
import numpy as np
import plotly.express as px
from fredapi import Fred
import os
import json
import requests

# use pandas df and fred to gather data
# use plotly express to create chorpleth colour code
# functions if elif to generate affordability evaulation of each state with respect to median household income 

states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
    "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
    "UT", "VT", "VA", "WA", "WV", "WI", "WY",]

FRED_BASE = "https://api.stlouisfed.org/fred/"
fred_api_key = os.environ.get("FRED_API_KEY")

rpp_rows=[]
for state in states:
    SERIES_ID_RPP = f"{state}RPPSERVERENT"
    print("Will ask", FRED_BASE, "for series", SERIES_ID_RPP)
    params = {"series_id": SERIES_ID_RPP, "file_type": "json", "api_key": fred_api_key}
    resp = requests.get(FRED_BASE + "series/observations", params=params, timeout=30)
    if resp.ok:
       for observation in resp.json().get("observations", []):
           rpp_rows.append({
               "state": state,
               "date": observation["date"],
               "value": observation["value"]})
    print("Got", len(rpp_rows), "rows for", SERIES_ID_RPP)

mhi_rows=[]
for state in states:
    SERIES_ID_MHI = f"MEHOINUS{state}A672N"
    print("Will ask", FRED_BASE, "for series", SERIES_ID_MHI)
    params = {"series_id": SERIES_ID_MHI, "file_type": "json", "api_key": fred_api_key}
    resp = requests.get(FRED_BASE + "series/observations", params=params, timeout=30)
    if resp.ok:
        for observation in resp.json().get("observations", []):
            mhi_rows.append({
                "state": state,
                "date": observation["date"],
                "value": observation["value"]})
        print("Got", len(mhi_rows), "rows for", SERIES_ID_MHI)

rpp_df = pd.DataFrame(rpp_rows)
mhi_df = pd.DataFrame(mhi_rows)

rpp_df["year"] = pd.to_datetime(rpp_df["date"]).dt.year
mhi_df["year"] = pd.to_datetime(mhi_df["date"]).dt.year

rpp_df["rent_rpp"] = pd.to_numeric(rpp_df["value"], errors="coerce")
mhi_df["median_household_income"] = pd.to_numeric(mhi_df["value"], errors="coerce")

df = pd.merge(rpp_df[["state", "year", "rent_rpp"]].dropna(),
               mhi_df[["state", "year", "median_household_income"]].dropna()
              ,on=["state", "year"], how="inner")

year_median_income = df.groupby("year")["median_household_income"].transform("median")

def affordability_evaluation(rent_rpp, median_household_income, year_median_income):
    relative_income = median_household_income / year_median_income
    relative_rent = rent_rpp / 100.00
    ratio = relative_income / relative_rent

    if ratio >= x
      return "Less affordable"
    elif ratio <= y
      return "More affordable"
    else:
      return "Moderate"

    

if fred_api_key:
 print("Key found:", len(fred_api_key), "characters")
else:
 print("No key found. That's fine today:",
"we'll use the offline sample.")







