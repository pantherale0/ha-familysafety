"""Diagnostics support for Reolink."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .config_entry import FamilySafetyConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: FamilySafetyConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = config_entry.runtime_data
    diagnostic_data = {
        "accounts": [],
        "pending_requests": data.api.pending_requests
    }
    accounts = data.api.accounts
    for acc in accounts:
        acc_data = {
            "id": acc.user_id,
            "role": acc.role,
            "devices": [],
            "applications": [],
            "today_screentime_usage": acc.today_screentime_usage,
            "average_screentime_usage": acc.average_screentime_usage,
            "screentime_usage": acc.screentime_usage,
            "blocked_platforms": [str(x) for x in acc.blocked_platforms],
            "experimental": acc.experimental,
            "acc_balance": acc.account_balance,
            "acc_currency": acc.account_currency
        }
        for dev in acc.devices:
            acc_data["devices"].append({
                "id": dev.device_id,
                "class": dev.device_class,
                "make": dev.device_make,
                "model": dev.device_model,
                "form_factor": dev.form_factor,
                "os_name": dev.os_name,
                "today_screentime_used": dev.today_time_used,
                "issues": dev.issues,
                "states": dev.states,
                "last_seen": dev.last_seen,
                "blocked": dev.blocked
            })
        for app in acc.applications:
            acc_data["applications"].append({
                "id": app.app_id,
                "name": app.name,
                "icon": app.icon,
                "policy": app.policy,
                "blocked": app.blocked
            })
        diagnostic_data["accounts"].append(acc_data)

    return diagnostic_data
