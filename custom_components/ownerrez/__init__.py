"""The OwnerRez Integration integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_TOKEN, CONF_USERNAME, CONF_DELAY_TIME
from .const import CONF_DAYS, CONF_MAX_EVENTS, DEFAULT_URL
from homeassistant.components.calendar import CalendarEvent
from homeassistant.util import Throttle, dt
from datetime import datetime, timedelta, date

from .const import DOMAIN

import logging
import aiohttp
import pytz

_LOGGER = logging.getLogger(__name__)
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=7200)
PLATFORMS: list[Platform] = [Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OwnerRez Integration from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    config = entry.data
    auth = aiohttp.BasicAuth(config.get(CONF_USERNAME), config.get(CONF_API_TOKEN))
    domain_entry = {
        "auth": auth,
        # CONF_DELAY_TIME: config.get(CONF_DELAY_TIME),
        CONF_DAYS: config.get(CONF_DAYS),
        CONF_MAX_EVENTS: config.get(CONF_MAX_EVENTS),
    }

    hass.data[DOMAIN][entry.entry_id] = domain_entry

    jresult = []
    jre2 = []
    api_url = DEFAULT_URL + "/properties"
    async with aiohttp.ClientSession(auth=auth) as session:
        async with session.get(api_url) as resp:
            jresult = await resp.json()

            peter = dict(jresult[0])
            paul = dict(jresult[0])
            jre2.append(peter)
            paul["Key"] = "3f6a144d-298a-40f9-836d-8cdce30ed570"
            paul["Name"] = "Calgary Condo"
            paul["Id"] = 1234
            jre2.append(paul)

            hass.data[DOMAIN]["Calendars"] = []
            CalPointer = hass.data[DOMAIN]["Calendars"]

    for orproperty in jre2:
        CalPointer.append(CalEvents(config, orproperty))
        # hass.data[DOMAIN][orproperty["Key"]] = CalEvents(config, orproperty)
        # glenn7 = hass.data[DOMAIN][orproperty["Key"]]
        # await glenn7.update()
        # glenn8 = glenn7

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class CalEvents:
    """Populate the events for each property"""

    def __init__(self, config, orproperty):
        self.url = DEFAULT_URL
        self.max_events = config.get(CONF_MAX_EVENTS)
        self.days = int(config.get(CONF_DAYS))
        self.tzid = orproperty["TimeZoneId"]
        self.name = orproperty["Name"]
        self.orid = orproperty["Id"]
        self.auth = auth = aiohttp.BasicAuth(
            config.get(CONF_USERNAME), config.get(CONF_API_TOKEN)
        )
        self.calendar = []
        self.event = None

    async def async_get_events(self, start_date, end_date):
        """Get list of upcoming events."""
        _LOGGER.debug("Running ICalEvents async_get_events")
        events = []
        if len(self.calendar) > 0:
            for event in self.calendar:
                _LOGGER.debug(
                    "Checking if event %s has start %s and end %s within in the limit: %s and %s",
                    event["summary"],
                    event["start"],
                    event["end"],
                    start_date,
                    end_date,
                )
                if event["start"] < end_date and event["end"] > start_date:
                    _LOGGER.debug("... and it has")
                    # strongly type class fix
                    events.append(
                        CalendarEvent(event["start"], event["end"], event["summary"])
                    )
                    # events.append(event)
        return events

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update(self):
        """Update list of upcoming events."""
        _LOGGER.debug("Running ICalEvents update for calendar %s", self.name)
        # url_for_bookings = DEFAULT_URL + "/bookings?property_ids=" + self.propertyid
        start_of_events = dt.start_of_local_day() - timedelta(days=60)
        end_of_events = dt.start_of_local_day() + timedelta(days=self.days)
        current_date = dt.now()
        events_start = start_of_events.strftime("%Y-%m-%d")
        events_end = end_of_events.strftime("%Y-%m-%d")
        # current_date_formated = current_date.strftime("%Y-%m-%d")

        date_format = "%Y-%m-%dT%H:%M:%S"
        tz = pytz.timezone(self.tzid)
        glenn5 = self.name
        self.calendar = []

        if glenn5 == "Calgary Condo":
            glenn6 = glenn5
        defurl = "https://api.ownerreservations.com/v2"

        api_url = (
            defurl
            # DEFAULT_URL
            # + "/bookings/calendar?propertyIds/"
            + "/bookings?property_ids="
            + str(self.orid)
            + "&from="
            + events_start
            + "&to="
            + events_end
        )
        jresult = {}
        resp = ""
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    jresult = await resp.json()

                    for bookingrecord in jresult["items"]:
                        if bookingrecord["is_block"] == False:
                            api_url = (
                                "https://api.ownerreservations.com/v2/bookings/"
                                + str(bookingrecord["id"])
                            )
                            async with aiohttp.ClientSession(auth=self.auth) as session:
                                async with session.get(api_url) as resp:
                                    bresult = await resp.json()

                            # nr_datestr = bookingrecord["arrival"].replace(
                            #    "T00:00", "T" + bresult["check_in"]
                            # )
                            nr_datestr = (
                                bookingrecord["arrival"]
                                + "T"
                                + bresult["check_in"]
                                + ":00"
                            )

                            nr_start_dt = datetime.strptime(nr_datestr, date_format)
                            nr_start = tz.localize(nr_start_dt)

                            nr_datestr = (
                                bookingrecord["departure"]
                                + "T"
                                + bresult["check_out"]
                                + ":00"
                            )

                            # nr_datestr = bookingrecord["departure"].replace(
                            #    "T00:00", "T" + bresult["check_out"]
                            # )
                            nr_end_dt = datetime.strptime(nr_datestr, date_format)
                            nr_end = tz.localize(nr_end_dt)

                            api_url = (
                                "https://api.ownerreservations.com/v2/guests/"
                                + str(bookingrecord["guest_id"])
                            )
                            async with aiohttp.ClientSession(auth=self.auth) as session:
                                async with session.get(api_url) as resp:
                                    guest_name = await resp.json()

                            new_record = {
                                "start": nr_start,
                                "end": nr_end,
                                "summary": guest_name["first_name"]
                                + " "
                                + guest_name["last_name"],
                            }
                            self.calendar.append(new_record)
