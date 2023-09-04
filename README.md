# Microsoft Family Safety

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]

_Integration to integrate with [family_safety][family_safety]._

**IMPORTANT: Do not use `configuration.yaml` to configure this integration as it is not supported**

**This integration will set up the following platforms.**

| Platform | Description |
| -------- | ----------- |

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `family_safety`.
1. Download _all_ the files from the `custom_components/family_safety/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Integration blueprint"

## Configuration is done in the UI

**IMPORTANT:** Make sure you do the following steps after starting the config flow as the response token can expire very quickly

1. First authorize a session by navigating to the following URL:
   [login.live.com](https://login.live.com/oauth20_authorize.srf?cobrandid=b5d15d4b-695a-4cd5-93c6-13f551b310df&client_id=dce5010f-c52d-4353-ae86-d666373528d8&response_type=code&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf&response_mode=query&scope=service%3A%3Afamilymobile.microsoft.com%3A%3AMBI_SSL&lw=1&fl=easi2&login_hint=)
1. Once logged in you should be taken to a blank page copy the full URL in the address bar (including `https`)
1. Paste the copied URL into the `OAuth response URL` field in the Home Assistant UI.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/pantherale0/ha-familysafety.svg?style=for-the-badge
[commits]: https://github.com/pantherale0/ha-familysafety/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/pantherale0/ha-familysafety.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/pantherale0/ha-familysafety.svg?style=for-the-badge
[releases]: https://github.com/pantherale0/ha-familysafety/releases
