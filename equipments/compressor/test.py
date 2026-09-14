"""Unit tests for the industrial gas compressor backend module.
This module validates thermodynamic calculations, constraint enforcement (Such as
preventing liquid slugging, negative pressure drops, and invalid isentropic efficiencies),
and Second Law compliance for the Compressor class.
"""
import sys
import os

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
#pylint: disable=wrong-import-position
import pytest
from stream import Stream
from equipments.compressor.backend import Compressor

def test_compressor_narmal_opeartion():
    """ Test normal operation of compressor with superheated vapor inlet."""
    inlet= Stream(name= "inlet", fluid="Water")
    inlet.update_by_PT(P= 100000.0, T= 450.0)
    compressor= Compressor(name="Test_Compressor", eta_s=0.85)
    outlet= compressor.run(inlet_stream=inlet, P_out= 500000.0)

    assert outlet is not None
    assert outlet.P == 500000.0
    assert compressor.W_dot > 0.0

def test_liquid_inlet_raises_error():
    """ Test that introducing liquid phase at the inlet raises a thermodynamic error."""
    inlet= Stream(name="liquid_in", fluid= "Water")
    inlet.update_by_PT(P= 100000.0, T=300.0)
    compressor= Compressor(name="Liquid_Compressor", eta_s=1.0)

    with pytest.raises(ValueError, match="liquid phase"):
        compressor.run(inlet_stream=inlet, P_out= 500000.0)

def test_negative_pressure_rise_raise_error():
    """Test that outlet pressure lower than inlet pressure raises an error."""
    inlet= Stream(name="inlet", fluid= "Water")
    inlet.update_by_PT(P= 500000.0, T= 450.0)
    compressor= Compressor(name="Neggative_Work_Compressor", eta_s=1.0)

    with pytest.raises(ValueError, match="Outlet pressure.*is lower than inlet pressure"):
        compressor.run(inlet_stream= inlet, P_out= 100000.0)

def test_invalid_efficiency_bounds():
    """Test that invalid isentropic efficiencies raise a ValueError."""
    with pytest.raises(ValueError, match=
                       "Isentropic efficiency must be stricrly between 0 and 1."):
        Compressor(name="Badd_Eff_Compressor", eta_s=1.2)

def test_second_law_violation():
    """Test that an outlet enthalpy lower than the isentropic enthalpy at 100%
    efficiency triggers a Second Law error."""
    inlet= Stream(name="inlet", fluid= "Water", m_dot=1.0)
    inlet.update_by_PT(P=100000.0, T= 450.0)
    compressor= Compressor(name="Perpetual_Compressor", eta_s=1.0)

    #Fake outlet withe unrealistically low enthalpy/temperature (violates 2nd law)
    fake_outlet = Stream(name="fake_out", fluid="Water")
    fake_outlet.update_by_PT(P=500000.0, T=350.0)

    with pytest.raises(ValueError, match="Second Law violation"):
        compressor.run(inlet_stream=inlet, outlet_stream= fake_outlet, P_out=500000.0)
