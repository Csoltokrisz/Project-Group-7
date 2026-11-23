import os

import pandas as pd
import plotly.graph_objects as go
import requests


STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
    "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
    "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

FRED_BASE = "https://api.stlouisfed.org/fred/"

# State-level presidential vote winners. Maine and Nebraska use the state winner,
# rather than the outcome in an individual congressional district.
ELECTION_WINNERS = {
    2008: {
        "AL": "Republican", "AK": "Republican", "AZ": "Republican", "AR": "Republican",
        "CA": "Democratic", "CO": "Democratic", "CT": "Democratic", "DE": "Democratic",
        "DC": "Democratic", "FL": "Democratic", "GA": "Republican", "HI": "Democratic",
        "ID": "Republican", "IL": "Democratic", "IN": "Democratic", "IA": "Democratic",
        "KS": "Republican", "KY": "Republican", "LA": "Republican", "ME": "Democratic",
        "MD": "Democratic", "MA": "Democratic", "MI": "Democratic", "MN": "Democratic",
        "MS": "Republican", "MO": "Republican", "MT": "Republican", "NE": "Republican",
        "NV": "Democratic", "NH": "Democratic", "NJ": "Democratic", "NM": "Democratic",
        "NY": "Democratic", "NC": "Republican", "ND": "Republican", "OH": "Democratic",
        "OK": "Republican", "OR": "Democratic", "PA": "Democratic", "RI": "Democratic",
        "SC": "Republican", "SD": "Republican", "TN": "Republican", "TX": "Republican",
        "UT": "Republican", "VT": "Democratic", "VA": "Democratic", "WA": "Democratic",
        "WV": "Republican", "WI": "Democratic", "WY": "Republican",
    },
    2012: {
        "AL": "Republican", "AK": "Republican", "AZ": "Republican", "AR": "Republican",
        "CA": "Democratic", "CO": "Democratic", "CT": "Democratic", "DE": "Democratic",
        "DC": "Democratic", "FL": "Democratic", "GA": "Republican", "HI": "Democratic",
        "ID": "Republican", "IL": "Democratic", "IN": "Republican", "IA": "Democratic",
        "KS": "Republican", "KY": "Republican", "LA": "Republican", "ME": "Democratic",
        "MD": "Democratic", "MA": "Democratic", "MI": "Democratic", "MN": "Democratic",
        "MS": "Republican", "MO": "Republican", "MT": "Republican", "NE": "Republican",
        "NV": "Democratic", "NH": "Democratic", "NJ": "Democratic", "NM": "Democratic",
        "NY": "Democratic", "NC": "Republican", "ND": "Republican", "OH": "Democratic",
        "OK": "Republican", "OR": "Democratic", "PA": "Democratic", "RI": "Democratic",
        "SC": "Republican", "SD": "Republican", "TN": "Republican", "TX": "Republican",
        "UT": "Republican", "VT": "Democratic", "VA": "Democratic", "WA": "Democratic",
        "WV": "Republican", "WI": "Democratic", "WY": "Republican",
    },
    2016: {
        "AL": "Republican", "AK": "Republican", "AZ": "Republican", "AR": "Republican",
        "CA": "Democratic", "CO": "Democratic", "CT": "Democratic", "DE": "Democratic",
        "DC": "Democratic", "FL": "Republican", "GA": "Republican", "HI": "Democratic",
        "ID": "Republican", "IL": "Democratic", "IN": "Republican", "IA": "Republican",
        "KS": "Republican", "KY": "Republican", "LA": "Republican", "ME": "Democratic",
        "MD": "Democratic", "MA": "Democratic", "MI": "Republican", "MN": "Democratic",
        "MS": "Republican", "MO": "Republican", "MT": "Republican", "NE": "Republican",
        "NV": "Democratic", "NH": "Democratic", "NJ": "Democratic", "NM": "Democratic",
        "NY": "Democratic", "NC": "Republican", "ND": "Republican", "OH": "Republican",
        "OK": "Republican", "OR": "Democratic", "PA": "Republican", "RI": "Democratic",
        "SC": "Republican", "SD": "Republican", "TN": "Republican", "TX": "Republican",
        "UT": "Republican", "VT": "Democratic", "VA": "Democratic", "WA": "Democratic",
        "WV": "Republican", "WI": "Republican", "WY": "Republican",
    },
    2020: {
        "AL": "Republican", "AK": "Republican", "AZ": "Democratic", "AR": "Republican",
        "CA": "Democratic", "CO": "Democratic", "CT": "Democratic", "DE": "Democratic",
        "DC": "Democratic", "FL": "Republican", "GA": "Democratic", "HI": "Democratic",
        "ID": "Republican", "IL": "Democratic", "IN": "Republican", "IA": "Republican",
        "KS": "Republican", "KY": "Republican", "LA": "Republican", "ME": "Democratic",
        "MD": "Democratic", "MA": "Democratic", "MI": "Democratic", "MN": "Democratic",
        "MS": "Republican", "MO": "Republican", "MT": "Republican", "NE": "Republican",
        "NV": "Democratic", "NH": "Democratic", "NJ": "Democratic", "NM": "Democratic",
        "NY": "Democratic", "NC": "Republican", "ND": "Republican", "OH": "Republican",
        "OK": "Republican", "OR": "Democratic", "PA": "Democratic", "RI": "Democratic",
        "SC": "Republican", "SD": "Republican", "TN": "Republican", "TX": "Republican",
        "UT": "Republican", "VT": "Democratic", "VA": "Democratic", "WA": "Democratic",
        "WV": "Republican", "WI": "Democratic", "WY": "Republican",
    },
    2024: {
        "AL": "Republican", "AK": "Republican", "AZ": "Republican", "AR": "Republican",
        "CA": "Democratic", "CO": "Democratic", "CT": "Democratic", "DE": "Democratic",
        "DC": "Democratic", "FL": "Republican", "GA": "Republican", "HI": "Democratic",
        "ID": "Republican", "IL": "Democratic", "IN": "Republican", "IA": "Republican",
        "KS": "Republican", "KY": "Republican", "LA": "Republican", "ME": "Democratic",
        "MD": "Democratic", "MA": "Democratic", "MI": "Republican", "MN": "Democratic",
        "MS": "Republican", "MO": "Republican", "MT": "Republican", "NE": "Republican",
        "NV": "Republican", "NH": "Democratic", "NJ": "Democratic", "NM": "Democratic",
        "NY": "Democratic", "NC": "Republican", "ND": "Republican", "OH": "Republican",
        "OK": "Republican", "OR": "Democratic", "PA": "Republican", "RI": "Democratic",
        "SC": "Republican", "SD": "Republican", "TN": "Republican", "TX": "Republican",
        "UT": "Republican", "VT": "Democratic", "VA": "Democratic", "WA": "Democratic",
        "WV": "Republican", "WI": "Republican", "WY": "Republican",
    },
}


def get_presidential_winner(state, year):
    election_year = max(
        election_year
        for election_year in ELECTION_WINNERS
        if election_year <= year
    )
    return ELECTION_WINNERS[election_year][state]


def load_rpp_data(api_key=None):
    rows = []
    for state in STATES:
        series_id = f"{state}RPPSERVERENT"
        response = requests.get(
            FRED_BASE + "series/observations",
            params={
                "series_id": series_id,
                "file_type": "json",
                "api_key": api_key,
            },
            timeout=30,
        )
        if not response.ok:
            continue

        for observation in response.json().get("observations", []):
            rows.append({
                "state": state,
                "date": observation["date"],
                "rent_rpp": pd.to_numeric(observation["value"], errors="coerce"),
            })

    return pd.DataFrame(rows)


def panel4fig():
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        fig = go.Figure()
        fig.add_annotation(
            text="Set FRED_API_KEY to load RPP data.",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        fig.update_layout(
            title="RPP Change by Presidential Election Winner",
            xaxis={"visible": False},
            yaxis={"visible": False},
        )
        return fig

    rpp_df = load_rpp_data(api_key)
    if rpp_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No RPP observations were returned by FRED.",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        fig.update_layout(title="RPP Change by Presidential Election Winner")
        return fig

    rpp_df["year"] = pd.to_datetime(rpp_df["date"]).dt.year
    rpp_df = rpp_df.dropna(subset=["rent_rpp"])
    rpp_df = rpp_df.sort_values(["state", "year"])
    rpp_df["rpp_change_percent"] = rpp_df.groupby("state")["rent_rpp"].pct_change() * 100
    rpp_df = rpp_df.dropna(subset=["rpp_change_percent"])
    rpp_df = rpp_df[rpp_df["year"] >= 2008]
    rpp_df["presidential_winner"] = rpp_df.apply(
        lambda row: get_presidential_winner(row["state"], int(row["year"])),
        axis=1,
    )

    party_year = (
        rpp_df.groupby(["year", "presidential_winner"], as_index=False)["rpp_change_percent"]
        .mean()
        .rename(columns={"rpp_change_percent": "average_rpp_change_percent"})
    )

    fig = go.Figure()
    colors = {"Democratic": "#1f77b4", "Republican": "#d62728"}
    for party in ["Democratic", "Republican"]:
        party_data = party_year[party_year["presidential_winner"] == party]
        fig.add_trace(go.Scatter(
            x=party_data["year"],
            y=party_data["average_rpp_change_percent"],
            mode="lines+markers",
            name=party,
            line={"color": colors[party]},
        ))

    fig.update_layout(
        title="Average Year-over-Year RPP Change by Presidential Vote Winner",
        xaxis_title="Year",
        yaxis_title="Average RPP change (%)",
        hovermode="x unified",
        legend_title="State presidential vote winner",
    )
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    return fig


if __name__ == "__main__":
    panel4fig().show()
