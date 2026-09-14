"""Backend thermodynamic model for Liquid Pump equipment.
Handles mass/energy balances, isentropic efficiency, 
and strict liquid phase constraints.
"""
#pylint: disable= too-many-locals, invalid-name, too-many-branches
import sys
import os
from base_component import BaseComponent
from stream import Stream
current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

class Pump(BaseComponent):
    """
    Modular Liquid Pump Component with strict thermodynamic constraints.
    Enforced constraints:
        1. Inlet and outlet must be strictly in liquid phase (no vapor/two_phase).
        2. Pump work and pressure rise must be posetive (p_out >= P_in, W_dot > 0).
        3. Isentropic efficiency must be between 0 and 1 (0 < eta_s <= 1).
        4.First and second Law of thermodynamics compliance (h_out >= h_2s for actual pump).
        5. Mass and enrgy balance monitoring.
    """
    def __init__(self,name: str,eta_s: float= 1.0):
        super().__init__(name)
        if not 0.0 < eta_s <= 1.0:
            raise ValueError(f"[{name}] Isentropic efficiency must be "
                             "strictly between 0 and 1.")
        self.eta_s = eta_s
        self.W_dot = 0.0
        self.Q_dot= 0.0

    def run(
            self,
            inlet_stream: Stream,
            outlet_stream: Stream = None,
            P_out: float= None,
            eta_s: float=None,
    ):
        """Execute the thermodynamic simulation for a liquid pump.
        Parameters:
            inlet_stream (Stream): The incoming thermodynamic stream object.
            outlet_stream (Stream, optional): Pre-defined outlet object.
            P_out (float, optional): Target outlet pressure in Pascals.
            eta_s (float, optional): Isentropic efficiency of the pump (0 < eta_s <= 1).
        Returns:
            Stream: The updated outlet stream object containing calculated properties.
        Raises:
            ValueError: If inlet stream is in vapor/two-phase region, pressure drops,
            efficiency bounds are violated. or Second Law is breached.
            """
        # Handle list or tuple inputs from solver
        if isinstance(inlet_stream, (list, tuple)):
            inlet_stream= inlet_stream[0] if len(inlet_stream) > 0 else None
        if isinstance(outlet_stream, (list, tuple)):
            outlet_stream= outlet_stream[0] if len(outlet_stream) > 0 else None

        if inlet_stream is None:
            return outlet_stream

        target_P_out = P_out
        if target_P_out is None and outlet_stream is not None:
            target_P_out = outlet_stream.P

        if(
            inlet_stream.P is None
            or inlet_stream.h is None
            or inlet_stream.s is None
            or target_P_out is None
            ):
            return None

        # ___Constraint 1. : Inlet state must be liquid (no vapor/cavitation risk) ___
        # In CoolProp, vapor quality x is -1 for subcooled liquid, 0 for saturated liquid,
        # and > 0 up to 1 for two-phase/vapor.
        if inlet_stream.x is not None and inlet_stream.x>0.0:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: Inlet stream is in the vapor or"
                f"two=phase region (x= {inlet_stream.x}). Pumps can only handle liquids!"
            )
        # ___Constraint 2: Pressure rise and work cannot be negative ___
        if target_P_out < inlet_stream.P:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: "
                f"Outlet pressure ({target_P_out:1.f} Pa)"
                f"is lower than inlet pressure ({inlet_stream.P:.1f} Pa). "
                "Pump work cannot be negetive."
            )

        fluid = inlet_stream.fluid
        s_in = inlet_stream.s
        h_in= inlet_stream.h
        m_dot = inlet_stream.m_dot

        eff = eta_s if eta_s is not None else self.eta_s
        if eff is None:
            eff= 1.0

        # Validate efficiency bounds
        if not 0.0 < eta_s <= 1.0:
            raise ValueError(f"[{self.name}] Isentropic efficiency must be "
                             "greater than 0 and less than or equal to 1.")
        # Calculate ideal isentropic state at outlet
        s_ideal = Stream(name=f"{self.name}_ideal", fluid=fluid)
        s_ideal.update_by_Ps(target_P_out, s_in)
        h2s= s_ideal.h
        # Calculate actual outlet entalphy and verify Second Law
        if(
            outlet_stream is not None
            and outlet_stream.h is not None
            and outlet_stream.h != h_in
        ):
            h_out_act = outlet_stream.h

            # Second Law check for 100% efficiency case
            if h_out_act< h2s and eff == 1.0:
                raise ValueError(
                    f"Second Law violation [{self.name}]: "
                    f"Actual outlet enthalpy ({h_out_act:.2f})"
                    f"is less than isentropic enthalpy ({h2s:.2f})."
                )

            if (h_out_act - h_in) != 0:
                calc_eta = (h2s - h_in) / (h_out_act - h_in)
                if not 0.0 < calc_eta <= 1.0:
                    raise ValueError(
                        f"Thermodynamic Error [{self.name}]: "
                        f"Calculated efficiency {calc_eta:.3f}"
                        f"violates physical limits (0, 1]."
                    )
                self.eta_s= calc_eta
            out_stream= outlet_stream
        else:
            if eff== 1.0:
                h_out_act= h2s
            else:
                # Real enthalpy increase is higher than ideal due to irreversiblity
                h_out_act= h_in + (h2s - h_in) / eff

            out_stream=(
                outlet_stream if outlet_stream is not None
                else Stream(name=f"{self.name}_out", fluid=fluid)
            )
            out_stream.update_by_Ph(target_P_out, h_out_act, m_dot=m_dot)

        # ___Constraint 1 (Outlet): Outlet state must also remain liquid ___
        if out_stream.x is not None and out_stream.x > 0.0:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]:"
                " Outlet stream entered the vapor/two-phase"
                f"region (x = {out_stream.x}). Pump outlet must remain liquid."
            )
        #___Mass and Energy Balance (First Law) ___
        if m_dot is not None and h_in is not None and out_stream.h is not None:
            #W_dot in kW (m_dot in kg/s, enthalpy in J/kg -> divided by 1000.0)
            self.W_dot = abs(m_dot * (out_stream.h - h_in)/1000.0)
        else:
            self.W_dot = 0.0

        self.Q_dot = 0.0
        return out_stream

    def calculate(self, *args, **kwargs):
        """Alias for run method to ensure structural compatibility with solvers."""
        return self.run(*args,**kwargs)
