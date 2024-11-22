"""Define FamilySafety config entry."""

from homeassistant import config_entries

from .coordinator import FamilySafetyCoordinator

type FamilySafetyConfigEntry = config_entries.ConfigEntry[FamilySafetyCoordinator]
