"""Family Safety data hub"""

import logging
from datetime import timedelta

import async_timeout

from homeassistant.core import HomeAssistant
from pyfamilysafety import FamilySafety
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed
)

from .const import NAME

_LOGGER = logging.getLogger(__name__)

class FamilySafetyCoordinator(DataUpdateCoordinator):
    """Family safety data updater."""

    def __init__(self,
                 hass: HomeAssistant,
                 family_safety: FamilySafety,
                 update_interval: int=60) -> None:
        """Init the coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=NAME,
            update_interval=timedelta(seconds=update_interval)
        )
        self.api: FamilySafety = family_safety

    async def _async_update_data(self):
        """Fetch and update data from the API."""
        try:
            async with async_timeout.timeout(50):
                return await self.api.update()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API {err}") from err
