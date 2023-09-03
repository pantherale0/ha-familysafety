"""Family Safety data hub"""

import logging
from datetime import timedelta

import async_timeout

from .const import NAME

from homeassistant.core import HomeAssistant
from pyfamilysafety import FamilySafety
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed
)

_LOGGER = logging.getLogger(__name__)

class FamilySafetyCoordinator(DataUpdateCoordinator):
    """Family safety data updater."""

    def __init__(self, hass: HomeAssistant, family_safety: FamilySafety) -> None:
        """Init the coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=NAME,
            update_interval=timedelta(seconds=60)
        )
        self.api: FamilySafety = family_safety

    async def _async_update_data(self):
        """Fetch and update data from the API."""
        try:
            async with async_timeout.timeout(50):
                return await self.api.update()
        except Exception as err:
            raise UpdateFailed from err
