# HA-Ventoxx-HRV: Home Assistant Integration for Ventoxx HRV

![Example of card on the Dashboard](/images/Ventoxx_Dashboard.png)

![Example of card on the Dashboard](/images/Ventoxx_integration_slider.png)


A fully local, HACS-compatible custom component for Home Assistant to control Ventoxx Harmony Smart Heat Recovery Ventilation units via Wi-Fi.\## Advanced Setup: Dual-Unit Push-Pull Automation

If you have two Ventoxx units (e.g., Kitchen and Living Room), you can create a master controller to keep them in perfect push/pull synchronization.

\### 1. Template Sensors (configuration.yaml)

Add this to your `configuration.yaml` to track the system status:

```yaml

template:
  - sensor:
      - name: "Ventoxx Living Mode"
        state: >
          {% if is_state('fan.ventoxx_living_room', 'off') %}
            Off
          {% else %}
            {% set preset = state_attr('fan.ventoxx_living_room', 'preset_mode') %}
            {% set pct = state_attr('fan.ventoxx_living_room', 'percentage') | int(0) %}
            {% set dir = state_attr('fan.ventoxx_living_room', 'direction') %}
            {% set dir_str = 'Intake' if dir == 'forward' else 'Exhaust' %}
            
            {% if preset == 'Boost' %} Boost {{ dir_str }}
            {% elif preset == 'Night' %} Night Mode
            {% elif preset == 'Heat Recovery' %}
              {% set speed = 1 if pct <= 33 else (2 if pct <= 66 else 3) %}
              HRV Speed {{ speed }} - {{ dir_str }}
            {% else %}
              {% set speed = 1 if pct <= 33 else (2 if pct <= 66 else 3) %}
              Speed {{ speed }} - {{ dir_str }}
            {% endif %}
          {% endif %}
        icon: >
          {% if is_state('fan.ventoxx_living_room', 'off') %} mdi:fan-off
          {% elif state_attr('fan.ventoxx_living_room', 'preset_mode') == 'Boost' %} mdi:fan-plus
          {% elif state_attr('fan.ventoxx_living_room', 'direction') == 'forward' %} mdi:arrow-down-circle
          {% else %} mdi:arrow-up-circle
          {% endif %}

      - name: "Ventoxx Kitchen Mode"
        state: >
          {% if is_state('fan.ventoxx_kitchen', 'off') %}
            Off
          {% else %}
            {% set preset = state_attr('fan.ventoxx_kitchen', 'preset_mode') %}
            {% set pct = state_attr('fan.ventoxx_kitchen', 'percentage') | int(0) %}
            {% set dir = state_attr('fan.ventoxx_kitchen', 'direction') %}
            {% set dir_str = 'Intake' if dir == 'forward' else 'Exhaust' %}
            
            {% if preset == 'Boost' %} Boost {{ dir_str }}
            {% elif preset == 'Night' %} Night Mode
            {% elif preset == 'Heat Recovery' %}
              {% set speed = 1 if pct <= 33 else (2 if pct <= 66 else 3) %}
              HRV Speed {{ speed }} - {{ dir_str }}
            {% else %}
              {% set speed = 1 if pct <= 33 else (2 if pct <= 66 else 3) %}
              Speed {{ speed }} - {{ dir_str }}
            {% endif %}
          {% endif %}
        icon: >
          {% if is_state('fan.ventoxx_kitchen', 'off') %} mdi:fan-off
          {% elif state_attr('fan.ventoxx_kitchen', 'preset_mode') == 'Boost' %} mdi:fan-plus
          {% elif state_attr('fan.ventoxx_kitchen', 'direction') == 'forward' %} mdi:arrow-down-circle
          {% else %} mdi:arrow-up-circle
          {% endif %}
```


\### 2. Master Scripts (scripts.yaml)

Add these to your `scripts.yaml` to control both fans simultaneously:

```yaml

ventoxx_hrv1_mode:
  alias: "Heat Recovery Ventilation - Speed 1 - START"
  sequence:
    - parallel:
        # Living: HRV, Intake (Forward), Speed 1 (33%)
        - service: fan.turn_on
          target: { entity_id: fan.ventoxx_living_room }
          data: { preset_mode: "Heat Recovery", percentage: 33 }
        - service: fan.set_direction
          target: { entity_id: fan.ventoxx_living_room }
          data: { direction: "forward" }
        # Kitchen: HRV, Exhaust (Reverse), Speed 1 (33%)
        - service: fan.turn_on
          target: { entity_id: fan.ventoxx_kitchen }
          data: { preset_mode: "Heat Recovery", percentage: 33 }
        - service: fan.set_direction
          target: { entity_id: fan.ventoxx_kitchen }
          data: { direction: "reverse" }

ventoxx_hrv2_mode:
  alias: "Heat Recovery Ventilation - Speed 2 - START"
  sequence:
    - parallel:
        - service: fan.turn_on
          target: { entity_id: fan.ventoxx_living_room }
          data: { preset_mode: "Heat Recovery", percentage: 66 }
        - service: fan.set_direction
          target: { entity_id: fan.ventoxx_living_room }
          data: { direction: "forward" }
        - service: fan.turn_on
          target: { entity_id: fan.ventoxx_kitchen }
          data: { preset_mode: "Heat Recovery", percentage: 66 }
        - service: fan.set_direction
          target: { entity_id: fan.ventoxx_kitchen }
          data: { direction: "reverse" }

ventoxx_hrv3_mode:
  alias: "Heat Recovery Ventilation - Speed 3 - START"
  sequence:
    - parallel:
        - service: fan.turn_on
          target: { entity_id: fan.ventoxx_living_room }
          data: { preset_mode: "Heat Recovery", percentage: 100 }
        - service: fan.set_direction
          target: { entity_id: fan.ventoxx_living_room }
          data: { direction: "forward" }
        - service: fan.turn_on
          target: { entity_id: fan.ventoxx_kitchen }
          data: { preset_mode: "Heat Recovery", percentage: 100 }
        - service: fan.set_direction
          target: { entity_id: fan.ventoxx_kitchen }
          data: { direction: "reverse" }

ventoxx_cooking_mode:
  alias: "Kitchen Cooking - Exhaust - START"
  sequence:
    - parallel:
        # Living: Normal, Intake (Forward), Speed 3 (100%)
        - service: fan.turn_on
          target: { entity_id: fan.ventoxx_living_room }
          data: { preset_mode: "Normal", percentage: 100 }
        - service: fan.set_direction
          target: { entity_id: fan.ventoxx_living_room }
          data: { direction: "forward" }
        # Kitchen: Normal, Exhaust (Reverse), Speed 2 (66%)
        - service: fan.turn_on
          target: { entity_id: fan.ventoxx_kitchen }
          data: { preset_mode: "Normal", percentage: 66 }
        - service: fan.set_direction
          target: { entity_id: fan.ventoxx_kitchen }
          data: { direction: "reverse" }

ventoxx_cooking_boost_mode:
  alias: "Kitchen Cooking - Exhaust BOOST - START"
  sequence:
    - parallel:
        # Living: Boost Preset, Intake (Forward)
        - service: fan.turn_on
          target: { entity_id: fan.ventoxx_living_room }
          data: { preset_mode: "Boost" }
        - service: fan.set_direction
          target: { entity_id: fan.ventoxx_living_room }
          data: { direction: "forward" }
        # Kitchen: Normal, Exhaust (Reverse), Speed 3 (100%)
        - service: fan.turn_on
          target: { entity_id: fan.ventoxx_kitchen }
          data: { preset_mode: "Normal", percentage: 100 }
        - service: fan.set_direction
          target: { entity_id: fan.ventoxx_kitchen }
          data: { direction: "reverse" }

ventoxx_stop:
  alias: "Both Ventoxx Units - STOP"
  sequence:
    - service: fan.turn_off
      target:
        entity_id:
          - fan.ventoxx_living_room
          - fan.ventoxx_kitchen
```


\### 3. Dashboard Card

Add a Manual Card to your dashboard and paste this YAML:

```yaml

type: vertical-stack
cards:
  - type: entities
    title: Ventoxx Master Control
    entities:
      - entity: sensor.ventoxx_living_mode
        name: Living Room Status
      - entity: sensor.ventoxx_kitchen_mode
        name: Kitchen Status
    show_header_toggle: false
    state_color: true

  - type: horizontal-stack
    cards:
      - type: button
        name: HRV Speed 1
        show_name: false
        icon: mdi:fan-speed-1
        tap_action:
          action: call-service
          service: script.ventoxx_hrv1_mode
        icon_height: 50px
      - type: button
        name: HRV Speed 2
        show_name: false
        icon: mdi:fan-speed-2
        tap_action:
          action: call-service
          service: script.ventoxx_hrv2_mode
        icon_height: 50px
      - type: button
        name: HRV Speed 3
        show_name: false
        icon: mdi:fan-speed-3
        tap_action:
          action: call-service
          service: script.ventoxx_hrv3_mode
        icon_height: 50px

  - type: horizontal-stack
    cards:
      - type: button
        name: Cooking Exhaust
        show_name: false
        icon: mdi:pot-steam-outline
        tap_action:
          action: call-service
          service: script.ventoxx_cooking_mode
        icon_height: 50px
      - type: button
        name: Cooking Boost
        show_name: false
        icon: mdi:pot-steam
        tap_action:
          action: call-service
          service: script.ventoxx_cooking_boost_mode
        icon_height: 50px
      - type: button
        name: Stop All
        show_name: false
        icon: mdi:stop-circle-outline
        tap_action:
          action: call-service
          service: script.ventoxx_stop
        icon_height: 50px
```

