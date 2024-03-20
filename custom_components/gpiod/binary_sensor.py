from __future__ import annotations

from . import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
from homeassistant.const import CONF_SENSORS, CONF_NAME, CONF_PORT, CONF_UNIQUE_ID
CONF_INVERT_LOGIC = "invert_logic"
DEFAULT_INVERT_LOGIC = False
CONF_PULL_MODE = "pull_mode"
DEFAULT_PULL_MODE = "UP"
CONF_DEBOUNCE= "debounce"
DEFAULT_DEBOUNCE = 50

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Exclusive(CONF_SENSORS, CONF_SENSORS): vol.All(
                cv.ensure_list, [{
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_PORT): cv.positive_int,
                    vol.Optional(CONF_UNIQUE_ID): cv.string,
                    vol.Optional(CONF_INVERT_LOGIC, default=False): cv.boolean,
                    vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): cv.string,
                    vol.Optional(CONF_DEBOUNCE, default=DEFAULT_DEBOUNCE): cv.positive_int
                }]
            )
        }
    )
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None) -> None:
    
    _LOGGER.debug(f"setup_platform: {config}")
    hub = hass.data[DOMAIN]

    sensors = []
    for sensor in config.get(CONF_SENSORS):
        sensors.append(
            GPIODBinarySensor(
                hub,
                sensor[CONF_NAME],
                sensor[CONF_PORT],
                sensor.get(CONF_UNIQUE_ID) or f"gpio_{sensor[CONF_PORT]}_{sensor[CONF_NAME].lower().replace(' ', '_')}",
                sensor.get(CONF_INVERT_LOGIC),
                sensor.get(CONF_PULL_MODE),
                sensor.get(CONF_DEBOUNCE)
            )
        )

    add_entities(sensors)


class GPIODBinarySensor(BinarySensorEntity):
    def __init__(self, hub, name, port, unique_id, invert_logic, pull_mode, debounce):
        _LOGGER.debug(f"GPIODBinarySensor init: {port} - {name} - {unique_id}")
        self._hub = hub
        self._attr_name = name
        self._port = port
        self._attr_unique_id = unique_id
        self._invert_logic = invert_logic
        self._pull_mode = pull_mode
        self._debounce = debounce
        self._attr_should_poll = False
        self._state = False != invert_logic
        hub.add_sensor(port, invert_logic, pull_mode, debounce)

    @property
    def name(self) -> str:
        return self._attr_name

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    @property
    def is_on(self): 
        return self._state

    def update(self):
        self._state = self.hub.update(self._port)
