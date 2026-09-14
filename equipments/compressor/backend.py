"""Backend thermodynamic simulation module for an industrial gas compressor.
This module handles the thermodynamic modeling of gas compression precesses,
including state validation, isentropic efficiency calculations, first and second law
compliance, and liquid slugging prevention.
"""
# pylint: disable=invalid-name, too-many-locals, too-many-branches, too-many-statements, broad-exception-caught, raise-missing-from, too-many-arguments
import sys
import os
from base_component import BaseComponent
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

class Compressor(BaseComponent):
    """
    Madular Gas Copressor Component with strict thermodynamic consttraints.
    Enforced constraints:
        1. Inlet stream must be in vapor or gas phase (no liquid/ liquid slugging prevention).
        2. Compressor work and pressure rise must be posetive (P_out >= P_in, W_dot > 0).
        3. Isentropic efficiencty must be between 0 and 1 (0 < eta_s <= 1).
        4. First and Second Law of thermodynamics compliance (h_out >= h_2s for actual compressor).
        5. Mass and energy balance monitoring.
    """
    def __init__(self, name: str, eta_s: float= 1.0):
        super().__init__(name)
        if not 0.0 < eta_s <= 1.0:
            raise ValueError(f"[{name}] Isentropic efficiency must be strictly between 0 and 1.")
        self.eta_s = eta_s
        self.W_dot= 0.0
        self.Q_dot= 0.0

    def run(
            self,
            inlet_stream: Stream,
            outlet_stream: Stream= None,
            P_out: float= None,
            eta_s: float= None,
    ):
        """ Run the thermodynamic simulation for the gas compressor.
        Args:
            inlet_stream (Stream): The incoming gas or vapor stream object.
            outlet_stream (Stream, optional): Pre-defined outlet stream object, if any.
            P_out (float, optional): Target outlet pressure in Pascals.
            eta-s (float, optional): Isentropic efficiency override (0 < eta_s <= 1).
        Returnas:
            Stream: The resulting high_pressure outlet stream object with updated properties.
        Raises:
            ValueError: If inlet is in liquid/two-phase region, pressure drops,
                        efficiency is out of bounds, or Second Law is violated.
        """
        #Handle list or tuple inputs from solver
        if isinstance(inlet_stream, (list, tuple)):
            inlet_stream= inlet_stream[0] if len(inlet_stream) > 0 else None
        if isinstance(outlet_stream,(list, tuple)):
            outlet_stream= outlet_stream[0] if len(outlet_stream) > 0 else None

        if inlet_stream is None:
            return outlet_stream
        target_P_out= P_out
        if target_P_out is None and outlet_stream is not None:
            target_P_out= outlet_stream.P

        if(
           inlet_stream.P is None
           or inlet_stream.h is None
           or inlet_stream.s is None
           or target_P_out is None
        ):
            return None

        fluid= inlet_stream.fluid
        s_in= inlet_stream.s
        h_in= inlet_stream.h
        m_dot= inlet_stream.m_dot

        #___Constraint 1: Inlet stae must be vapor/gas (prevent liquid slugging)___
        #Check if innlet is in two_phase region (0 <= x <= 1)
        if inlet_stream.x is not None and 0.0 <= inlet_stream.x <= 1.0:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: Inlet stream is in two_phase region "
                f"(x= {inlet_stream.x}). Compressor cannot handle wet vapor or liquid!"
            )
        # Check if inlet temperature is below or equal to saturation temperature
        try:
            sat_liquid= Stream(name= f"{self.name}_sat", fluid=fluid)
            sat_liquid.update_by_Px(inlet_stream.P, 0.0)
            if sat_liquid.T is not None and inlet_stream.T <= sat_liquid.T:
                raise ValueError(
                    f"Thermodynamic Error [{self.name}]: Inlet stream is in the liquid region"
                    f"(T = {inlet_stream.T - 273.15:.2f} °C <= T_sat ="
                    f"{sat_liquid.T -273.15:.2f} °C)."
                )
        except  Exception as e:
            if "Thermodynamic Error" in str(e):
                raise e
        # ___Constraint 2: Pressure rise and work cannot be negative ___
        if target_P_out < inlet_stream.P:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: Outlet pressure"
                f" ({target_P_out:.1f} Pa)"
                f"is lower than inlet pressur ({inlet_stream.P:.1f} Pa)."
                "Compressor work cannot be negative."
            )

        eff= eta_s if eta_s is not None else self.eta_s
        if eff is None:
            eff= 1.0

        #Validate efficiency bounds
        if not 0.0 < eff <= 1.0:
            raise ValueError(f"[{self.name}] Isentropic efficiency must"
                             "be greater than 0 and less than or equal to 1.")

        #Calculate ideal isentropic state at outlet
        s_ideal = Stream(name= f"{self.name}_ideal", fluid=fluid)
        s_ideal.update_by_Ps(target_P_out, s_in)
        h2s= s_ideal.h

        #Calculate actual outlet enthalpy and verify Second Law
        if(
            outlet_stream is not None
            and outlet_stream.h is not None
            and outlet_stream.h != h_in
        ):
            h_out_act= outlet_stream.h

            # Second Law check for 100% efficiency case
            if h_out_act < h2s and eff == 1.0:
                raise ValueError(
                    f"Second Law violation [{self.name}]: Actual outlet enthalpy ({h_out_act:.2f})"
                    f"is less than isentropic enthalpy ({h2s:.2f})."
                )

            if (h_out_act - h_in) != 0:
                calc_eta= (h2s - h_in) / (h_out_act - h_in)
                if 0.0 < calc_eta <= 1.0:
                    raise ValueError(
                        f"Thermodynamic Error [{self.name}]: Calculated efficiency {calc_eta:.3f}"
                        f"violates physical limits (0, 1]"
                    )
                self.eta_s = calc_eta
            out_stream= outlet_stream
        else:
            if eff == 1.0:
                h_out_act = h2s
            else:
                #Real enthalpy increase higher than ideal due to irreversibility in compressor
                h_out_act= h_in + (h2s - h_in) / eff

            out_stream= (
                outlet_stream if outlet_stream is not None
                else Stream(name= f"{self.name}_out", fluid=fluid)
            )
            out_stream.update_by_Ph(target_P_out, h_out_act, m_dot=m_dot)
        # Mass and Energy Balance (First Law)
        if m_dot is not None and h_in is not None and out_stream.h is not None:
            #W_dot in kW (m_dot in kg/s, enthalpy in J/kg -> divided by 1000.0)
            self.W_dot= abs(m_dot * (out_stream.h - h_in)/ 1000.0)
        else:
            self.W_dot= 0.0
        self.Q_dot= 0.0
        return out_stream
    def calculate(self, *args, **kwargs):
        """Alias for run method to ensure structural compatibility with solvers."""
        return self.run(*args, **kwargs)
