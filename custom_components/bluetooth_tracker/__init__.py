from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN
from .bluetooth_tracker import BluetoothTracker

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    print('async_setup_entry', entry.data)
    cfg = entry.data
    host = cfg.get('ip')
    mac = cfg.get('mac')
    person = cfg.get('person')
    hass.data[f'{DOMAIN}{person}'] = BluetoothTracker(hass, host, mac, person)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    print('async_unload_entry', entry.data)
    cfg = entry.data
    person = cfg.get('person')
    key = f'{DOMAIN}{person}'
    hass.data[key].remove_listener()
    hass.data.pop(key)
    return True
