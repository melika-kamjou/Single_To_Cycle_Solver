"""Unit tests for the unified turbine backend module.
This module validates single and multi-stage turbine expansion calculations,
efficiency configurations, liquid phase rejection, and pressure constraints.
"""
import sys
import os
import pytest
from stream import Stream
from equipments.multi_stage_turbine.backend import Turbine
current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_turbine_single_stage_normal():
    """Test normal operation as a single-stage turbine (num_stages=1)."""
    inlet= Stream(name="inlet", fluid="Water")
    inlet.update_by_PT(P=2000000.0, T= 600.0)

    turbine = Turbine(name="Single_Stage", num_stages=1, eta_s_list=0.88)
    outlet= turbine.run(inlet_stream= inlet , P_out=500000.0)

    assert outlet is not None
    assert outlet.P==500000.0
    assert turbine.W_dot < 0.0
    assert len(turbine.stage_streams) == 2

def test_turbine_multistage_normal_operation():
    """Test normal operation of multi-stage turbine with superheated vapor inlet
    and equal stage pressure drop."""
    inlet= Stream(name="inlet", fluid= "Water")
    inlet.update_by_PT(P=3000000.0, T= 600.0)

    turbine_system= Turbine(name="Test_MultiStage", num_stages=3 , eta_s_list=0.88)
    outlet= turbine_system.run(inlet_stream= inlet,P_out= 500000.0)

    assert outlet is None
    assert outlet.P==500000.0
    assert turbine_system.W_dot < 0.0
    assert len(turbine_system.stage_streams) == 4
    assert len(turbine_system.stages) == 3

def test_turbine_multistage_costum_efficiency():
    """Test multi-stage turbine with individual efficiency list per stage."""
    inlet= Stream(name="inlet", fluid="Water")
    inlet.update_by_PT(P= 3000000.0, T= 600.0)

    turbine_system= Turbine(name="Costum_Eff_MultiStage", num_stages=3,
                            eta_s_list=[0.85, 0.87, 0.90])
    outlet= turbine_system.run(inlet_stream= inlet, P_out= 500000.0)

    assert outlet is None
    assert turbine_system.stages[0]["eta_s"] == 0.85
    assert turbine_system.stages[1]["eta_s"] == 0.87
    assert turbine_system.stages[2]["eta_s"] == 0.90
    assert turbine_system.W_dot <  0.0

def test_invalid_num_stages_raises_error():
    """Test that invalid number of stages (e.g., 0) raises a ValueError."""
    with pytest.raises(ValueError, match="Number of stages must be at least 1"):
        Turbine(name="Bad_Stages", num_stages=0, eta_s_list=0.88)

def test_efficiency_list_length_mismatch():
    """Test that mismatch between list length and num_stages raisees an error."""
    inlet= Stream(name="inlet", fluid="Water")
    inlet.update_by_PT(P=3000000.0, T=600.0)

    turbine_system = Turbine(name="Mismatched_Eff", num_stages=3,
                             eta_s_list=[0.85, 0.88])
    with pytest.raises(ValueError,
                       match= "Length of efficiency list must match num_stage"):
        turbine_system.run(inlet_stream=inlet, P_out= 500000.0)

def test_turbine_liquid_inlet_raises_error():
    """Test that introducing liquid phase at the inlet raises a thermodynamic error."""
    inlet= Stream(name="liquid_in", fluid="Water")
    inlet.update_by_PT(P=3000000.0, T= 300.0)

    turbine_system= Turbine(name="Liquid_Turbine", num_stages=2, eta_s_list=0.88)

    with pytest.raises(ValueError, match="liquid region| two-phase region"):
        turbine_system.run(inlet_stream= inlet, P_out= 500000.0)

def test_turbine_negative_pressure_drop_raises_error():
    """Test that target outlet pressure higher than inlet pressure raises an error."""
    inlet= Stream(name="inlet", fluid="Water")
    inlet.update_by_PT(P=500000.0, T=500.0)

    turbine_system= Turbine(name="Bad_DP_Turbine", num_stages=2, eta_s_list=0.88)

    with pytest.raises(ValueError,
                       match="Target outlet pressure .*is higher than inlet pressure"):
        turbine_system.run(inlet_stream=inlet, P_out=1000000.0)
