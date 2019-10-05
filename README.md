# here_travel_time

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![License][license-shield]](LICENSE.md)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Community Forum][forum-shield]][forum]

_Homeassistant Custom Component sensor provides travel time from the [HERE Routing API](https://developer.here.com/documentation/routing/topics/introduction.html)._

**This component will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Show travel time between two places.

![example][exampleimg]

## Installation

### Important information for hass.io users on > 0.96.0

If you are using hass.io in a version later than 0.96.0 you have to restart twice in order for this component to work.

This is a known problem for some custom_components and will hopefully be fixed soon

### HACS

The easiest way to add this to your Homeassistant installation is using [HACS](https://custom-components.github.io/hacs/) and add this repository as a custom repository. And then follow the instructions under [Configuration](#configuration) below.

### Manual

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `here_travel_time`.
4. Download _all_ the files from the `custom_components/here_travel_time/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Follow the instructions under [Configuration](#configuration) below.

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/here_travel_time/__init__.py
custom_components/here_travel_time/manifest.json
custom_components/here_travel_time/sensor.py
```

## Setup

You need to register for an API key by following the instructions [here](https://developer.here.com/documentation/routing/topics/introduction.html?create=Freemium-Basic&keepState=true&step=account).

HERE offers a Freemium Plan which includes 250.000 free Transactions per month. For the Routing API, one transaction equals one request with one starting point (no multistop). More information can be found [here](https://developer.here.com/faqs#payment-subscription)

By default HERE will deactivate your account if you exceed the free Transaction limit for the month. You can add payment details to reenable your account as described [here](https://developer.here.com/faqs)

##  Configuration 

To enable the sensor, add the following lines to your `configuration.yaml` file:

```yaml
# Example entry for configuration.yaml
sensor:
  - platform: here_travel_time
    app_id: "YOUR_APP_ID"
    app_code: "YOUR_APP_CODE"
    origin_latitude: "51.222975"
    origin_longitude: "9.267577"
    destination_latitude: "51.257430"
    destination_longitude: "9.335892"
```

## Configuration options

Key | Type | Required | Description
-- | -- | -- | --
`app_id` | `string` | `true` | Your application's API id (get one by following the instructions above).
`app_code` | `string` | `true` | Your application's API code (get one by following the instructions above).
`origin_latitude` | `string` | `true` | The starting latitude for calculating travel distance and time. Must be used in combination with origin_longitude. Cannot be used in combination with origin_entity_id
`origin_longitude` | `string` | `true` | The starting longitude for calculating travel distance and time. Must be used in combination with origin_latitude. Cannot be used in combination with origin_entity_id
`destination_latitude` | `string` | `true` | The finishing latitude for calculating travel distance and time. Must be used in combination with destination_longitude. Cannot be used in combination with destination_entity_id
`destination_longitude` | `string` | `true` | The finishing longitude for calculating travel distance and time. Must be used in combination with destination_latitude. Cannot be used in combination with destination_entity_id
`origin_entity_id` | `string` | `true` | The entity_id holding the starting point for calculating travel distance and time. Cannot be used in combination with origin_latitude / origin_longitude
`destination_entity_id` | `string` | `true` | The entity_id holding the finishing point for calculating travel distance and time. Cannot be used in combination with destination_latitude / destination_longitude
`name` | `string` | `false` | A name to display on the sensor. The default is "HERE Travel Time".
`mode` | `string` | `false` | You can choose between: `bicycle`, `car`, `pedestrian`, `publicTransport`, `publicTransportTimeTable` or `truck`. The default is `car`. For public transport publicTransportTimetable is recommended. You can find more information on the modes [here](https://developer.here.com/documentation/routing/topics/transport-modes.html) and on the public modes [here](https://developer.here.com/documentation/routing/topics/public-transport-routing.html)
`route_mode` | `string` | `false` | You can choose between: `fastest`, or `shortest`. This will determine whether the route is optimized to be the shortest and completely disregard traffic and speed limits or the fastest route according to the current traffic information. The default is `fastest`
`traffic_mode` | `string` | `false` | You can choose between: `true`, or `false`. Decide whether you want to take the current traffic condition into account. Default is `false`.
`unit_system` | `string` | `false` | You can choose between `metric` or `imperial`. Defaults to `metric` or `imperial` based on the Home Assistant configuration.
`scan_interval` | `integer` | `false` | "Defines the update interval of the sensor in seconds. Defaults to 300 (5 minutes)."


## Dynamic Configuration 

If an entity is placed in the `origin_entity_id` or `destination_entity_id` then every 5 minutes when the platform updates it will use the latest location of that entity.


```yaml
# Example entry for configuration.yaml
sensor:
  # Tracking entity to entity
  - platform: here_travel_time
    app_id: "YOUR_APP_ID"
    app_code: "YOUR_APP_CODE"
    name: Phone To Home
    origin_entity_id: device_tracker.mobile_phone
    destination_entity_id: zone.home
```

## Entity Tracking 

- **device_tracker**
  - If the state is a zone, then the zone location will be used
  - If the state is not a zone, it will look for the longitude and latitude attributes
- **zone**
  - Uses the longitude and latitude attributes
- **other**
  - Will try to recursively resolve the state if it is an entity id until it finds coordinates

##  Updating sensors on-demand using Automation 

You can also use the `homeassistant.update_entity` service to update the sensor on-demand. For example, if you want to update `sensor.morning_commute` every 2 minutes on weekday mornings, you can use the following automation:

```yaml
automation:
- id: update_morning_commute_sensor
  alias: "Commute - Update morning commute sensor"
  initial_state: 'on'
  trigger:
    - platform: time_pattern
      minutes: '/2'
  condition:
    - condition: time
      after: '08:00:00'
      before: '11:00:00'
    - condition: time
      weekday:
        - mon
        - tue
        - wed
        - thu
        - fri
  action:
    - service: homeassistant.update_entity
      entity_id: sensor.morning_commute
```

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

<a href="https://www.buymeacoffee.com/eifinger" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/black_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a><br>

***

[buymecoffee]: https://www.buymeacoffee.com/eifinger
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/custom-components/blueprint.svg?style=for-the-badge
[commits]: https://github.com/eifinger/here_travel_time/commits/master
[customupdater]: https://github.com/custom-components/custom_updater
[customupdaterbadge]: https://img.shields.io/badge/custom__updater-true-success.svg?style=for-the-badge
[exampleimg]: https://github.com/eifinger/here_travel_time/blob/master/example.PNG?raw=true
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/t/custom-component-here-travel-time/125908
[license-shield]: https://img.shields.io/github/license/eifinger/here_travel_time.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Kevin%20Eifinger%20%40eifinger-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/eifinger/here_travel_time.svg?style=for-the-badge
[releases]: https://github.com/eifinger/here_travel_time/releases