import pandas as pd
import requests
from io import StringIO

def fetch_owid_data(metric="life_expectancy", country="India"):
    print(f"📡 Fetching data for metric: {metric}, country: {country}")
    try:
        # Try OWID-datasets GitHub repo
        base_url = f"https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/{metric}/data/{metric}.csv"
        response = requests.get(base_url)
        if response.status_code == 200:
            print("✅ Found dataset in OWID-datasets")
            df = pd.read_csv(StringIO(response.text))
        else:
            raise ValueError("Not found in OWID-datasets")
    except:
        # Fallback to OWID COVID dataset
        print("⚠️ Falling back to OWID COVID dataset")
        covid_url = "https://covid.ourworldindata.org/data/owid-covid-data.csv"
        try:
            df = pd.read_csv(covid_url)
        except Exception as e:
            print(f"❌ Failed to download fallback dataset: {e}")
            return pd.DataFrame()

        if metric not in df.columns:
            print(f"❌ Metric '{metric}' not found in fallback COVID dataset.")
            return pd.DataFrame()

    if 'location' in df.columns:
        df = df[df['location'] == country]

    if 'date' not in df.columns or metric not in df.columns:
        print("❌ Required columns missing in dataset")
        return pd.DataFrame()

    df = df[['date', metric]].dropna()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', metric])
    df = df.sort_values('date').reset_index(drop=True)

    print(f"📈 Loaded {len(df)} valid records.")
    return df
