
from __future__ import annotations
from datetime import datetime, timedelta
from asyncio import sleep

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode, ClimateEntityFeature
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval, async_call_later
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .const import *
from .helpers import clamp, is_night


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    async_add_entities([SmartSplitThermostat(hass, entry)], True)


class SmartSplitThermostat(ClimateEntity, RestoreEntity):
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_precision = 0.1
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.DRY]
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry):
        self.hass = hass
        self.entry = entry
        d = entry.data
        o = {**DEFAULTS, **entry.options}
        self._name = d[CONF_NAME]
        self._unique_id = f"smartsplit_{entry.entry_id}"
        self._ac = d[CONF_AC_ENTITY]
        self._t_sens = d[CONF_TEMP_SENSOR]
        self._h_sens = d.get(CONF_HUM_SENSOR)
        self._w_sens = d.get(CONF_WINDOW_SENSOR)
        self._target: float = d.get(CONF_TARGET_INIT, DEFAULTS[CONF_TARGET_INIT])
        self._mode: HVACMode = HVACMode.OFF
        self.opts = o
        self._last_adj: datetime | None = None
        self._last_autotune: datetime | None = None
        self._restored_mode: HVACMode | None = None
        self._restore_timer = None
        async_track_state_change_event(hass, [self._t_sens, self._ac], self._on_state)
        if self._h_sens:
            async_track_state_change_event(hass, [self._h_sens], self._on_state)
        if self._w_sens:
            async_track_state_change_event(hass, [self._w_sens], self._on_window)
        self._unsub_timer = async_track_time_interval(hass, self._tick, timedelta(minutes=5))

    async def async_added_to_hass(self):
        # Restore last known target/mode
        last = await self.async_get_last_state()
        if last:
            try:
                if last.state in [m.value for m in HVACMode]:
                    self._mode = HVACMode(last.state)
            except Exception:
                pass
            try:
                t = last.attributes.get("temperature")
                if t is not None:
                    self._target = float(t)
            except Exception:
                pass
        # Adjust exposed hvac_modes to match underlying AC (plus OFF)
        ac = self.hass.states.get(self._ac)
        if ac:
            try:
                ac_modes = set(ac.attributes.get("hvac_modes", []))
                allowed = [m for m in [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.DRY] if (m == HVACMode.OFF or m.value in ac_modes)]
                if allowed:
                    self._attr_hvac_modes = allowed
            except Exception:
                pass
        self.async_write_ha_state()

    # ---- properties
    @property
    def name(self): return self._name
    @property
    def unique_id(self): return self._unique_id
    @property
    def hvac_modes(self): return self._attr_hvac_modes
    @property
    def hvac_mode(self): return self._mode
    @property
    def current_temperature(self):
        st = self.hass.states.get(self._t_sens)
        try: return float(st.state)
        except Exception: return None
    @property
    def target_temperature(self): return self._target
    @property
    def supported_features(self): return self._attr_supported_features

    # ---- UI setters
    async def async_set_temperature(self, **kwargs):
        if "temperature" in kwargs:
            self._target = float(kwargs["temperature"])
            await self._maybe_act(reason="target_changed")
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: str):
        self._mode = HVACMode(hvac_mode)
        if self._w_sens and self._is_window_open():
            self._restored_mode = self._mode
            self._mode = HVACMode.OFF
        await self._maybe_act(reason="mode_changed")
        self.async_write_ha_state()

    # ---- helpers
    def _is_window_open(self) -> bool:
        if not self._w_sens: return False
        st = self.hass.states.get(self._w_sens)
        return bool(st and st.state == "on")

    @callback
    async def _on_window(self, event):
        if not self._w_sens: return
        if self._is_window_open():
            if self._mode != HVACMode.OFF:
                self._restored_mode = self._mode
                self._mode = HVACMode.OFF
                await self._turn_off_real()
                self.async_write_ha_state()
        else:
            # one-shot delayed restore after 5 minutes closed
            if self._restore_timer:
                self._restore_timer()  # cancel previous
            def _cb(now):
                if not self._is_window_open() and self._restored_mode:
                    self.hass.async_create_task(self.async_set_hvac_mode(self._restored_mode))
                    self._restored_mode = None
            self._restore_timer = async_call_later(self.hass, 300, _cb)

    @callback
    async def _on_state(self, event):
        await self._maybe_act(reason="state_change")

    async def _tick(self, now):
        await self._maybe_act(reason="timer")

    def _rate_limit_ok(self, now: datetime) -> bool:
        if not self._last_adj: return True
        day = self.opts.get(CONF_RATE_DAY_MIN, 0)
        night = self.opts.get(CONF_RATE_NIGHT_MIN, 0)
        need_min = night if is_night(now) else day
        if need_min <= 0: return True
        return (now - self._last_adj) >= timedelta(minutes=need_min)

    def _safe_float(self, entity_id: str, default=None):
        st = self.hass.states.get(entity_id)
        try: return float(st.state)
        except Exception: return default

    # ---- core logic
    async def _maybe_act(self, reason: str):
        now = datetime.now()
        if self._mode == HVACMode.OFF:
            await self._turn_off_real()
            return

        # DRY mode handling
        if self._mode == HVACMode.DRY and self.opts.get(CONF_DRY_ENABLED) and self._h_sens:
            rh = self._safe_float(self._h_sens, default=None)
            if rh is None: return
            rh_t = self.opts[CONF_RH_TARGET]
            band = self.opts[CONF_RH_BAND]
            high = rh_t + band
            low = rh_t - band
            ac = self.hass.states.get(self._ac)
            if rh >= high and (not ac or ac.state != HVACMode.DRY):
                await self._set_ac_mode(HVACMode.DRY)
            elif rh <= low:
                await self._turn_off_real()
            return

        tnow = self._safe_float(self._t_sens, default=None)
        if tnow is None: return
        target = self._target
        ac = self.hass.states.get(self._ac)
        curr_sp = float(ac.attributes.get("temperature", target)) if ac else target
        up_boost = self.opts[CONF_UP_BOOST]
        down_boost = self.opts[CONF_DOWN_BOOST]

        if self._mode == HVACMode.HEAT:
            desired_mode = HVACMode.HEAT
            on_d = self.opts[CONF_HEAT_ON_DELTA]
            off_d = self.opts[CONF_HEAT_OFF_DELTA]
            base = self.opts[CONF_BASELINE_HEAT]
            cold = tnow <= (target - on_d)
            hot = tnow >= (target - off_d)
            if cold: desired_sp = clamp(base + up_boost, 16.0, 26.0)
            elif hot: desired_sp = clamp(base - down_boost, 16.0, 26.0)
            else: desired_sp = base
        elif self._mode == HVACMode.COOL:
            desired_mode = HVACMode.COOL
            on_d = self.opts[CONF_COOL_ON_DELTA]
            off_d = self.opts[CONF_COOL_OFF_DELTA]
            base = self.opts[CONF_BASELINE_COOL]
            hot = tnow >= (target + on_d)
            cool_ok = tnow <= (target + off_d)
            if hot: desired_sp = clamp(base - up_boost, 16.0, 30.0)
            elif cool_ok: desired_sp = clamp(base + down_boost, 16.0, 30.0)
            else: desired_sp = base
        else:
            return

        if not self._rate_limit_ok(now): return

        if not ac or ac.state != desired_mode:
            await self._set_ac_mode(desired_mode)

        if abs((curr_sp or 0) - desired_sp) >= 0.05:
            await self._set_ac_temp(desired_sp)
            self._last_adj = now
            if self.opts.get(CONF_WATCHDOG_ENABLED, True):
                await self._watchdog(desired_sp, desired_mode)

        if self.opts.get(CONF_AUTOTUNE_ENABLED, True):
            await self._maybe_autotune(now, tnow, target)

    async def _maybe_autotune(self, now: datetime, tnow: float, target: float):
        if self._last_autotune and (now - self._last_autotune) < timedelta(hours=self.opts[CONF_AUTOTUNE_MIN_GAP_H]):
            return
        bias = tnow - target
        db = self.opts[CONF_AUTOTUNE_DEADBAND]
        step = self.opts[CONF_AUTOTUNE_STEP]
        if abs(bias) < db: return
        if self._mode == HVACMode.HEAT:
            b = self.opts[CONF_BASELINE_HEAT]
            self.opts[CONF_BASELINE_HEAT] = clamp(round((b - step if bias > 0 else b + step)*2)/2, 16.0, 26.0)
        elif self._mode == HVACMode.COOL:
            b = self.opts[CONF_BASELINE_COOL]
            self.opts[CONF_BASELINE_COOL] = clamp(round((b - step if bias < 0 else b + step)*2)/2, 16.0, 30.0)
        self._last_autotune = now
        self.hass.config_entries.async_update_entry(self.entry, options=self.opts)

    # ---- low level
    async def _set_ac_mode(self, mode: HVACMode):
        await self.hass.services.async_call(
            CLIMATE_DOMAIN, "set_hvac_mode",
            {"entity_id": self._ac, "hvac_mode": mode.value if hasattr(mode, "value") else mode}
        )

    async def _set_ac_temp(self, temp: float):
        await self.hass.services.async_call(
            CLIMATE_DOMAIN, "set_temperature",
            {"entity_id": self._ac, "temperature": float(temp)}
        )

    async def _turn_off_real(self):
        await self.hass.services.async_call(CLIMATE_DOMAIN, "turn_off", {"entity_id": self._ac})

    async def _watchdog(self, desired_sp: float, mode: HVACMode):
        await sleep(180)
        ac = self.hass.states.get(self._ac)
        sp = float(ac.attributes.get("temperature", 0)) if ac else 0
        if abs(sp - desired_sp) >= 0.2:
            await self._turn_off_real()
            await sleep(20)
            await self._set_ac_mode(mode)
            await sleep(5)
            await self._set_ac_temp(desired_sp)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._unique_id)}, name=self._name)
