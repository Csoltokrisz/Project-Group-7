import pandas as pd 
import numpy as np
import plotly.express as px
from fredapi import Fred
import os
import json
import requests

# use pandas df and fred to gather data
# use plotly express to create chorpleth colour code
# functions if elif to generate evaulation of each state

states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
    "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
    "UT", "VT", "VA", "WA", "WV", "WI", "WY",]

FRED_BASE = "https://api.stlouisfed.org/fred/"
fred_api_key = os.environ.get("FRED_API_KEY")
for state in states:
    SERIES_ID = f"{state}RPPSERVERENT"
    print("Will ask", FRED_BASE, "for series", SERIES_ID)
    params = {"series_id": SERIES_ID, "file_type": "json", "api_key": fred_api_key}
    resp = requests.get(FRED_BASE + "series/observations", params=params, timeout=30)
    print(resp.ok)

if fred_api_key:
 print("Key found:", len(fred_api_key), "characters")
else:
 print("No key found. That's fine today:",
"we'll use the offline sample.")







