"""Unit tests for the industrial evaporator backend module.
This module validates thermodynamic calculations, constraints, and error handling.
"""
import sys
import os
import pytest
from stream import Stream
from equipments.evaporator.backend import Evaporator

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_evaporator_normal_operational():
    """Test normal evaporator operation with liquid inlet and default effectiveness."""
    inlet= Stream(name="evaporator_inlet", fluid="Water")
    inlet.update_by_PT(P=100000.0, T= 300.0)
    inlet.m_dot= 1.0
    evaporator= Evaporator(name= "Test_Evaporator", effectiveness=0.90)
    outlet= evaporator.run(inlet_stream=inlet, P_out= 100000, target_superheat=5.0)

    assert outlet is not None
    assert outlet.P==100000.0
    assert outlet.h > inlet.h
    assert evaporator.Q_dot > 0.0
    assert evaporator.W_dot == 0.0

def test_evaporator_with_pressure_drop_and_superheat():
    """Test evaporator operation with explicit delta_P and target superheat."""
    inlet=Stream(name="evaporator_inlet", fluid="Water")
    inlet.update_by_PT(P=200000.0, T=320.0)
    inlet.m_dot= 2.0

    evaporator= Evaporator(name="Superheat_Evaporator", effectiveness=0.85)
    outlet= evaporator.run(inlet_stream=inlet, delta_P=5000.0, target_superheat=10.0)

    assert outlet is not None
    assert outlet.P==195000.0
    assert outlet.h > inlet.h
    assert evaporator.Q_dot > 0.0

def test_evaporator_invalid_effectiveness_raises_error():
    """Test that effectiveness out of industrial range [0.5, 1.0] raises ValueError."""
    with pytest.raises(ValueError, match="out of industrial limits"):
        Evaporator(name="Bad_Eff", effectiveness=0.30)

def test_evaporator_superheated_inlet_raises_error():
    """Test that yntroducing a superheated vapor phase at inlet raises a thermodynamic error."""
    inlet= Stream(name="vapor_in", fluid="Water")
    inlet.update_by_PT(P=100000.0, T=400.0)
    inlet.m_dot= 1.0

    evaporator= Evaporator(name="Vapor_Evaporator", effectiveness=0.90)

    with pytest.raises(ValueError, match="Evaporator inlet cannot be superheated vapor"):
        evaporator.run(inlet_stream=inlet, P_out=100000.0)

def test_evaporator_invalid_pressure_drop_raises_error():
    """Test that target outlet pressure higher than inlet pressure raises an error."""
    inlet= Stream(name="evaporator_inlet", fluid= "Water")
    inlet.update_by_PT(P=100000.0, T=300.0)
    inlet.m_dot= 1.0

    evaporator= Evaporator(name="Bad_DP_Evaporator", effectiveness=0.90)
    with pytest.raises(ValueError, match="cannot be higher than inlet pressure"):
        evaporator.run(inlet_stream=inlet, P_out=150000.0)
