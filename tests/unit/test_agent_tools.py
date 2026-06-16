"""Unit tests for the agent_tools module (device agent tools)."""

import pytest

from src.evaluations.offline.pipeline_multi_agent_evaluation.agent_inference.agent_tools import (
    get_ac_status, get_dishwasher_status, get_tv_status, set_ac_mode,
    set_ac_temperature, set_dishwasher_delay, set_tv_channel, set_tv_volume,
    start_dishwasher, stop_dishwasher, turn_ac_off, turn_ac_on, turn_tv_off,
    turn_tv_on)

# ---------------------------------------------------------------------------
# AC Tools
# ---------------------------------------------------------------------------

class TestACTools:
    def test_set_temperature_valid(self):
        """Valid temperature should succeed."""
        result = set_ac_temperature(temperature=72)
        assert "72" in result
        assert "set to" in result.lower() or "72°F" in result

    def test_set_temperature_too_low(self):
        """Temperature below range should return error."""
        result = set_ac_temperature(temperature=50)
        assert "error" in result.lower() or "out of range" in result.lower()

    def test_set_temperature_too_high(self):
        """Temperature above range should return error."""
        result = set_ac_temperature(temperature=90)
        assert "error" in result.lower() or "out of range" in result.lower()

    def test_set_temperature_boundary_low(self):
        """60°F should be accepted."""
        result = set_ac_temperature(temperature=60)
        assert "60" in result

    def test_set_temperature_boundary_high(self):
        """85°F should be accepted."""
        result = set_ac_temperature(temperature=85)
        assert "85" in result

    def test_turn_ac_on(self):
        """Should confirm AC turned on."""
        result = turn_ac_on()
        assert "on" in result.lower()

    def test_turn_ac_off(self):
        """Should confirm AC turned off."""
        result = turn_ac_off()
        assert "off" in result.lower()

    def test_set_ac_mode_valid(self):
        """Valid modes should succeed."""
        for mode in ["cool", "heat", "fan", "auto"]:
            result = set_ac_mode(mode=mode)
            assert mode in result.lower()

    def test_set_ac_mode_invalid(self):
        """Invalid mode should return error."""
        result = set_ac_mode(mode="turbo")
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_get_ac_status(self):
        """Should return a status string."""
        result = get_ac_status()
        assert isinstance(result, str)
        assert "AC" in result or "ac" in result.lower()


# ---------------------------------------------------------------------------
# TV Tools
# ---------------------------------------------------------------------------

class TestTVTools:
    def test_turn_tv_on(self):
        """Should confirm TV turned on."""
        result = turn_tv_on()
        assert "on" in result.lower()

    def test_turn_tv_off(self):
        """Should confirm TV turned off."""
        result = turn_tv_off()
        assert "off" in result.lower()

    def test_set_channel_valid(self):
        """Valid channel should succeed."""
        result = set_tv_channel(channel=42)
        assert "42" in result

    def test_set_channel_too_low(self):
        """Channel 0 should return error."""
        result = set_tv_channel(channel=0)
        assert "error" in result.lower() or "out of range" in result.lower()

    def test_set_channel_too_high(self):
        """Channel 1000 should return error."""
        result = set_tv_channel(channel=1000)
        assert "error" in result.lower() or "out of range" in result.lower()

    def test_set_channel_boundary(self):
        """Channels 1 and 999 should be accepted."""
        assert "1" in set_tv_channel(channel=1)
        assert "999" in set_tv_channel(channel=999)

    def test_set_volume_valid(self):
        """Valid volume should succeed."""
        result = set_tv_volume(volume=50)
        assert "50" in result

    def test_set_volume_too_low(self):
        """Volume -1 should return error."""
        result = set_tv_volume(volume=-1)
        assert "error" in result.lower() or "out of range" in result.lower()

    def test_set_volume_too_high(self):
        """Volume 101 should return error."""
        result = set_tv_volume(volume=101)
        assert "error" in result.lower() or "out of range" in result.lower()

    def test_set_volume_boundaries(self):
        """Volume 0 and 100 should be accepted."""
        assert "0" in set_tv_volume(volume=0)
        assert "100" in set_tv_volume(volume=100)

    def test_get_tv_status(self):
        """Should return a status string."""
        result = get_tv_status()
        assert isinstance(result, str)
        assert "TV" in result or "tv" in result.lower()


# ---------------------------------------------------------------------------
# Dishwasher Tools
# ---------------------------------------------------------------------------

class TestDishwasherTools:
    def test_start_dishwasher(self):
        """Should confirm dishwasher started."""
        result = start_dishwasher()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_stop_dishwasher(self):
        """Should confirm dishwasher stopped."""
        result = stop_dishwasher()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_dishwasher_status(self):
        """Should return a status string."""
        result = get_dishwasher_status()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_set_dishwasher_delay(self):
        """Should confirm delay set."""
        result = set_dishwasher_delay(hours=2)
        assert isinstance(result, str)
        assert len(result) > 0
