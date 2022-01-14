from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN
from .bluetooth_tracker import BluetoothTracker

CONFIG_SCHEMA = cv.deprecated(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    print('async_setup_entry', entry.data)
    cfg = entry.data
    options = entry.options
    person = cfg.get('person')
    host = options.get('ip')
    mac = options.get('mac')
    if host is not None and mac is not None:
        hass.data[f'{DOMAIN}{person}'] = BluetoothTracker(hass, host, mac, person)
    
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def update_listener(hass, entry):
    """Handle options update."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    print('async_unload_entry', entry.data)
    cfg = entry.data
    person = cfg.get('person')
    key = f'{DOMAIN}{person}'
    if key in hass.data:
        hass.data[key].remove_listener()
        hass.data.pop(key)
    return True
