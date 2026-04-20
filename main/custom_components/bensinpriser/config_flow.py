import os
import voluptuous as vol
import requests
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN
import logging

LANS = [
    "blekinge-lan", "dalarnas-lan", "gavleborgs-lan", "gotlands-lan",
    "hallands-lan", "jamtlands-lan", "jonkoping-lan", "kalmar-lan",
    "kronobergs-lan", "norrbottens-lan", "orebro-lan", "ostergotlands-lan",
    "skane-lan", "sodermanlands-lan", "stockholms-lan", "uppsala-lan",
    "varmlands-lan", "vasterbottens-lan", "vasternorrlands-lan",
    "vastmanlands-lan", "vastra-gotalands-lan"
]

_LOGGER = logging.getLogger(__name__)

def get_stations(lan):
    try:
        response = requests.get(f"https://henrikhjelm.se/api/getdata.php?lan={lan}")
        response.raise_for_status()
        data = response.json()
        _LOGGER.debug(f"Data fetched for lan {lan}: {data}")
        stations = []
        for name, price in data.items():
            stations.append(f"{price} - {name}")
        _LOGGER.debug(f"Stations for lan {lan}: {stations}")
        return stations
    except Exception as e:
        _LOGGER.error(f"Error fetching stations for lan {lan}: {e}")
        return []

def load_api_key_from_env():
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

class BensinpriserConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.lan = user_input["lan"]
            self.subscription_key = user_input["subscription_key"]
            return await self.async_step_station()

        api_key_default = load_api_key_from_env() or ""
        data_schema = vol.Schema({
            vol.Required("subscription_key", default=api_key_default): str,
            vol.Required("lan"): vol.In(LANS)
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_station(self, user_input=None):
        errors = {}
        stations = await self.hass.async_add_executor_job(get_stations, self.lan)
        if not stations:
            errors["base"] = "no_stations"
            return self.async_show_form(step_id="station", data_schema=vol.Schema({vol.Required("station"): vol.In([])}), errors=errors)

        # Skapa en mapping så vi kan plocka ut station+bränsle från val i dropdown
        station_map = {s: s.split(' - ', 1)[-1] if ' - ' in s else s for s in stations}

        if user_input is not None:
            selected = user_input["station"]
            station_id = station_map.get(selected, selected)
            return self.async_create_entry(
                title=f"Bensinpriser {self.lan} {station_id}",
                data={
                    "lan": self.lan,
                    "station": station_id,
                    "subscription_key": getattr(self, 'subscription_key', None)
                }
            )

        data_schema = vol.Schema({
            vol.Required("station"): vol.In(stations)
        })

        return self.async_show_form(step_id="station", data_schema=data_schema, errors=errors)
