"""Unit tests for the Liquid Pump equipment backend module.
This module validates pump thermodynamic constraints, liquid phase requirements,
isentropic efficiency bounds, pressure rise rules, and Second Law compliance.
"""
import sys
import os
import pytest
from stream import Stream
from equipments.pump.backend import Pump

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_pump_normal_operation():
    """ Test normal operational behavior of the pump with a valid liquid inlet."""
    inlet= Stream(name= "inlet", fluid= "Water", m_dot=2.0)
    inlet.update_by_PT(P=100000.0, T= 300.0)

    pump= Pump(name="Test_Pump", eta_s=0.85)
    outlet= pump.run(inlet_stream= inlet, P_out=5000000.0)

    assert outlet is not None
    assert outlet.P == 5000000.0
    assert outlet.x == -1.0
    assert pump.W_dot > 0.0

def test_vapor_inlet_raises_error():
    """Test that introducing a vapor or two-phase inlet stream raises a ValueError."""
    inlet= Stream(name= "vapor_in", fluid="Water", m_dot=1.0)
    inlet.update_by_Px(P=100000.0, x= 0.5)

    pump = Pump(name= " Cavitation_Pump", eta_s=1.0)

    with pytest.raises(ValueError, match= "vapor or two-phase region"):
        pump.run(inlet_stream= inlet, P_out= 500000.0)

def test_negative_pressure_rise_raise_error():
    """Test that an outlet pressure lower than inlet pressure raises a ValueError."""
    inlet = Stream(name="inlet", fluid="Water", m_dot=1.0)
    inlet.update_by_PT(P=500000.0, T=300.0)

    pump= Pump(name="Negetive_Work_Pump", eta_s=1.0)

    with pytest.raises(ValueError, match= "Outlet prresure.*is lower than inlet pressure"):
        pump.run(inlet_stream=inlet, P_out=100000.0)

def test_invalid_efficiency_bounds():
    """Test that out-of-bound isentropic efficiencies raise a ValueError."""
    with pytest.raises(ValueError,
                       match="Isentropic efficiency must be strictly between 0 and 1"):
        Pump(name="Bad_Eff_Pump_2", eta_s=1.2)

def test_second_law_violation():
    """Test that violations of the Second Law of Thermodynamics trigger an exception."""
    inlet= Stream(name="inlet", fluid="Water", m_dot=1.0)
    inlet.update_by_PT(P=100000.0, T=300.0)

    pump= Pump(name="Prepetual_Pump", eta_s=1.0)

    fake_outlet = Stream(name="fake_out", fluid="Water")
    fake_outlet.update_by_PT(P=5000000.0, T= 290.0)

    with pytest.raises(ValueError,match="Second Law Violation"):
        pump.run(inlet_stream=inlet, outlet_stream=fake_outlet, P_out= 500000.0)

def test_outlet_phase_change_to_vapor():
    """Test that phase change to vapor at the outlet correctly raises an error."""
    inlet= Stream(name="inlet", fluid="Water", m_dot=1.0)
    inlet.update_by_PT(P=100000.0, T= 370.0)

    pump = Pump(name="Boiling_Pump", eta_s= 0.5)

    fake_outlet= Stream(name="vapor_out", fluid="Water")
    fake_outlet.update_by_Ph(P= 150000.0, h=3000000.0)

    with pytest.raises(ValueError,
                       match="Outlet stream entered the vapor/two-phase region"):
        pump.run(inlet_stream=inlet, outlet_stream=fake_outlet, P_out=1500000.0)
