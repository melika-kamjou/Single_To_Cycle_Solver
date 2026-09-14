"""Unit tests for the industrial heat exchanger backend module.
This module validates thermodynamic calculations, energy balances, 
effectiveness models, and error handling for the HeatExchanger component.
"""
# pylint: disable= invalid-name
import sys
import os
import pytest
from stream import Stream
from equipments.heat_exchanger.backend import HeatExchanger
current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_hx_normal_operation():
    """Test normal heat exchanger operation with valid hot and cold streams."""
    hot_in= Stream(name="hot_in", fluid= "Water")
    hot_in.update_by_PT(P=400000.0, T= 363.15)
    hot_in.m_dot= 3.0

    cold_in= Stream(name="cold_in", fluid="Water")
    cold_in.update_by_PT(P=300000.0, T= 293.15)
    cold_in.m_dot= 5.0

    hx= HeatExchanger(name="Test_HX", effectiveness=0.80)
    hot_out, cold_out= hx.run(hot_inlet=hot_in, cold_inlet=cold_in)

    assert hot_out is not None
    assert cold_out is not None
    assert hot_out.h < hot_in.h
    assert cold_out.h > cold_in.h
    assert hx.Q_dot > 0.0

def test_hx_invalid_effectiveness_raises_error():
    """Test that effectiveness out of limits [0.1, 1.0] raises ValueError."""
    with pytest.raises(ValueError, match="Heat exchanger effectiveness must be between"):
        HeatExchanger(name="Bad_HX", effectiveness= 1.20)

def test_hx_invalid_temperature_raises_error():
    """Test that hot inlet temperature lower than or equal to 
    cold inlet temperature raises ValueError."""
    hot_in= Stream(name="hot_in", fluid="Water")
    hot_in.update_by_PT(P=400000.0, T= 283.15)
    hot_in.m_dot= 3.0

    cold_in= Stream(name="cold_in", fluid="Water")
    cold_in.update_by_PT(P=300000.0, T=293.15)
    cold_in.m_dot=5.0

    hx= HeatExchanger(name="Test_HX")
    with pytest.raises(ValueError, match="Hot inlet temperature must be"
                       " higher than cold inlet temperature"):
        hx.run(hot_inlet=hot_in, cold_inlet= cold_in)
