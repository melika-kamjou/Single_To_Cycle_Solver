"""Unit tests for the industrial flash tank backend module.
This module validates flash separation calculations, mass conservation, and error handling.
"""
import sys
import os
import pytest
from stream import Stream
from equipments.flashtank.backend import FlashTank
current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_flash_tank_normal_operation():
    """Test normal flash tank operation with mass conservation and two distinct outlets."""
    inlet= Stream(name="flash_inlet", fluid= "Water")
    inlet.update_by_PT(P=3000000.0, T=473.15)
    inlet.m_dot= 4.0

    flash= FlashTank(name= "Test_Flash")
    res= flash.run(inlet_stream=inlet, P_flash= 1500000.0)

    assert res is not None
    assert res["vapor_outlet"] is not None
    assert res["liquid_outlet"] is not None
    assert abs((res["vapor_outlet"].m_dot + res["liquid_outlet"].m_dot) - inlet.m_dot) < 1e-5

def test_flash_tank_invalid_pressure_raises_error():
    """Test that flash pressure higher than or equal to inlet pressure raises ValueError."""
    inlet= Stream(name="flash_inlet", fluid="Water")
    inlet.update_by_PT(P= 2000000.0, T= 400.0)
    inlet.m_dot= 2.0

    flash= FlashTank(name="Test_Flash")
    with pytest.raises(ValueError, match="must be strictly lower than inlet stream pressure."):
        flash.run(inlet_stream=inlet, P_flash= 2500000.0)
