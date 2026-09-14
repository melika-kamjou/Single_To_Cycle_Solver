"""Unit tests for the Throtlling Valve equipment backend model.
Validates isenthalpic processes, pressure drop rules, and negative pressure rise errors."""
import sys
import os
import pytest
from stream import Stream
from equipments.valve.backend import Valve

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_valve_normal_operation_p_out():
    """Test normal valveoperation specifying target 
    outlet pressure (isenthalpic process)."""
    inlet= Stream(name= "valve_inlet", fluid="Water")
    inlet.update_by_PT(P=2000000.0, T=400.0)
    h_in= inlet.h

    valve= Valve(name="Test_Valve", valve_type="Expansion Valve")
    outlet= valve.run(inlet_stream=inlet, P_out=500000.0)

    assert outlet is not None
    assert outlet.P == 500000.0
    assert abs(outlet.h - h_in) < 1e-3

def test_valve_normal_operation_delta_p():
    """Test normal valve operation specifying pressure drop delta_P."""
    inlet= Stream(name="valve_inlet", fluid="Water")
    inlet.update_by_PT(P=2000000.0, T=400.0)

    valve= Valve(name="Test_Valve_DP", valve_type="Control Valve")
    outlet= valve.run(inlet_stream= inlet, delta_P=1500000.0)

    assert outlet is not None
    assert outlet.P == 500000.0
    assert abs(outlet.h - inlet.h) < 1e-3

def test_valve_invalid_pressure_increas_raises_error():
    """Test that soecifying an outlet pressure higher than inlet pressure 
    raises a ValueError due to passive valve constraints."""
    inlet= Stream(name="valve_inlet", fluid="Water")
    inlet.update_by_PT(P=500000.0, T= 400.0)

    valve= Valve(name="Bad_Valve")
     # Matchesthe exact wording in the backend code check
    with pytest.raises(ValueError, match="cannot be higher than inlet pressure"):
        valve.run(inlet_stream=inlet, P_out=1000000.0)
