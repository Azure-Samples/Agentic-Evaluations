"""Tool functions for the device agents in the Multi-Agent system."""

from random import choice, randint
from typing import Annotated

from agent_framework import tool
from pydantic import Field


# =============================================================================
# AC AGENT TOOLS
# =============================================================================
# NOTE: approval_mode="never_require" is for sample brevity.
# Use "always_require" in production.
@tool(approval_mode="never_require")
def set_ac_temperature(
    temperature: Annotated[int, Field(description="The target temperature in degrees Fahrenheit (60-85).")],
) -> str:
    """Set the air conditioner to a specific temperature."""
    if temperature < 60 or temperature > 85:
        return f"Error: Temperature {temperature}°F is out of range. Please set between 60°F and 85°F."
    return f"AC temperature set to {temperature}°F."


@tool(approval_mode="never_require")
def turn_ac_on() -> str:
    """Turn the air conditioner on."""
    return "AC has been turned on."


@tool(approval_mode="never_require")
def turn_ac_off() -> str:
    """Turn the air conditioner off."""
    return "AC has been turned off."


@tool(approval_mode="never_require")
def set_ac_mode(
    mode: Annotated[str, Field(description="The AC mode to set: 'cool', 'heat', 'fan', or 'auto'.")],
) -> str:
    """Set the air conditioner operating mode."""
    valid_modes = ["cool", "heat", "fan", "auto"]
    if mode.lower() not in valid_modes:
        return f"Error: Invalid mode '{mode}'. Valid modes are: {', '.join(valid_modes)}."
    return f"AC mode set to {mode.lower()}."


@tool(approval_mode="never_require")
def get_ac_status() -> str:
    """Get the current status of the air conditioner."""
    modes = ["cool", "heat", "fan", "auto"]
    status = choice(["on", "off"])
    temp = randint(60, 85)
    mode = choice(modes)
    return f"AC is {status}, set to {temp}°F in {mode} mode."


# =============================================================================
# TV AGENT TOOLS
# =============================================================================
@tool(approval_mode="never_require")
def turn_tv_on() -> str:
    """Turn the television on."""
    return "TV has been turned on."


@tool(approval_mode="never_require")
def turn_tv_off() -> str:
    """Turn the television off."""
    return "TV has been turned off."


@tool(approval_mode="never_require")
def set_tv_channel(
    channel: Annotated[int, Field(description="The channel number to switch to (1-999).")],
) -> str:
    """Switch the television to a specific channel."""
    if channel < 1 or channel > 999:
        return f"Error: Channel {channel} is out of range. Please set between 1 and 999."
    return f"TV channel set to {channel}."


@tool(approval_mode="never_require")
def set_tv_volume(
    volume: Annotated[int, Field(description="The volume level to set (0-100).")],
) -> str:
    """Set the television volume."""
    if volume < 0 or volume > 100:
        return f"Error: Volume {volume} is out of range. Please set between 0 and 100."
    return f"TV volume set to {volume}."


@tool(approval_mode="never_require")
def get_tv_status() -> str:
    """Get the current status of the television."""
    status = choice(["on", "off"])
    channel = randint(1, 200)
    volume = randint(0, 100)
    return f"TV is {status}, channel {channel}, volume {volume}."


# =============================================================================
# DISHWASHER AGENT TOOLS
# =============================================================================
@tool(approval_mode="never_require")
def start_dishwasher(
    cycle: Annotated[str, Field(description="The wash cycle to use: 'normal', 'heavy', 'quick', or 'rinse'.")] = "normal",
) -> str:
    """Start the dishwasher with a specified cycle."""
    valid_cycles = ["normal", "heavy", "quick", "rinse"]
    if cycle.lower() not in valid_cycles:
        return f"Error: Invalid cycle '{cycle}'. Valid cycles are: {', '.join(valid_cycles)}."
    return f"Dishwasher started on {cycle.lower()} cycle."


@tool(approval_mode="never_require")
def stop_dishwasher() -> str:
    """Stop the dishwasher."""
    return "Dishwasher has been stopped."


@tool(approval_mode="never_require")
def get_dishwasher_status() -> str:
    """Get the current status of the dishwasher."""
    statuses = ["idle", "washing", "drying", "complete"]
    cycles = ["normal", "heavy", "quick", "rinse"]
    status = choice(statuses)
    cycle = choice(cycles)
    remaining = randint(0, 90)
    if status == "idle":
        return "Dishwasher is idle."
    elif status == "complete":
        return "Dishwasher cycle is complete."
    else:
        return f"Dishwasher is {status} on {cycle} cycle, {remaining} minutes remaining."


@tool(approval_mode="never_require")
def set_dishwasher_delay(
    hours: Annotated[int, Field(description="Number of hours to delay the start (1-24).")],
) -> str:
    """Set a delayed start for the dishwasher."""
    if hours < 1 or hours > 24:
        return f"Error: Delay {hours} hours is out of range. Please set between 1 and 24 hours."
    return f"Dishwasher delayed start set for {hours} hour(s) from now."
