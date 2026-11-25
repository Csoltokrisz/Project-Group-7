import pandas as pd 
import numpy as np
import plotly.express as px
import os
import requests

states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
    "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
    "UT", "VT", "VA", "WA", "WV", "WI", "WY",]

FRED_BASE = "https://api.stlouisfed.org/fred/"
fred_api_key = os.environ.get("FRED_API_KEY")

if fred_api_key:
 print("Key found:", len(fred_api_key), "characters")
else:
 print("No key found. That's fine today:",
"we'll use the offline sample.")

# Retrieve Regional Price Parities (RPP) for Services: Rents by state
rpp_rows=[]
for state in states:
    SERIES_ID_RPP = f"{state}RPPSERVERENT"
    print("Will ask", FRED_BASE, "for series", SERIES_ID_RPP)
    params = {"series_id": SERIES_ID_RPP, "file_type": "json", "api_key": fred_api_key}
    resp = requests.get(FRED_BASE + "series/observations", params=params, timeout=60)
    if resp.ok:
       for observation in resp.json().get("observations", []):
           rpp_rows.append({
               "state": state,
               "date": observation["date"],
               "value": observation["value"]})
    print("Got", len(rpp_rows), "rows for", SERIES_ID_RPP)

# Retrieve Median Household Income by state (current dollars, annual)
mhi_rows=[]
for state in states:
    SERIES_ID_MHI = f"MEHOINUS{state}A672N"
    print("Will ask", FRED_BASE, "for series", SERIES_ID_MHI)
    params = {"series_id": SERIES_ID_MHI, "file_type": "json", "api_key": fred_api_key}
    resp = requests.get(FRED_BASE + "series/observations", params=params, timeout=60)
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

# Compute the national median across states for each year to use as a baseline
df["year_median_income"] = df.groupby("year")["median_household_income"].transform("median")

def affordability_evaluation(data: pd.DataFrame, high_threshold: float = 1.10,
                             low_threshold: float = 0.90):
    """
    Calculates a relative rental affordability ratio and categorizes states per year.

    Formula:
        affordability_ratio = (state_income / yearly_national_median_income) / (rent_rpp / 100)
        Values > 1.0 indicate higher purchasing power relative to local rent costs.
    """
    output = data.copy()

    # Normalize both metrics around 1.0 (national median income = 1.0, national avg rent RPP = 100)
    relative_income = output["median_household_income"] / output["year_median_income"]
    relative_rent = output["rent_rpp"] / 100.00

    output["affordability_ratio"] = relative_income / relative_rent
    output["affordability_pct_rank_year"] = (
        output.groupby("year")["affordability_ratio"].rank(pct=True, method="average") * 100)

    # Classify affordability relative to the high/low thresholds (defaults: >= 1.10 and <= 0.90)
    output["affordability"] = np.select(
        [
            output["affordability_ratio"] >= high_threshold,
            output["affordability_ratio"] <= low_threshold
        ],
        [
            "More Affordable",
            "Less Affordable"
        ],
        default="Moderate"
    )
    return output

df = affordability_evaluation(df)

print(
    df[
        [
            "state",
            "year",
            "rent_rpp",
            "median_household_income",
            "year_median_income",
            "affordability_ratio",
            "affordability_pct_rank_year",
            "affordability",
        ]
    ]
)

fig = px.choropleth(
    df,
    locations="state",
    locationmode="USA-states",
    scope="usa",
    color="affordability_pct_rank_year",
    range_color=[0, 100],
    color_continuous_scale="RdYlGn",
    animation_frame="year",
    hover_name="state",
    hover_data={
        "state": False,
        "year": False,
        "affordability_pct_rank_year": ":.1f",
        "affordability_ratio": ":.2f",
        "affordability": True,
        "rent_rpp": ":.1f",
        "median_household_income": ":$,.0f",
    },
    labels={
        "affordability_pct_rank_year": "Affordability Percentile (Yearly)",
        "affordability_ratio": "Affordability Ratio",
        "affordability": "Category",
        "rent_rpp": "Rent RPP",
        "median_household_income": "Median Household Income",
    },
)

fig.update_traces(
    marker_line_color="#ffffff",
    marker_line_width=0.7,
)

fig.add_annotation(
    text="Source: Federal Reserve Economic Data (FRED) — Regional Price Parities & Median Household Income",
    xref="paper",
    yref="paper",
    x=0.03,
    y=-0.22,
    showarrow=False,
    font=dict(size=10, color="#6b7280"),
)

fig.update_layout(
    margin=dict(t=85, b=115, l=15, r=15),
)

fig.update_layout(
    template="plotly_white",
    title=dict(
        text="<b>U.S. Rental Affordability Percentile From 2008-2024</b>",
        subtitle=dict(
            text="Relative to state median household income and local rent RPP",
            font=dict(size=13, family="Arial, sans-serif", color="#4b5563"),
        ),
        x=0.03,
        y=0.96,
        font=dict(size=18, family="Arial, sans-serif", color="#111827"),
    ),
    font=dict(family="Arial, sans-serif", size=12, color="#1f2937"),
    geo=dict(
        scope="usa",
        showlakes=True,
        lakecolor="#f8fafc",
        bgcolor="rgba(0,0,0,0)",
    ),
    coloraxis_colorbar=dict(
        title=dict(text="Percentile", side="right"),
        thickness=12,
        len=0.72,
        outlinewidth=0,
        ticks="outside",
    ),
    margin=dict(t=65, b=75, l=15, r=15),)

fred_api_key = os.getenv("FRED_API_KEY")
if not fred_api_key:
    raise ValueError("FRED_API_KEY environment variable is not set.")


# Fetch annual U.S. inflation rate (%) from FRED (2008–2024)
def get_fred_inflation(api_key, start_year=2008, end_year=2024):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "FPCPITOTLZGUSA",
        "api_key": api_key,
        "file_type": "json",
        "observation_start": f"{start_year}-01-01",
        "observation_end": f"{end_year}-12-31",
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    obs = resp.json()["observations"]
    
    inflation_by_year = {}
    for row in obs:
        yr = int(row["date"][:4])
        val = row["value"]
        if val != ".":
            inflation_by_year[yr] = float(val)
    return inflation_by_year

inflation_by_year = get_fred_inflation(fred_api_key)


# Format the text shown in the bottom-right box for each year
def make_inflation_text(yr):
    rate = inflation_by_year.get(yr)
    rate_str = f"{rate:.1f}%" if rate is not None else "N/A"
    return f"<b>{yr}</b><br>U.S. Inflation Rate: <b>{rate_str}</b>"

# Create the base annotation near the bottom right (near Florida)
first_year = int(sorted(df["year"].unique())[0])
inflation_box = dict(
    text=make_inflation_text(first_year),
    xref="paper",
    yref="paper",
    x=0.84,
    y=0.14,
    xanchor="center",
    yanchor="middle",
    align="left",
    showarrow=False,
    font=dict(size=12, color="#1f2937"),
    bgcolor="rgba(248, 250, 252, 0.92)",
    bordercolor="#cbd5e1",
    borderwidth=1,
    borderpad=8,
)

fig.add_annotation(inflation_box)

base_annotations = [ann.to_plotly_json() for ann in fig.layout.annotations]
box_idx = len(base_annotations) - 1

# Capture all current layout annotations and find which index is the inflation box
for frame in fig.frames:
    yr = int(frame.name)
    frame_annotations = [dict(a) for a in base_annotations]
    frame_annotations[box_idx]["text"] = make_inflation_text(yr)
    frame.update(layout=dict(annotations=frame_annotations))

# Update the box on every animation frame
for frame in fig.frames:
    yr = int(frame.name)
    frame_box = dict(inflation_box, text=make_inflation_text(yr))
    existing = list(frame.layout.annotations) if frame.layout and frame.layout.annotations else []
    frame.update(layout=dict(annotations=existing + [frame_box]))

fig.add_annotation(inflation_box)

fig.show()

                            

    








