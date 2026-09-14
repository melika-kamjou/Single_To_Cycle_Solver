"""Unit tests for the industrial mixing chamber backend module.
This module validates adiabatic mixing chamber calculations 
mass and energy conservation, fluid compatibility checks,
and pressure constraints for the MixingChamber component.
"""
import sys
import os
import pytest
from stream import Stream
from equipments.mixer.backend import MixingChamber

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_mixer_normal_operation():
    """Test normal adiabatic mixing operation with default lowest_pressure matching."""
    inlet1= Stream(name="mixer_inlet_1", fluid= "Water")
    inlet1.update_by_PT(P= 300000.0, T= 323.15)
    inlet1.m_dot= 2.0

    inlet2= Stream(name="mixer_inlet_2", fluid="Water")
    inlet2.update_by_PT(P=300000.0, T=343.15)
    inlet2.m_dot=3.0
    mixer= MixingChamber(name="Test_Mixer")
    outlet= mixer.run(inlet_streams=[inlet1, inlet2])

    assert outlet is not None
    assert outlet.m_dot== 5.0
    assert outlet.P == 300000.0
    assert outlet.h > inlet1.h

def test_mixer_custom_outlet_pressure():
    """Test mixing with a valid custom lower outlet pressure."""
    inlet1= Stream(name= "mixer_inlet_1", fluid= "Water")
    inlet1.update_by_PT(P=300000.0, T=323.15)
    inlet1.m_dot= 2.0

    inlet2= Stream(name= "mixer_inlet_2", fluid= "Water")
    inlet2.update_by_PT(P=300000.0, T=343.15)
    inlet2.m_dot= 3.0

    mixer= MixingChamber(name="Test_Mixer")
    outlet= mixer.run(inlet_streams=[inlet1, inlet2], P_out= 280000.0)
    assert outlet is not None
    assert outlet.P == 280000.0

def test_mixer_insufficient_streams_raises_error():
    """Test that providing fewer than 2 inlet streams raises ValueError."""
    inlet1= Stream(name="mixer_inlet_1", fluid= "Water")
    inlet1.m_dot= 2.0

    mixer= MixingChamber(name="Test_Mixer")
    with pytest.raises(ValueError, match="requires at least 2 inlet streams"):
        mixer.run(inlet_streams=[inlet1])

def test_mixer_incompatible_fluids_raises_error():
    """Test that mixing streams with different fluids raises ValueError."""
    inlet1= Stream(name="mixer_inlet_1", fluid="water")
    inlet1.update_by_PT(P=300000.0, T=323.15)
    inlet1.m_dot= 2.0

    inlet2= Stream(name="mixer_inlet_2", fluid="Water")
    inlet2.update_by_PT(P=300000.0, T= 300.15)
    inlet2.m_dot= 3.0

    mixer= MixingChamber(name="Test_Mixer")
    with pytest.raises(ValueError, match="Mixing streams with different fluids"):
        mixer.run(inlet_streams=[inlet1, inlet2])

def test_mixer_high_outlet_pressure_raises_error():
    """Test that setting outlet pressure higher than
    the lowest inlet pressure raises ValueError."""
    inlet1= Stream(name="mixer_inlet_1", fluid="Water")
    inlet1.update_by_PT(P=300000.0, T= 323.15)
    inlet1.m_dot= 2.0

    inlet2= Stream(name="mixer_inlet_2", fluid="Water")
    inlet2.update_by_PT(P= 250000.0, T= 343.15)
    inlet2.m_dot= 3.0

    mixer= MixingChamber(name="Test_Mixer")
    with pytest.raises(ValueError, match="cannot exceed the lowest inlet pressure"):
        mixer.run(inlet_streams=[inlet1, inlet2], P_out= 280000.0)
