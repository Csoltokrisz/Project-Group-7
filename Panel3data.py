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
