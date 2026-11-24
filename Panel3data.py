import pandas as pd
def get_economic_data():
    cpi = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL")
    rates = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS")
  cpi['observation_date'] = pd.to_datetime(cpi['observation_date'])
    rates['observation_date'] = pd.to_datetime(rates['observation_date'])
    
    cpi['Year'] = cpi['observation_date'].dt.year
    rates['Year'] = rates['observation_date'].dt.year
    
    cpi = cpi[(cpi['Year'] >= 1995) & (cpi['Year'] <= 2025)]
    rates = rates[(rates['Year'] >= 1995) & (rates['Year'] <= 2025)]
    
    annual_cpi = cpi.groupby('Year')['CPIAUCSL'].mean().reset_index()
    annual_cpi['Inflation Rate (%)'] = annual_cpi['CPIAUCSL'].pct_change() * 100
    
    annual_rates = rates.groupby('Year')['FEDFUNDS'].mean().reset_index()
    annual_rates.rename(columns={'FEDFUNDS': 'Interest Rate (%)'}, inplace=True)
    
    df = pd.merge(annual_cpi[['Year', 'Inflation Rate (%)']], 
                  annual_rates[['Year', 'Interest Rate (%)']], 
                  on='Year')
    
    return df.dropna().reset_index(drop=True)
