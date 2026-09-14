""" Unit tests for the industrial combustion chamber backend module.
This module validates the thermodynamic calculatios, mass and energy balances,
fuel combustion performence, and expection handling (such as invalid efficiencies
and pressure constraints) for CombustionChamber class.
"""
import sys
import os
import pytest
from stream import Stream
from equipments.combustion_chamber.backend import CombustionChamber

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_combustion_normal_operation():
    """Test normal combustion chamber operation with valid fuel input and efficiency."""
    inlet= Stream(name="air_inlet", fluid="Water")
    inlet.update_by_PT(P= 300000.0, T=298.15)
    inlet.m_dot= 5.0
    chamber= CombustionChamber(name="Test_Combustor", combustion_efficiency=0.95)
    outlet= chamber.run(inlet_streams=[inlet], fuel_mass_flow=0.1, fuel_lhv= 50000.0)

    assert outlet is not None
    assert outlet.m_dot == 5.1
    assert outlet.h > inlet.h
    assert chamber.Q_dot > 0.0

def test_combustion_invalid_efficiency_raises_error():
    """Test that combustion efficiency outside [0.5, 1.0] raises ValueError."""
    with pytest.raises(ValueError, match="Combustion efficiency must be between"):
        CombustionChamber(name="Bad_eff_Combustor", combustion_efficiency=0.40)
def test_combustion_high_outlet_pressure_raises_error():
    """Test that setting outlet pressure higher than inlet pressure raises ValueError."""
    inlet= Stream(name="air_inlet", fluid="Water")
    inlet.update_by_PT(P=300000.0, T=298.15)
    inlet.m_dot= 5.0
    chamber= CombustionChamber(name="Test_Combustor")
    with pytest.raises(ValueError, match="cannot exceed the lowest inlet pressure"):
        chamber.run(inlet_streams=[inlet], fuel_mass_flow= 0.1, fuel_lhv=50000.0, P_out=320000.0)
