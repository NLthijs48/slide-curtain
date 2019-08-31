"""Support for Go Slide slides."""

import logging

from homeassistant.util import slugify
from homeassistant.components.cover import (
    ATTR_POSITION,
    ENTITY_ID_FORMAT,
    STATE_OPEN,
    STATE_CLOSED,
    STATE_OPENING,
    STATE_CLOSING,
    DEVICE_CLASS_CURTAIN,
    CoverDevice,
)
from .const import API, DOMAIN, SLIDES

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up cover(s) for Go Slide platform."""

    if discovery_info is None:
        return

    entities = []

    for slide in hass.data[DOMAIN][SLIDES].values():
        _LOGGER.debug("Setting up Slide entity: %s", slide)
        entities.append(SlideCover(hass.data[DOMAIN][API], slide))

    async_add_entities(entities)


class SlideCover(CoverDevice):
    """Representation of a Go Slide cover."""

    def __init__(self, api, slide):
        """Initialize the cover."""
        self._api = api
        self._slide = slide
        self._id = slide["id"]
        self._name = slide["name"]
        self._entity_id = ENTITY_ID_FORMAT.format(slugify("slide_" + slide["mac"]))

    @property
    def entity_id(self):
        """Return the entity id of the cover."""
        return self._entity_id

    @property
    def name(self):
        """Return the name of the cover."""
        return self._name

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        return self._slide["state"] == STATE_OPENING

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        return self._slide["state"] == STATE_CLOSING

    @property
    def is_closed(self):
        """Return None if status is unknown, True if closed, else False."""
        if self._slide["state"] is None:
            return None
        return self._slide["state"] == STATE_CLOSED

    @property
    def assumed_state(self):
        """Let HA know the integration is assumed state."""
        return True

    @property
    def device_class(self):
        """Return the device class of the cover."""
        return DEVICE_CLASS_CURTAIN

    @property
    def current_cover_position(self):
        """Return the current position of cover shutter."""
        if self._slide["pos"] is None:
            pos = None
        else:
            pos = int(self._slide["pos"] * 100)

        return pos

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        self._slide["state"] = STATE_OPENING
        await self._api.slideopen(self._id)

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        self._slide["state"] = STATE_CLOSING
        await self._api.slideclose(self._id)

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self._api.slidestop(self._id)

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs[ATTR_POSITION] / 100

        if self._slide["pos"] is not None:
            if position > self._slide["pos"]:
                self._slide["state"] = STATE_CLOSING
            else:
                self._slide["state"] = STATE_OPENING

        await self._api.slidesetposition(self._id, position)