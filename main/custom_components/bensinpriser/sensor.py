import logging
import os
import json
import requests
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from homeassistant.components.sensor import SensorEntity

SCAN_INTERVAL = timedelta(minutes=180)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    try:
        _LOGGER.debug(f"Setting up entry {entry.entry_id} with data: {entry.data}")

        # Create an instance of coordinator and first update
        coordinator = BensinpriserDataUpdateCoordinator(
            hass,
            entry.data.get("lan"),
            entry.data.get("station"),
            entry.data.get("subscription_key")
        )
        await coordinator.async_config_entry_first_refresh()

        # Add sensor entity
        sensor_name = f"{entry.data.get('lan')}_{entry.data.get('station')}"
        async_add_entities([BensinpriserSensor(coordinator, sensor_name)])

        # Debug
        _LOGGER.debug(f"Added sensor {sensor_name}")
        _LOGGER.debug(f"Coordinator data: {coordinator.data}")
        _LOGGER.debug(f"Coordinator last update success: {coordinator.last_update_success}")

        # Save coordinator in hass.data
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        
        hass.data[DOMAIN][entry.entry_id] = coordinator

        _LOGGER.debug(f"Successfully set up entry {entry.entry_id}")
        return True

    except Exception as e:
        _LOGGER.error(f"Error setting up entry {entry.entry_id}: {e}")
        return False

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

def load_env_api_key():
    env_key = os.getenv('OKQ8_SUBSCRIPTION_KEY')
    if env_key:
        return env_key

    env_paths = [
        os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '.env')),
        os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')),
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, value = line.split('=', 1)
                    if key.strip() == 'OKQ8_SUBSCRIPTION_KEY':
                        return value.strip().strip('"').strip("'")
    return None

class BensinpriserDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, lan: str, station: str, subscription_key: str | None = None):
        self.lan = lan
        self.station = station
        self.subscription_key = subscription_key or load_env_api_key()
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        try:
            url = f"https://henrikhjelm.se/api/getdata.php?lan={self.lan}"
            _LOGGER.debug(f"Fetching data from URL: {url}")
            response = await self.hass.async_add_executor_job(requests.get, url)
            response.raise_for_status()
            data = response.json()  # Convert response to JSON
            _LOGGER.debug(f"Data fetched: {data}")

            if self.station in data and data[self.station] not in (None, "0", "0.0", ""):
                return data[self.station]

            if self.subscription_key:
                okq8_price = await self.hass.async_add_executor_job(self._fetch_okq8_price)
                if okq8_price is not None:
                    return okq8_price

            if self.station in data:
                return data[self.station]

            raise UpdateFailed(f"Station {self.station} not found in data")
        except Exception as e:
            raise UpdateFailed(f"Error fetching data: {e}")

    def _fetch_okq8_price(self):
        if not self.subscription_key:
            return None

        def normalize(text: str) -> str:
            return ''.join(ch for ch in text.lower() if ch.isalnum() or ch.isspace())

        station_query = self.station
        if '__' in self.station:
            station_query, fuel_code = self.station.rsplit('__', 1)
        else:
            fuel_code = ''

        station_query = station_query.split('_', 1)[-1] if '_' in station_query else station_query
        station_query = normalize(station_query.replace('okq8', '').replace('st1', ''))
        headers = {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "DefaultHeader": json.dumps({
                "transactionId": "eacab7fb-74d6-ec11-a7b5-000d3a4a5fec",
                "systemName": "1012",
                "ipAddress": "100.45.67.01",
                "hostName": "HOSTPC",
                "userToken": "Unique data",
                "serviceToken": "unique data"
            })
        }
        page = 1
        page_size = 100

        while True:
            params = {"page": page, "pageSize": page_size}
            response = requests.get("https://api.okq8.se/stationFuelProductPrices/v1/prices", headers=headers, params=params)
            if response.status_code != 200:
                _LOGGER.warning(f"OKQ8 fallback error: {response.status_code} - {response.text}")
                return None
            data = response.json()
            for station in data.get('stationsPrices', []):
                address = normalize(station.get('address', '') or '')
                if station_query and station_query not in address:
                    continue
                for product in station.get('products', []):
                    if fuel_code and (product.get('productId') == fuel_code or normalize(product.get('productName', '')) == normalize(fuel_code)):
                        return str(product.get('price', 0))
            total_pages = data.get('totalPages', 1)
            if page >= total_pages:
                break
            page += 1
        return None

class BensinpriserSensor(SensorEntity):
    def __init__(self, coordinator: BensinpriserDataUpdateCoordinator, name: str):
        super().__init__()
        _LOGGER.debug(f"Creating BensinpriserSensor: {name}")
        self.coordinator = coordinator
        self._name = name
        self._state = self.coordinator.data
        self._attr_extra_state_attributes = {}

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return "kr/l"

    async def async_update(self):
        _LOGGER.debug(f"Updating BensinpriserSensor: {self._name}")
        await self.coordinator.async_request_refresh()
        data = self.coordinator.data

        _LOGGER.debug(f"Data received for update: {data}")
        try:
            self._state = data
            self._attr_extra_state_attributes = {}
            
        except Exception as e:
            _LOGGER.error(f"Error updating BensinpriserSensor {self._name}: {e}")

        _LOGGER.debug(f"Updated BensinpriserSensor {self._name} to state: {self._state}")

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes

    @property
    def unique_id(self):
        return f"{self.coordinator.lan}_{self.coordinator.station}"

    @property
    def available(self):
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def should_poll(self):
        return True

    @property
    def icon(self):
        return "mdi:gas-station"