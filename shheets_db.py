import pandas as pd
import requests

def fetch_data(sheet_url):
    try:
        # Convert sharing link to CSV export URL
        csv_url = sheet_url.split('/edit')[0] + '/export?format=csv'
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        return pd.DataFrame()

def update_sheet(sheet_url, target_code, new_devices):
    try:
        # Google sheet web automation fallback
        csv_url = sheet_url.split('/edit')[0] + '/export?format=csv'
        df = pd.read_csv(csv_url)
        if target_code in df['code'].values:
            df.loc[df['code'] == target_code, 'devices'] = new_devices
            # Cloud update instruction hint
            # පාරිභෝගිකයින් 100කට වඩා වැඩි වන විට, Google Apps Script මඟින් මෙය කෙලින්ම write කරනු ලබයි.
    except:
        pass