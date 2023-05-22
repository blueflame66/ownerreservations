"""Support for iCal-URLs."""

import copy
import logging

# import aiohttp
# import pytz

# from .const import DEFAULT_URL
from homeassistant.util import dt
from datetime import datetime, timedelta, date

from .const import CONF_DAYS, CONF_MAX_EVENTS


from homeassistant.components.calendar import (
    ENTITY_ID_FORMAT,
    CalendarEntity,
    CalendarEvent,
    extract_offset,
    get_date,
    is_offset_reached,
)
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.components.calendar import CalendarEvent

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the OwnerRez Calendar platform."""
    config = config_entry.data
    _LOGGER.debug("Running setup_platform for calendar")
    _LOGGER.debug(f"Conf: {config}")

    config_info = hass.data[DOMAIN][config_entry.entry_id]
    moore = hass.data[DOMAIN]

    for orCal in hass.data[DOMAIN]["Calendars"]:
        await orCal.update()
        # glenn = orCal.name
        entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, DOMAIN + "_" + str(orCal.orid), hass=hass
        )

        calendar = ORCalendar(entity_id, orCal)

        async_add_entities([calendar], True)


class ORCalendar(CalendarEntity):
    """OR Calendar Entry"""

    def __init__(self, entity_id, cal_events):
        """Create the iCal Calendar Event Device."""
        self.entity_id = entity_id
        self._event = None
        self._name = cal_events.name
        self._offset_reached = False
        self._prop_id = cal_events.orid
        self._prop_tz = cal_events.tzid
        self._maxdays = cal_events.days
        self._maxevents = cal_events.max_events
        self.cal_events = cal_events

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        return {"offset_reached": self._offset_reached}

    @property
    def event(self):
        """Return the next upcoming event."""
        return self._event

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    async def async_get_events(self, hass, start_date, end_date):
        """Get all events in a specific time frame."""
        _LOGGER.debug("Running ICalCalendarEventDevice async get events")
        return await self.cal_events.async_get_events(start_date, end_date)
        # return await get_or_events(
        #    self._prop_id, self._prop_tz, self._maxdays, self._maxevents, self._auth
        # )

    async def async_update(self):
        """Update the Calendar"""
        _LOGGER.debug("Running ICalCalendarEventDevice async update for %s", self.name)
        await self.cal_events.update()
        event = copy.deepcopy(self.cal_events.event)
        if event is None:
            self._event = event
            return
        (summary, offset) = extract_offset(event["summary"], OFFSET)
        event["summary"] = summary
        self._offset_reached = is_offset_reached(event["start"], offset)
        self._event = CalendarEvent(event["start"], event["end"], event["summary"])
        # strongly typed class required.
        # self._event = copy.deepcopy(event)
        # self._event["start"] = {}
        # self._event["end"] = {}
        # self._event["start"]["dateTime"] = event["start"].isoformat()
        # self._event["end"]["dateTime"] = event["end"].isoformat()
        # self._event["all_day"] = event["all_day"]
