import math
import logging
from typing import Any

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PRESET_NORMAL = "Normal"
PRESET_HEAT_RECOVERY = "Heat Recovery"
PRESET_BOOST = "Boost"
PRESET_NIGHT = "Night"

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Ventoxx fan platform from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([VentoxxFan(coordinator)])

class VentoxxFan(CoordinatorEntity, FanEntity):
    """Representation of a Ventoxx HRV unit as a Fan."""

    def __init__(self, coordinator):
        """Initialize the fan."""
        super().__init__(coordinator)
        self._attr_name = coordinator.config_entry.data["name"]
        self._attr_unique_id = f"{coordinator.config_entry.data['host']}_fan"
        
        self._attr_supported_features = (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.DIRECTION
            | FanEntityFeature.PRESET_MODE
        )
        self._attr_preset_modes = [PRESET_NORMAL, PRESET_HEAT_RECOVERY, PRESET_BOOST, PRESET_NIGHT]

    @property
    def speed_count(self) -> int:
        """Return the number of speeds (Speed 1, 2, 3)."""
        return 3

    @property
    def _fstate(self) -> int:
        """Helper to get current fstate from coordinator data."""
        return int(self.coordinator.data.get("fstate", 0))

    @property
    def is_on(self) -> bool:
        """Return true if the entity is on."""
        return self._fstate > 0

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        if not self.is_on:
            return 0
            
        speed_val = self._fstate & 7 
        if speed_val == 6:
            return 100
        if speed_val in (1, 2, 3):
            return int((speed_val / self.speed_count) * 100)
        return 0

    @property
    def current_direction(self) -> str:
        """Return the fan direction (Forward=Intake, Reverse=Exhaust)."""
        return DIRECTION_REVERSE if (self._fstate & 8) else DIRECTION_FORWARD

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        if not self.is_on:
            return None
            
        # Detect Night Mode natively based on display/buzzer status
        buzzst = int(self.coordinator.data.get("buzzst", 1))
        dispst = int(self.coordinator.data.get("dispst", 1))
        if buzzst == 0 and dispst == 0:
            return PRESET_NIGHT
            
        if (self._fstate & 7) == 6:
            return PRESET_BOOST
            
        return PRESET_HEAT_RECOVERY if (self._fstate & 16) else PRESET_NORMAL

    def _calculate_fstate(self, is_on: bool, percentage: int, direction: str, preset: str) -> int:
        """Calculate the target fstate bitmask."""
        if not is_on or percentage == 0:
            return 0

        target_fstate = 0
        if direction == DIRECTION_REVERSE:
            target_fstate |= 8

        if preset == PRESET_BOOST:
            target_fstate |= 6
        else:
            speed_step = math.ceil(percentage / (100 / self.speed_count))
            speed_step = max(1, min(3, speed_step))
            target_fstate |= speed_step

            # Night mode defaults to HRV under the hood
            if preset in (PRESET_HEAT_RECOVERY, PRESET_NIGHT):
                target_fstate |= 16

        return target_fstate

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode, handling Night Mode payload routing."""
        if preset_mode == PRESET_NIGHT:
            fstate = self._calculate_fstate(True, 33, self.current_direction, PRESET_HEAT_RECOVERY)
            await self.coordinator.api.set_full_state(fstate, 0, 0)
            
            # Optimistic update
            self.coordinator.data["fstate"] = fstate
            self.coordinator.data["buzzst"] = 0
            self.coordinator.data["dispst"] = 0
        else:
            pct = self.percentage if self.percentage > 0 else 50
            fstate = self._calculate_fstate(True, pct, self.current_direction, preset_mode)
            await self.coordinator.api.set_full_state(fstate, 1, 1)
            
            self.coordinator.data["fstate"] = fstate
            self.coordinator.data["buzzst"] = 1
            self.coordinator.data["dispst"] = 1

        self.async_write_ha_state()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan."""
        if percentage == 0:
            await self.async_turn_off()
            return

        preset = PRESET_NORMAL if self.preset_mode in (PRESET_BOOST, PRESET_NIGHT) else (self.preset_mode or PRESET_NORMAL)
        fstate = self._calculate_fstate(True, percentage, self.current_direction, preset)
        await self._send_standard_fstate(fstate)

    async def async_set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        pct = self.percentage if self.percentage > 0 else 50
        preset = self.preset_mode or PRESET_NORMAL
        fstate = self._calculate_fstate(True, pct, direction, preset)
        
        if preset == PRESET_NIGHT:
            await self.coordinator.api.set_full_state(fstate, 0, 0)
            self.coordinator.data["fstate"] = fstate
            self.async_write_ha_state()
        else:
            await self._send_standard_fstate(fstate)

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs) -> None:
        """Turn on the fan."""
        pct = percentage if percentage is not None else (self.percentage if self.percentage > 0 else 50)
        preset = preset_mode if preset_mode is not None else (self.preset_mode or PRESET_HEAT_RECOVERY)
        
        fstate = self._calculate_fstate(True, pct, self.current_direction, preset)
        
        if preset == PRESET_NIGHT:
            await self.coordinator.api.set_full_state(fstate, 0, 0)
            self.coordinator.data["fstate"] = fstate
            self.coordinator.data["buzzst"] = 0
            self.coordinator.data["dispst"] = 0
        else:
            await self.coordinator.api.set_full_state(fstate, 1, 1)
            self.coordinator.data["fstate"] = fstate
            self.coordinator.data["buzzst"] = 1
            self.coordinator.data["dispst"] = 1
            
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        await self._send_standard_fstate(0)

    async def _send_standard_fstate(self, fstate: int) -> None:
        """Send state and restore buzzer/display to normal."""
        await self.coordinator.api.set_full_state(fstate, 1, 1)
        self.coordinator.data["fstate"] = fstate
        self.coordinator.data["buzzst"] = 1
        self.coordinator.data["dispst"] = 1
        self.async_write_ha_state()