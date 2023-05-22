"""Creating sensors for upcoming events."""


from datetime import datetime, timedelta
import logging


from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity, generate_entity_id

# from homeassistant.components.sensor import CalendarEvent

from .const import CONF_MAX_EVENTS, DOMAIN

_LOGGER = logging.getLogger(__name__)


# async def async_setup_entry(hass, config, add_entities, discovery_info=None):
async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up this integration with config flow."""
    return True


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Sensors"""
    config = config_entry.data
    max_events = config.get(CONF_MAX_EVENTS) - 1

    for orCal in hass.data[DOMAIN]["Calendars"]:
        sensors = []
        await orCal.update()

        Glenn2 = orCal.calendar
        Glenn3 = hass.data[DOMAIN]
        for index, OR_Event in enumerate(orCal.calendar):
            if index < max_events:
                entity_id = generate_entity_id(
                    "sensor.{}",
                    DOMAIN + "_" + str(orCal.orid) + "_" + str(index),
                    hass=hass,
                )
                Glenn3 = OR_Sensor(hass, OR_Event, index, entity_id)
                sensors.append(OR_Sensor(hass, OR_Event, index, entity_id))

        async_add_entities(sensors)


#    sensors = []
#    for eventnumber in range(max_events):
#        sensors.append(ICalSensor(hass, ical_events, DOMAIN + " " + name, eventnumber))

#    async_add_entities(sensors)


# pylint: disable=too-few-public-methods
class OR_Sensor(Entity):
    """

    Represents the Nth upcoming event.
    May have a name like 'sensor.mycalander_event_0' for the first
    upcoming event.
    """

    def __init__(self, hass, OR_Event, index, entity_id):
        """
        Initialize the sensor.

        sensor_name is typically the name of the calendar.
        eventnumber indicates which upcoming event this is, starting at zero
        """
        self._event_number = index
        self._hass = hass
        # self.ical_events = ical_events
        self._entity_id = entity_id
        # self._unique_id = str(OR_Event["orid"]) + "_" + str(index)
        self._event_attributes = {
            "summary": "glenn",
            "description": "moore",
            "location": None,
            "start": OR_Event["start"],
            "end": OR_Event["end"],
            "cleaning": None,
        }
        self._guestname = OR_Event["guestname"]
        self._state = None
        self._is_available = None

    @property
    def entity_id(self):
        """Return the entity_id of the sensor."""
        return self._entity_id

    @property
    def index_no(self):
        """Return the entity_id of the sensor."""
        return self._event_number

    @property
    def name(self):
        """Return the guest name for the Sensor."""
        return self._guestname

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return "mdi:account-filter"

    @property
    def state(self):
        """Return the date of the next event."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the attributes of the event."""
        return self._event_attributes

    @property
    def available(self):
        """Return True if ZoneMinder is available."""
        return self.extra_state_attributes["start"] is not None

    async def async_update(self):
        """Update the sensor."""
        _LOGGER.debug("Running ICalSensor async update for %s", self.name)

        """
        await self.ical_events.update()

        event_list = self.ical_events.calendar
        # _LOGGER.debug(f"Event List: {event_list}")
        if event_list and (self._event_number < len(event_list)):
            val = event_list[self._event_number]
            name = val.get("summary", "Unknown")
            start = val.get("start")

            # _LOGGER.debug(f"Val: {val}")
            _LOGGER.debug(
                "Adding event %s - Start %s - End %s - as event %s to calendar %s",
                val.get("summary", "unknown"),
                val.get("start"),
                val.get("end"),
                str(self._event_number),
                self.name,
            )

            self._event_attributes["summary"] = val.get("summary", "unknown")
            self._event_attributes["start"] = val.get("start")
            self._event_attributes["end"] = val.get("end")
            self._event_attributes["location"] = val.get("location", "")
            self._event_attributes["description"] = val.get("description", "")
            self._event_attributes["eta"] = (
                start - datetime.now(start.tzinfo) + timedelta(days=1)
            ).days
            self._event_attributes["all_day"] = val.get("all_day")
            self._state = f"{name} - {start.strftime('%-d %B %Y')}"
            if not val.get("all_day"):
                self._state += f" {start.strftime('%H:%M')}"
            # self._is_available = True
        elif self._event_number >= len(event_list):
            # No further events are found in the calendar
            self._event_attributes = {
                "summary": None,
                "description": None,
                "location": None,
                "start": None,
                "end": None,
                "eta": None,
            }
            self._state = None
            self._is_available = None """
