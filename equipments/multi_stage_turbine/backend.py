"""Backend thermodynamic module for the unified single-stage and multi-stage turbine equipment.
This module handles multi-stage expansion paths, isentropic efficiencies,
blade erosion limits, and rigorous First/Second Law thermodynamic validations.
"""
# pylint: disable= invalid-name, too-many-instance-attributes, too-many-locals,broad-exception-caught, too-many-branches
import sys
import os
from base_component import BaseComponent
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..",".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

class Turbine(BaseComponent):
    """
   Unified Modular Turbine Component (Supports both Single_Stage and Multi_Stage).
    Enforces all rigorous thermodynamic constraints of the single-stage turbine across every stage:
        1. Inlet stream vapor/gas phase validation per stage.
        2. Positive pressure drop per stage.
        3. Isentropic efficiency bounds (0 < eta_s <= 1) per stage.
        4. First and Second Law compliance per stage.
        5. Enthalpy decrease across each stage.
        6. Cumulative negative work/power (W_dot < 0).
        7. Second Law Enthalpy Generation check (s_out >= s_in) per stage.
        8. Blade Erosion limit (x >= 0.88) across stages.
    """
    def __init__(self, name:str, num_stages: int=1, eta_s_list= 0.88):
        super().__init__(name)
        if num_stages < 1 :
            raise ValueError(f"[{name}] Number of stages must be at least 1.")
        self.num_stages= num_stages
        self.W_dot_stage= 0.0
        self.stage_streams= []

        # Handle efficiency input: can be a single float or a list/tuple per stage
        if isinstance(eta_s_list, (list, tuple)):
            if len(eta_s_list) != num_stages:
                raise ValueError(f"[{name}] Length of efficiency list must match"
                                f"the number of stages ({num_stages}).")
            for eff in eta_s_list:
                if not 0.0 < eff <= 1.0:
                    raise ValueError(f"[{name}] Isemtropic efficiency must be"
                                     " strictly between 0 and 1.")
            self.eta_s_list= list(eta_s_list)

        else:
            if not 0.0 < eta_s_list <= 1.0:
                raise ValueError(f"[{name}] Isentropic efficiency must be "
                                 "strictly between 0 and 1.")
            self.eta_s_list= [eta_s_list] * num_stages

        self.W_dot= 0.0
        self.Q_dot= 0.0
        self.stages= []
        self.stage_stream= []

    def _run_single_stage(self,name: str, inlet_stream: Stream,
                          target_P_out: float, eta_s: float) -> Stream:
        """Internal helper method executing single-stage turbine 
        thermodynamic and constraints."""
        if inlet_stream is None or target_P_out is None:
            return None

        if (
            inlet_stream.P is None
            or inlet_stream.h is None
            or inlet_stream.s is None
        ):
            return None

        fluid= inlet_stream.fluid
        s_in= inlet_stream.s
        h_in= inlet_stream.h
        m_dot= inlet_stream.m_dot

        #--- Constraint 1: Inlet state must be vapor/gas ---
        if inlet_stream.x is not None and 0.0 <= inlet_stream.x <= 1.0:
            if inlet_stream.x < 0.88:
                raise ValueError(
                    f"Blade Erosion Error [{name}]: Inlet stream vapor quality"
                    f" (x= {inlet_stream.x:.3f})"
                    f"is below than minimum safe limit of 0.88."
                )

        else:
            try:
                sat_liquid= Stream(name= f"{name}_sat", fluid=fluid)
                sat_liquid.update_by_Px(inlet_stream.x, 0.0)
                if sat_liquid.T is not None and inlet_stream.T <= sat_liquid.T:
                    raise ValueError(
                        f"Thermodynamic Error [{name}]: "
                        "Inlet stream is in the liquid region"
                        f"T= {inlet_stream.T - 273.15:.2f} °C <= "
                        f"T_sat = {sat_liquid.T - 273.15:.2f} °C."
                    )
            except Exception as e:
                if" Thermodynamic Error" in str(e):
                    raise e

        # ---Constraint 2: Pressure drop cannot be negative---
        if target_P_out > inlet_stream.P:
            raise ValueError(
                f"Thermodynamic Error [{name}]: Outlet pressure ({target_P_out:.1f} Pa)"
                f"is higher than inlet pressure ({inlet_stream.P:.1f} Pa)."
            )

        eff= eta_s if eta_s is not None else 1.0
        if not 0.0 < eff <= 1.0:
            raise ValueError(f"[{name}] Isentropic efficiency must be"
                             " greater than 0 and less than or equal to 1.")

        #Calculate ideal isentropic state at outlet
        s_ideal= Stream(name= f"{name}_ideal", fluid=fluid)
        s_ideal.update_by_Ps(target_P_out, s_in)
        h2s= s_ideal.h
        if eff == 1.0:
            h_out_act= h2s
        else:
            h_out_act= h_in - eff * (h_in - h2s)

        out_stream= Stream(name= f"{name}_out", fluid=fluid)
        out_stream.update_by_Ph(target_P_out, h_out_act, m_dot=m_dot)

        # ---Constraint 3: Second Law Entropy Generation Check (s_out >= s_in) ---
        if out_stream.s < s_in - 1e-4:
            raise ValueError(
                f"Second Law violation [{name}]: "
                f"Outlet entropy ({out_stream.s / 1000.0:.4f})"
                f"is less than inlet entropy ({s_in / 1000.0:.4f})."
            )

        #---Constraint 4: Blade Erosion / Exit wetness limit (x >= 0.88)---
        if out_stream.x is not None and 0.0 < out_stream.x < 1.0:
            min_safe_quality= 0.88
            if out_stream.x < min_safe_quality:
                raise ValueError(
                    f"Blade Erosion Error [{name}]: "
                    f"Outlet vapor quality (x= {out_stream.x:.3f})"
                    f"is below the safe limit ({min_safe_quality})"
                )

        #---Constraint 5 : First Law & Sign Convention (Turbine work must be negative)---
        if m_dot is not None and h_in is not None and out_stream.h is not None:
            W_dot_stage= (m_dot * (out_stream.h - h_in)) / 1000.0
            if W_dot_stage > 0.0:
                raise ValueError(
                    f"Thermodynamic Error [{name}]: "
                    f"Turbine work/power ({W_dot_stage:.3f} kW)"
                    "cannot be positive."
               )

        else:
            W_dot_stage= 0.0

        self.eta_s= eff
        self.W_dot_stage= W_dot_stage
        return out_stream
    def run (
        self,
        inlet_stream: Stream,
        outlet_stream: Stream = None,
        P_out: float=None,
        eta_s_list: float= None
    ):
        """Execute thermodynamic simulation and multi-stage expansionfor the turbine.
        Args:
            inlet_stream (Stream): The incoming high_pressure stream entering the turbine.
            outlet_stream (Stream): Target or placeholder outlet stream object.
            P_out (float, optional): Target final outlet pressure in Pascals.
            Defaults to None.
            eta_s_list (float or list of float, optional):
                Isentropic efficiency for stage(s). Defaults to None. 
        Returns:
            Stream: The final expanded outlet stream object.
        Raises:
            ValueError: 
                If inlet phase is invalid, pressure constraints are violated,
                entropy decreases, or blade erosion limits are breached.
            """
        if isinstance(inlet_stream, (list, tuple)):
            inlet_stream= inlet_stream[0] if len(inlet_stream) > 0 else None
        if isinstance(outlet_stream, (list, tuple)):
            outlet_stream= outlet_stream[0] if len(outlet_stream) > 0 else None

        if inlet_stream is None:
            return outlet_stream

        target_P_out= P_out
        if target_P_out is None and outlet_stream.P is not None:
            target_P_out= outlet_stream.P

        if(
            inlet_stream.P is None
            or inlet_stream.h is None
            or inlet_stream.s is None
            or target_P_out is None
        ):
            return None

        if target_P_out > inlet_stream.P:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: "
                f"Outlet pressure ({target_P_out:.1f} Pa)"
                f"is higher than inlet pressure ({inlet_stream.P:.1f} Pa)."
            )

        if eta_s_list is not None:
            if isinstance(eta_s_list, (list,tuple)):
                if len(eta_s_list) != self.num_stages:
                    raise ValueError(f"[{self.name}] Length of efficiency list "
                                     f"must match num_stages ({self.num_stages}).")
                self.eta_s_list= list(eta_s_list)
            else:
                self.eta_s_list= [eta_s_list] * self.num_stages

        # Clculate stage pressure using equal pressure ratio rule:
            #r_p= (P_out / P_in)^(1/N)
        p_in= inlet_stream.P

        current_stream= inlet_stream
        total_W_dot= 0.0
        self.stages= []
        self.stage_streams = [inlet_stream]

        for i in range(self.num_stages):
            if self.num_stages > 1:
                stage_name= f"{self.name}_Stage_{i+1}"
            else:
                stage_name= self.name
            stage_p_out= p_in * ((target_P_out / p_in) ** ((i+1) / self.num_stages))

           # Run single stage calculation
            current_stream= self._run_single_stage(
                name= stage_name,
                inlet_stream= current_stream,
                target_P_out= stage_p_out,
                eta_s= self.eta_s_list[i]
            )

            total_W_dot += self.W_dot_stage
            self.stages.append({
                "name": stage_name,
                "eta_s": self.eta_s_list[i],
                "W_dot": self.W_dot_stage
            })
            self.stage_streams.append(current_stream)
        self.W_dot = total_W_dot
        self.Q_dot= 0.0

        return current_stream

    def calculate(self, *args, **kwargs):
        """Alias for run method to ensure structural compatibility with solvers."""
        return self.run(*args, **kwargs)
