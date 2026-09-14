"""Unit tests for the industrial condenser backend module.
This module validates thermodynamic calculations, constraints, and error handling.
"""
import sys
import os
import pytest
from stream import Stream
from equipments.condenser.backend import Condenser

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_condenser_normal_operational():
    """Test normal condenser operation with superheated vapor inlet 
    and default effectiveness."""
    inlet= Stream(name="condenser_inlet", fluid="Water")
    inlet.update_by_PT(P=100000.0, T=400.0)
    inlet.m_dot= 1.0
    condenser = Condenser(name="Test_Condenser", effectiveness=0.90)
    outlet= condenser.run(inlet_stream=inlet, P_out=100000.0)
    assert outlet is not None
    assert outlet.P == 100000.0
    assert outlet.h < inlet.h
    assert condenser.Q_dot < 0.0
    assert condenser.W_dot == 0.0

def test_condenser_with_pressure_drop_and_subcooling():
    """Test condenser operation with explicit delta_P and target subcooling."""
    inlet= Stream(name="condenser_inlet", fluid="Water")
    inlet.update_by_PT(P= 200000.0, T= 350.0)
    inlet.m_dot= 2.0

    condenser= Condenser(name="Subcool_Condenser", effectiveness=0.85)
    outlet= condenser.run(inlet_stream=inlet, delta_P=5000.0, target_subcooling=5.0)

    assert outlet is not None
    assert outlet.P == 195000.0
    assert outlet.h < inlet.h
    assert condenser.Q_dot < 0.0

def test_condenser_invalid_effectiveness_raises_error():
    """Test that effectiveness out of industrial range [0.5, 1.0] raises ValueError."""
    with pytest.raises(ValueError, match="out of industrial limits"):
        Condenser(name="Bad_Eff", effectiveness=0.30)

def test_condenser_liquid_inlet_raises_error():
    """Test that introducing a subcooled liquid phase at inlet raises a thermodynamic error."""
    inlet= Stream(name="liquid_in", fluid="Water")
    inlet.update_by_PT(P= 100000.0, T=300.0)
    inlet.m_dot= 1.0

    condenser= Condenser(name="Liquid_Condenser", effectiveness=0.90)

    with pytest.raises(ValueError, match="Condenser inlet cannot be subcooled liquid"):
        condenser.run(inlet_stream=inlet, P_out=100000.0)

def test_condenser_invalid_pressure_drop_raises_error():
    """Test that target outlet pressure higher than inlet pressure raises an error."""
    inlet= Stream(name="condenser_inlet", fluid="Water")
    inlet.update_by_PT(P=100000.0, T=400.0)
    inlet.m_dot= 1.0

    condenser= Condenser(name="Bad_DP_Condenser", effectiveness=0.90)
    with pytest.raises(ValueError, match="cannot be higher than inlet pressure"):
        condenser.run(inlet_stream=inlet, P_out=150000.0)
