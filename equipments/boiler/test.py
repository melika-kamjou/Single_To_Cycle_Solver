"""Unit tests for the industrial boiler equipment backend module."""
# pylint: disable=invalid-name, too-many-locals, too-many-branches, too-many-statements, broad-exception-caught, raise-missing-from. too-many-arguments
import sys
import os
import pytest
from stream import Stream
from equipments.boiler.backend import Boiler

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def test_boiler_normal_operation():
    """Test normal boiler operation with liquid feedwater and valid effectiveness."""
    inlet= Stream(name="boiler_inlet", fluid= "Water")
    inlet.update_by_PT(P=5000000.0, T=373.15)
    inlet.m_dot= 5.0

    boiler= Boiler("Test_Boiler", effectiveness= 0.90)
    outlet= boiler.run(inlet_stream=inlet,P_out= 4900000.0, target_superheat= 50.0)

    assert outlet is not None
    assert outlet.P == 4900000.0
    assert outlet.h > inlet.h
    assert boiler.Q_dot > 0.0

def test_boiler_invalid_effectiveness_raises_error():
    """Test that effectiveness out of industrial limits [0.5, 1.0] raises ValueError."""
    with pytest.raises(ValueError, match="is out of industrial limits"):
        Boiler(name="Bad_Effectiveness_Boiler", effectiveness=0.30)

def test_boiler_superheated_feedwater_raises_error():
    """Test that supplying superheated vapor as boiler feedwater raises ValueError."""
    inlet=Stream(name="superheated_inlet",  fluid= "Water")
    inlet.update_by_PT(P= 100000.0, T= 400.0)
    inlet.m_dot= 1.0

    boiler= Boiler(name="Test_Boiler", effectiveness= 0.90)
    with pytest.raises(ValueError, match="Boiler feedwater must be liquid"):
        boiler.run(inlet_stream=inlet,P_out= 100000.0, target_superheat=20.0)

def test_boiler_invalid_outlet_pressure_raises_error():
    """Test that outlet pressure higher than inlet pressure raises ValueError."""
    inlet= Stream(name= "boiler_inlet", fluid= "Water")
    inlet.update_by_PT(P= 2000000.0, T= 350.0)
    inlet.m_dot= 1.0

    boiler= Boiler(name="Test_Boiler", effectiveness= 0.90)
    with pytest.raises(ValueError, match="cannot be higher than inlet pressure"):
        boiler.run(inlet_stream=inlet,P_out= 2500000, target_superheat=20.0)
