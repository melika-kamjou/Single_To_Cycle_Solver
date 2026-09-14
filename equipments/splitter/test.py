"""Unit tests for the Stream Splitter equipment backend module.
Validates mass/energy balance, split ratios constraints, and exception handling.
"""
import sys
import os
import pytest
from stream import Stream
from equipments.splitter.backend import Splitter

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_splitter_normal_operation():
    """Test normal stream splitter operation with
    valid split ratios summing to 1.0."""
    inlet= Stream(name="splitter_inlet", fluid="Water")
    inlet.update_by_PT(P=300000.0, T=333.15)
    inlet.m_dot = 5.0

    splitter= Splitter(name="Test_Splitter")
    outlets= splitter.run(inlet_stream=inlet, split_ratios=[0.4, 0.6])

    assert outlets is not None
    assert len(outlets) == 2
    assert outlets[0].m_dot == 2.0
    assert outlets[1].m_dot== 3.0
    assert outlets[0].P == 300000.0
    assert  outlets[1].P == 300000.0

def test_splitter_invalid_ratios_sum_raises_error():
    """Test that split ratios not summing to 1.0 raises ValueError."""
    inlet= Stream(name="splitter_inlet", fluid="Water")
    inlet.update_by_PT(P= 300000.0, T=333.15)
    inlet.m_dot= 5.0

    splitter= Splitter(name="Test_Splitter")
    with pytest.raises(ValueError, match="Split ratios must sum up to 1.0"):
        splitter.run(inlet_stream= inlet, split_ratios=[0.3, 0.4])

def test_splitter_insufficient_ratios_raises_error():
    """Test that providing fewer than 2 split ratios raises ValueError."""
    inlet= Stream(name="splitter_inlet", fluid= "Water")
    inlet.update_by_PT(P= 300000.0, T=333.15)
    inlet.m_dot= 5.0

    splitter= Splitter(name="Test_Splitter")
    with pytest.raises(ValueError,
                       match="requires at least 2 outlet split fractions"):
        splitter.run(inlet_stream= inlet, split_ratios= [1.0])
