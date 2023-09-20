"""Constants for integration_blueprint."""
from logging import Logger, getLogger
from pyfamilysafety.account import OverrideTarget

LOGGER: Logger = getLogger(__package__)

NAME = "Microsoft Family Safety"
DOMAIN = "family_safety"
VERSION = "1.1.0b5"

DEFAULT_OVERRIDE_ENTITIES = [OverrideTarget.MOBILE,
                             OverrideTarget.WINDOWS,
                             OverrideTarget.XBOX,
                             OverrideTarget.ALL_DEVICES]
AGG_TITLE = "Aggregator error occured. "
AGG_HELP = "This is an upstream issue with Microsoft and is usually temporary. "
AGG_FUTURE = "Try reloading the integration in 15 minutes."
AGG_ERROR = f"{AGG_TITLE}{AGG_HELP}{AGG_FUTURE}"
