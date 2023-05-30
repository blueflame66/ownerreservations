"""The OwnerRez Integration integration2."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_TOKEN, CONF_USERNAME, CONF_DELAY_TIME
from .const import CONF_DAYS, CONF_MAX_EVENTS, DEFAULT_URL, DEFAULT_URL_V2
from homeassistant.components.calendar import CalendarEvent
from homeassistant.util import Throttle, dt
from datetime import datetime, timedelta, date

from .const import DOMAIN

import logging
import aiohttp
import pytz

_LOGGER = logging.getLogger(__name__)
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=7200)
# PLATFORMS: list[Platform] = [Platform.CALENDAR]
PLATFORMS = ["sensor", "calendar"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OwnerRez Integration from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    config = entry.data
    auth = aiohttp.BasicAuth(config.get(CONF_USERNAME), config.get(CONF_API_TOKEN))
    domain_entry = {
        "auth": auth,
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
            await session.close()

            peter = dict(jresult[0])
            paul = dict(jresult[0])
            jre2.append(peter)
            paul["Key"] = "3f6a144d-298a-40f9-836d-8cdce30ed570"
            paul["Name"] = "Calgary Condo"
            paul["Id"] = 1234
            jre2.append(paul)

            hass.data[DOMAIN]["Calendars"] = []
            hass.data[DOMAIN]["Properties"] = []
            CalPointer = hass.data[DOMAIN]["Calendars"]
            CalPointer2 = hass.data[DOMAIN]["Properties"]
            CalPointer3 = hass.data[DOMAIN]

    for orproperty in jre2:
        CalPointer.append(CalEvents(config, orproperty))
        CalPointer2.append(OR_Property(orproperty, config, auth))

    for orprop in hass.data[DOMAIN]["Properties"]:
        await orprop.retrieve_bookings()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class OR_Property:
    """Property Object from OR"""

    def __init__(self, prop, config, auth) -> None:
        self._key = prop["Key"]
        self._id = prop["Id"]
        self._name = prop["Name"]
        self._tzid = prop["TimeZoneId"]
        self._auth = auth
        self.days = int(config.get(CONF_DAYS))
        self.bookings = []

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def retrieve_bookings(self) -> None:
        """Get the Bookings for the Property"""
        self.bookings = []

        start_of_events = dt.start_of_local_day() - timedelta(days=60)
        end_of_events = dt.start_of_local_day() + timedelta(days=self.days)
        current_date = dt.now()
        events_start = start_of_events.strftime("%Y-%m-%d")
        events_end = end_of_events.strftime("%Y-%m-%d")
        date_format = "%Y-%m-%dT%H:%M:%S"
        tz = pytz.timezone(self._tzid)

        api_url = (
            DEFAULT_URL_V2
            + "/bookings?property_ids="
            + str(self.id)
            + "&from="
            + events_start
            + "&to="
            + events_end
        )

        async with aiohttp.ClientSession(auth=self._auth) as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    jresult = await resp.json()

                    for bookingrecord in jresult["items"]:
                        if bookingrecord["is_block"] == False:
                            api_url = (
                                DEFAULT_URL_V2 + "/bookings/" + str(bookingrecord["id"])
                            )

                            async with session.get(api_url) as resp:
                                bresult = await resp.json()

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

                            nr_end_dt = datetime.strptime(nr_datestr, date_format)
                            nr_end = tz.localize(nr_end_dt)

                            api_url = (
                                DEFAULT_URL_V2
                                + "/guests/"
                                + str(bookingrecord["guest_id"])
                            )

                            async with session.get(api_url) as resp:
                                guest_name = await resp.json()

                                booking_record = {
                                    "start": nr_start,
                                    "end": nr_end,
                                    "summary": guest_name["first_name"]
                                    + " "
                                    + guest_name["last_name"]
                                    + " TZ:"
                                    + tz.zone,
                                    "guestname": guest_name["first_name"]
                                    + " "
                                    + guest_name["last_name"],
                                    "orid": self.id,
                                }

                                self.bookings.append(Booking(booking_record))

        await session.close()

    @property
    def key(self):
        """Return the next upcoming event."""
        return self._key

    @property
    def id(self):
        """Return the next upcoming event."""
        return self._id

    @property
    def name(self):
        """Return the next upcoming event."""
        return self._name


class Booking:
    """Object to Represent a booking"""

    def __init__(self, booking_id) -> None:
        self._booking_id = booking_id
        self._guest_name = "Test"
        self._arrival = None
        self._departure = None
        self._cleaning = None


class CalEvents:
    """Populate the events for each property"""

    def __init__(self, config, orproperty):
        self.url = DEFAULT_URL
        self.max_events = config.get(CONF_MAX_EVENTS)
        self.days = int(config.get(CONF_DAYS))
        self.tzid = orproperty["TimeZoneId"]
        self.name = orproperty["Name"]
        self.orid = orproperty["Id"]
        self.auth = aiohttp.BasicAuth(
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

                            async with session.get(api_url) as resp:
                                guest_name = await resp.json()

                            new_record = {
                                "start": nr_start,
                                "end": nr_end,
                                "summary": guest_name["first_name"]
                                + " "
                                + guest_name["last_name"]
                                + " TZ:"
                                + tz.zone,
                                "guestname": guest_name["first_name"]
                                + " "
                                + guest_name["last_name"],
                                "orid": self.orid,
                            }
                            self.calendar.append(new_record)
        await session.close()

class OR_UpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching update data from single endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: OmniLogic,
        name: str,
        config_entry: ConfigEntry,
        polling_interval: int,
    ) -> None:
        """Initialize the global Omnilogic data updater."""
        self.api = api
        self.config_entry = config_entry
        self._last_data = None
        self._timeout_count = 0

        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=name,
            update_interval=timedelta(seconds=polling_interval),
        )

    async def _async_update_data(self):
    """Fetch data from Owner Res."""
    try:
        async with async_timeout.timeout(30):
            data = await self.api.get_telemetry_data()

        self._timeout_count = 0

    except OmniLogicException as error:
        raise UpdateFailed(f"Error updating from OmniLogic: {error}") from error

    except LoginException as error:
        raise UpdateFailed(f"Login failed for Omnilogic: {error}") from error

    except TimeoutError as error:
        self._timeout_count += 1

        if self._timeout_count > 10 or not self._last_data:
            raise UpdateFailed(f"Timeout updating OmniLogic from cloud: {error}") from error
        else:
            data = self._last_data

    parsed_data = {}
    self._last_data = data