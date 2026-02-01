import pandas as pd
import requests

def debug_tables():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    print(f"Fetching {url}...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    try:
        tables = pd.read_html(response.text)
        print(f"Found {len(tables)} tables.")
        
        for i, df in enumerate(tables[:3]):
            print(f"\n--- Table {i} ---")
            print(f"Columns: {df.columns.tolist()}")
            print(f"First row: {df.iloc[0].tolist() if not df.empty else 'EMPTY'}")
            
    except Exception as e:
        print(f"Error parsing tables: {e}")

if __name__ == "__main__":
    debug_tables()
