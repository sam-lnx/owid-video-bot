import pandas as pd
import requests
from io import StringIO

def fetch_owid_data(metric="life_expectancy", country="India"):
    try:
        # Primary OWID dataset repo (GitHub raw CSV)
        base_url = f"https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/{metric}/data/{metric}.csv"
        response = requests.get(base_url)
        if response.status_code != 200:
            raise ValueError("Metric not found in OWID-datasets repo")
        df = pd.read_csv(StringIO(response.text))
    except:
        # Fallback to COVID dataset
        covid_url = "https://covid.ourworldindata.org/data/owid-covid-data.csv"
        df = pd.read_csv(covid_url)
        if metric not in df.columns:
            raise ValueError(f"Metric '{metric}' not found in fallback dataset")

    if 'location' in df.columns:
        df = df[df['location'] == country]

    df = df[['date', metric]].dropna()
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values('date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
