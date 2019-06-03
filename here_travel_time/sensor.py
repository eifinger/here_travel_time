"""Support for HERE travel time sensors."""
import logging
from datetime import datetime
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME,
    EVENT_HOMEASSISTANT_START,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_MODE,
)
from homeassistant.helpers import location
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

CONF_DESTINATION = "destination"
CONF_ORIGIN = "origin"
CONF_APP_ID = "app_id"
CONF_APP_CODE = "app_code"
CONF_TRAFFIC_MODE = "traffic_mode"

DEFAULT_NAME = "HERE Travel Time"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)

TRAVEL_MODE_CAR = "car"
TRAVEL_MODE_PEDESTRIAN = "pedestrian"
TRAVEL_MODE_PUBLIC = "publicTransport"
TRAVEL_MODE_TRUCK = "truck"
TRAVEL_MODE = [
    TRAVEL_MODE_CAR,
    TRAVEL_MODE_PEDESTRIAN,
    TRAVEL_MODE_PUBLIC,
    TRAVEL_MODE_TRUCK,
]
TRAFFIC_MODE_ENABLED = "traffic:enabled"
TRAFFIC_MODE_DISABLED = "traffic:disabled"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_APP_ID): cv.string,
        vol.Required(CONF_APP_CODE): cv.string,
        vol.Required(CONF_DESTINATION): cv.string,
        vol.Required(CONF_ORIGIN): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_MODE, default=TRAVEL_MODE_CAR): vol.In(TRAVEL_MODE),
        vol.Optional(CONF_TRAFFIC_MODE, default=False): cv.boolean,
    }
)

TRACKABLE_DOMAINS = ["device_tracker", "sensor", "zone", "person"]
DATA_KEY = "here_travel_time"


def convert_time_to_utc(timestr):
    """Take a string like 08:00:00 and convert it to a unix timestamp."""
    combined = datetime.combine(
        dt_util.start_of_local_day(), dt_util.parse_time(timestr)
    )
    if combined < datetime.now():
        combined = combined + timedelta(days=1)
    return dt_util.as_timestamp(combined)


def setup_platform(hass, config, add_entities_callback, discovery_info=None):
    """Set up the HERE travel time platform."""

    def run_setup(event):
        """
        Delay the setup until Home Assistant is fully initialized.

        This allows any entities to be created already
        """
        hass.data.setdefault(DATA_KEY, [])

        travel_mode = config.get(CONF_MODE)
        traffic_mode = config.get(CONF_TRAFFIC_MODE)

        name = config.get(CONF_NAME, DEFAULT_NAME)
        app_id = config.get(CONF_APP_ID)
        app_code = config.get(CONF_APP_CODE)
        origin = config.get(CONF_ORIGIN)
        destination = config.get(CONF_DESTINATION)

        sensor = HERETravelTimeSensor(
            hass, name, app_id, app_code, origin, destination, travel_mode, traffic_mode
        )
        hass.data[DATA_KEY].append(sensor)

        if sensor.valid_api_connection:
            add_entities_callback([sensor])

    # Wait until start event is sent to load this component.
    hass.bus.listen_once(EVENT_HOMEASSISTANT_START, run_setup)


class HERETravelTimeSensor(Entity):
    import herepy
    """Representation of a HERE travel time sensor."""

    def __init__(
        self,
        hass,
        name,
        app_id,
        app_code,
        origin,
        destination,
        travel_mode,
        traffic_mode,
    ):
        """Initialize the sensor."""
        self._hass = hass
        self._name = name
        self._travel_mode = travel_mode
        self._traffic_mode = traffic_mode
        self._unit_of_measurement = "min"
        self._response = None
        self.valid_api_connection = True

        # Check if location is a trackable entity
        if origin.split(".", 1)[0] in TRACKABLE_DOMAINS:
            self._origin_entity_id = origin
        else:
            self._origin = origin

        if destination.split(".", 1)[0] in TRACKABLE_DOMAINS:
            self._destination_entity_id = destination
        else:
            self._destination = destination

        self._client = herepy.RoutingApi("app_id", "app_code")
        try:
            self.update()
        except herepy.error.HEREError as err:
            _LOGGER.error(err)
            self.valid_api_connection = False
            return

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._response is None:
            return None

        _summary = self._response.response["route"][0]["summary"]
        return round(_summary["baseTime"] / 60)

    @property
    def name(self):
        """Get the name of the sensor."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        if self._response is None:
            return None

        _summary = self._response.response["route"][0]["summary"]
        _route = self._response.response["route"]

        res = {}
        res["distance"] = _summary["distance"]
        res["origin_name"] = _route[0]["waypoint"][0]["mappedRoadName"]
        res["destination_name"] = _route[0]["waypoint"][1]["mappedRoadName"]
        res[CONF_MODE] = self._travel_mode
        res[CONF_TRAFFIC_MODE] = self._traffic_mode
        return res

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self._unit_of_measurement

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from HERE."""

        # Convert device_trackers to HERE friendly location
        if hasattr(self, "_origin_entity_id"):
            self._origin = self._get_location_from_entity(self._origin_entity_id)

        if hasattr(self, "_destination_entity_id"):
            self._destination = self._get_location_from_entity(
                self._destination_entity_id
            )

        self._destination = self._resolve_zone(self._destination)
        self._origin = self._resolve_zone(self._origin)

        self._destination = self._get_location_as_herepy_location(self._destination)
        self._origin = self._get_location_as_herepy_location(self._origin)

        if self._traffic_mode:
            traffic_mode = TRAFFIC_MODE_ENABLED
        else:
            traffic_mode = TRAFFIC_MODE_DISABLED

        if self._destination is not None and self._origin is not None:
            response = self._client.car_route(
                self._origin,
                self._destination,
                [self._travel_mode, herepy.RouteMode.fastest, traffic_mode],
            )
            self._response = response

    def _get_location_from_entity(self, entity_id):
        """Get the location from the entity state or attributes."""
        entity = self._hass.states.get(entity_id)

        if entity is None:
            _LOGGER.error("Unable to find entity %s", entity_id)
            self.valid_api_connection = False
            return None

        # Check if the entity has location attributes
        if location.has_location(entity):
            return self._get_location_from_attributes(entity)

        # Check if device is in a zone
        zone_entity = self._hass.states.get("zone.%s" % entity.state)
        if location.has_location(zone_entity):
            _LOGGER.debug(
                "%s is in %s, getting zone location", entity_id, zone_entity.entity_id
            )
            return self._get_location_from_attributes(zone_entity)

        # If zone was not found in state then use the state as the location
        if entity_id.startswith("sensor."):
            return entity.state

        # When everything fails just return nothing
        return None

    @staticmethod
    def _get_location_from_attributes(entity):
        """Get the lat/long string from an entities attributes."""
        attr = entity.attributes
        return "%s,%s" % (attr.get(ATTR_LATITUDE), attr.get(ATTR_LONGITUDE))

    @staticmethod
    def _get_location_as_herepy_location(location):
        """Get the lat/long array from a comma-separated string"""
        return location.split(",")

    def _resolve_zone(self, friendly_name):
        entities = self._hass.states.all()
        for entity in entities:
            if entity.domain == "zone" and entity.name == friendly_name:
                return self._get_location_from_attributes(entity)

        return friendly_name
