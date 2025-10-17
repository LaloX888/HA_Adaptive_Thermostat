
from __future__ import annotations
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from homeassistant.const import CONF_NAME
from .const import *

class SmartSplitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str,Any] | None=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input, options=DEFAULTS.copy())

        dev_sel = selector.selector({"entity": {"domain": "climate"}})
        sensor_sel = selector.selector({"entity": {"domain": "sensor"}})
        bin_sel = selector.selector({"entity": {"domain": "binary_sensor"}})
        schema = vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_AC_ENTITY): dev_sel,
            vol.Required(CONF_TEMP_SENSOR): sensor_sel,
            vol.Optional(CONF_HUM_SENSOR): sensor_sel,
            vol.Optional(CONF_WINDOW_SENSOR): bin_sel,
            vol.Optional(CONF_TARGET_INIT, default=DEFAULTS[CONF_TARGET_INIT]): vol.Coerce(float),
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_import(self, import_data):
        return await self.async_step_user(import_data)

    async def async_get_options_flow(self, config_entry):
        return SmartSplitOptionsFlowHandler(config_entry)

class SmartSplitOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        o = {**DEFAULTS, **self.entry.options}

        schema = vol.Schema({
            vol.Required(CONF_HEAT_ON_DELTA, default=o[CONF_HEAT_ON_DELTA]): vol.Coerce(float),
            vol.Required(CONF_HEAT_OFF_DELTA, default=o[CONF_HEAT_OFF_DELTA]): vol.Coerce(float),
            vol.Required(CONF_COOL_ON_DELTA, default=o[CONF_COOL_ON_DELTA]): vol.Coerce(float),
            vol.Required(CONF_COOL_OFF_DELTA, default=o[CONF_COOL_OFF_DELTA]): vol.Coerce(float),
            vol.Required(CONF_UP_BOOST, default=o[CONF_UP_BOOST]): vol.Coerce(float),
            vol.Required(CONF_DOWN_BOOST, default=o[CONF_DOWN_BOOST]): vol.Coerce(float),
            vol.Required(CONF_BASELINE_HEAT, default=o[CONF_BASELINE_HEAT]): vol.Coerce(float),
            vol.Required(CONF_BASELINE_COOL, default=o[CONF_BASELINE_COOL]): vol.Coerce(float),
            vol.Required(CONF_AUTOTUNE_ENABLED, default=o[CONF_AUTOTUNE_ENABLED]): bool,
            vol.Required(CONF_AUTOTUNE_DEADBAND, default=o[CONF_AUTOTUNE_DEADBAND]): vol.Coerce(float),
            vol.Required(CONF_AUTOTUNE_STEP, default=o[CONF_AUTOTUNE_STEP]): vol.Coerce(float),
            vol.Required(CONF_AUTOTUNE_WINDOW_H, default=o[CONF_AUTOTUNE_WINDOW_H]): vol.Coerce(int),
            vol.Required(CONF_AUTOTUNE_MIN_GAP_H, default=o[CONF_AUTOTUNE_MIN_GAP_H]): vol.Coerce(int),
            vol.Required(CONF_DRY_ENABLED, default=o[CONF_DRY_ENABLED]): bool,
            vol.Required(CONF_RH_TARGET, default=o[CONF_RH_TARGET]): vol.Coerce(int),
            vol.Required(CONF_RH_BAND, default=o[CONF_RH_BAND]): vol.Coerce(int),
            vol.Required(CONF_RATE_DAY_MIN, default=o[CONF_RATE_DAY_MIN]): vol.Coerce(int),
            vol.Required(CONF_RATE_NIGHT_MIN, default=o[CONF_RATE_NIGHT_MIN]): vol.Coerce(int),
            vol.Required(CONF_WATCHDOG_ENABLED, default=o[CONF_WATCHDOG_ENABLED]): bool,
        })
        return self.async_show_form(step_id="init", data_schema=schema)
