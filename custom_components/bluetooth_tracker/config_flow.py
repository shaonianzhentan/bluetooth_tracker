from __future__ import annotations

from typing import Any
import voluptuous as vol
from homeassistant.helpers.device_registry import format_mac
import homeassistant.helpers.config_validation as cv

from homeassistant.core import callback
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry

from .const import DOMAIN

DATA_SCHEMA = vol.Schema({
    vol.Required("ip"): str,
    vol.Required("mac"): str
})

class SimpleConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input = None):
    
        if user_input is None:
            errors = {}
            entity_list = {}
            # 读取当前人员
            states = self.hass.states.async_all()
            for state in states:
                domain = state.domain
                if domain == 'person':
                    attributes = state.attributes
                    entity_id = state.entity_id
                    friendly_name = attributes.get('friendly_name')
                    if friendly_name is not None:
                        entity_list[entity_id] = friendly_name

            DATA_SCHEMA = vol.Schema({
                vol.Required("ip"): str,
                vol.Required("mac"): str,                
                vol.Required("person", default=[]): vol.In(entity_list)
            })
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

        return self.async_create_entry(title=user_input['ip'], data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry):
        return OptionsFlowHandler(entry)

class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is None:
            errors = {}
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)
        # 选项更新
        return self.async_create_entry(title=user_input['ip'], data={})