import os
import requests
import json
import time

# API details from fuel-product-prices.yaml
base_url = "https://api.okq8.se/stationFuelProductPrices/v1"
endpoint = "/prices"

def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

load_env_file()
subscription_key = os.getenv('OKQ8_SUBSCRIPTION_KEY', '')

# Headers for API calls
headers = {
    "Ocp-Apim-Subscription-Key": subscription_key,
    "DefaultHeader": json.dumps({
        "transactionId": "eacab7fb-74d6-ec11-a7b5-000d3a4a5fec",
        "systemName": "1012",
        "ipAddress": "100.45.67.01",
        "hostName": "HOSTPC",
        "userToken": "Unique data",
        "serviceToken": "unique data"
    })
}

def fetch_all_prices():
    all_stations = []
    page = 1
    page_size = 100  # Max per page

    while True:
        params = {
            "page": page,
            "pageSize": page_size
        }
        url = base_url + endpoint
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'stationsPrices' in data and data['stationsPrices']:
                all_stations.extend(data['stationsPrices'])
                total_pages = data.get('totalPages', 1)
                if page >= total_pages:
                    break
                page += 1
                time.sleep(1)  # Rate limiting
            else:
                break
        else:
            print(f"API error: {response.status_code} - {response.text}")
            return None

    return all_stations

# Function to normalize address to station name format
def normalize_station_name(address):
    if not address:
        return "unknown_station"

    # Example normalization: replace spaces, commas, etc.
    # This needs to be adjusted based on actual mapping
    normalized = address.replace(' ', '_').replace(',', '').replace('.', '').lower()
    # Remove city/postal code if present
    parts = normalized.split('_')
    # Assume last parts are city, remove them
    # This is simplistic; may need better logic
    return '_'.join(parts[:-2]) if len(parts) > 2 else normalized

# Function to map fuel types
fuel_mapping = {
    "95": "95",
    "98": "98",
    "diesel": "diesel",
    "etanol": "etanol",
    "biodiesel": "biodiesel",
    "fordonsgas": "fordonsgas"
    # Add more mappings as needed
}

def format_as_apisvar(stations):
    formatted = {}  # Start fresh for Sweden data
    lan = "sverige"  # Use all Sweden stations

    for station in stations:
        station_id = station.get('stationId', '')
        address = station.get('address', '')
        station_name = normalize_station_name(address)
        brand = "OKQ8"  # Assuming all are OKQ8

        if 'products' in station:
            for product in station['products']:
                product_name = product.get('productName', '').lower().replace(' ', '').replace('benzin', '')
                fuel_type = fuel_mapping.get(product_name, product_name)
                price = str(product.get('price', 0))
                key = f"{lan}_{brand}_{station_name}__{fuel_type}"
                formatted[key] = price

    return formatted

if __name__ == "__main__":
    if not subscription_key:
        print("Error: OKQ8 subscription key not found. Add OKQ8_SUBSCRIPTION_KEY to .env or environment variables.")
    else:
        stations = fetch_all_prices()
        if stations:
            formatted_data = format_as_apisvar(stations)
            print(json.dumps(formatted_data, indent=4, ensure_ascii=False))
        else:
            print("Failed to fetch data")