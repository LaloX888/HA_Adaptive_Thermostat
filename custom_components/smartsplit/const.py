
DOMAIN = "smartsplit"

CONF_NAME = "name"
CONF_AC_ENTITY = "ac_entity"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_HUM_SENSOR = "hum_sensor"
CONF_WINDOW_SENSOR = "window_sensor"

CONF_TARGET_INIT = "target_init"

# Thresholds & boosts
CONF_HEAT_ON_DELTA = "heat_on_delta"
CONF_HEAT_OFF_DELTA = "heat_off_delta"
CONF_COOL_ON_DELTA = "cool_on_delta"
CONF_COOL_OFF_DELTA = "cool_off_delta"

CONF_UP_BOOST = "up_boost"
CONF_DOWN_BOOST = "down_boost"

# Baselines
CONF_BASELINE_HEAT = "baseline_heat"
CONF_BASELINE_COOL = "baseline_cool"

# Autotune
CONF_AUTOTUNE_ENABLED = "autotune_enabled"
CONF_AUTOTUNE_DEADBAND = "autotune_deadband"
CONF_AUTOTUNE_STEP = "autotune_step"
CONF_AUTOTUNE_MIN_GAP_H = "autotune_min_gap_h"

# DRY
CONF_DRY_ENABLED = "dry_enabled"
CONF_RH_TARGET = "rh_target"
CONF_RH_BAND = "rh_band"

# Rate limit & watchdog
CONF_RATE_DAY_MIN = "rate_day_min"
CONF_RATE_NIGHT_MIN = "rate_night_min"
CONF_WATCHDOG_ENABLED = "watchdog_enabled"

DEFAULTS = {
    CONF_TARGET_INIT: 23.0,
    CONF_HEAT_ON_DELTA: 0.2,
    CONF_HEAT_OFF_DELTA: 0.0,
    CONF_COOL_ON_DELTA: 0.2,
    CONF_COOL_OFF_DELTA: 0.0,
    CONF_UP_BOOST: 3.5,
    CONF_DOWN_BOOST: 3.5,
    CONF_BASELINE_HEAT: 21.5,
    CONF_BASELINE_COOL: 25.0,
    CONF_AUTOTUNE_ENABLED: True,
    CONF_AUTOTUNE_DEADBAND: 0.3,
    CONF_AUTOTUNE_STEP: 0.5,
    CONF_AUTOTUNE_MIN_GAP_H: 4,
    CONF_DRY_ENABLED: True,
    CONF_RH_TARGET: 55,
    CONF_RH_BAND: 2,
    CONF_RATE_DAY_MIN: 0,
    CONF_RATE_NIGHT_MIN: 0,
    CONF_WATCHDOG_ENABLED: True,
}
