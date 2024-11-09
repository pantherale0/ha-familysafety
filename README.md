# Microsoft Family Safety

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]

_Integration to integrate with [ha-familysafety][ha-familysafety]._

**IMPORTANT: Do not use `configuration.yaml` to configure this integration as it is not supported**

**This integration will set up the following platforms.**

| Platform | Description                                                                                            |
| -------- | ------------------------------------------------------------------------------------------------------ |
| Sensor   | Screen time specified as a duration sensor measured in minutes for overall account and/or applications |
| Sensor | Number of pending requests for a given account |
| Switch   | Block access to platforms |

**This integration will register the following services.**

| Service     | Description                                 |
| ----------- | ------------------------------------------- |
| Block App   | Blocks a specified application from running |
| Unblock App | Allow a specified application to run        |
| Approve Request* | Approves a pending request |
| Deny Request* | Denies a pending request |

## Service Help

1. The target entity that you use should be the used screen time sensor that is registered for the account you wish to block an application for.
1. Application names must be exactly as seen in the extra state attributes for the used screen time sensor, for example:
   - For "LEGO® CITY UNDERCOVER: 0"
   - Use "LEGO® CITY UNDERCOVER" (without quotes)

### Pending Requests

As of 2024.12.0b0, support for pending requests has been added. Each time pending requests are retrieved (so everytime a request is approved/denied or on each update interval) this GUID of the specific request will change, therefore if used in automations, you should retrieve the GUID for use in the service calls by filtering the `requests` attribute found under the `Pending Requests` sensor.

If you would like to try, enable experimental features in the options flow (after initial configuration). This is found in the `Configure collected accounts` menu.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `family_safety`.
1. Download _all_ the files from the `custom_components/family_safety/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Microsoft Family Safety"

**IMPORTANT:** Make sure you do the following steps after starting the config flow as the response token can expire very quickly

1. First authorize a session by navigating to the following URL:
   [https://login.live.com/oauth20_authorize.srf?cobrandid=b5d15d4b-695a-4cd5-93c6-13f551b310df&client_id=000000000004893A&response_type=code&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf&response_mode=query&scope=service%3A%3Afamilymobile.microsoft.com%3A%3AMBI_SSL&lw=1&fl=easi2&login_hint=](https://login.live.com/oauth20_authorize.srf?cobrandid=b5d15d4b-695a-4cd5-93c6-13f551b310df&client_id=000000000004893A&response_type=code&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf&response_mode=query&scope=service%3A%3Afamilymobile.microsoft.com%3A%3AMBI_SSL&lw=1&fl=easi2&login_hint=)
1. Once logged in you should be taken to a blank page copy the full URL in the address bar (including `https`)
1. Paste the copied URL into the `OAuth response URL` field in the Home Assistant UI.

## Configuration is done in the UI

From the configuration menu:

- Additional entities can be configured to create switches to unlblock or block specific applications and also register screen time sensors

  1.  Select "Configure application entities"
  1.  Select required applications from list and press "Submit"

- You can control what accounts are collected
  1.  Select "Configure collected accounts"
  1.  A list of available accounts to control will appear, check the box next to the name of the account you would like entities for.
      **NOTE:** By default no options are selected and therefore all accounts will be collected

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[ha-familysafety]: https://github.com/pantherale0/ha-familysafety
[commits-shield]: https://img.shields.io/github/commit-activity/y/pantherale0/ha-familysafety.svg?style=for-the-badge
[commits]: https://github.com/pantherale0/ha-familysafety/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-green.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/pantherale0/ha-familysafety.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/pantherale0/ha-familysafety.svg?style=for-the-badge
[releases]: https://github.com/pantherale0/ha-familysafety/releases
