"""Backend thermodynamic model for the Throttling Valve component.
Handles isenthalpic expansion, pressure drop constraints, and safety  check.
"""
#pylint: disable= invalid-name
import os
import sys
from base_component import BaseComponent
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..",".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

class Valve(BaseComponent):
    """
    Throttling Valve Component (Expansion / Control Valve).
    Thermodynamic constraints:
        1. Isenthalpic process (h_out = h_in).
        2. No work or heat transfer (W_dot = 0 , Q_dot = 0).
        3.Positive pressure drop (P_out <= P_in).
    """
    def __init__(self, name: str, valve_type: str="Expansion Valve"):
        super().__init__(name)
        self.valve_type= valve_type
        self.W_dot= 0.0
        self.Q_dot= 0.0

    def run(self,inlet_stream: Stream, P_out: float= None, delta_P: float= None):
        """
        Executes the thermodynamic simulation for a throttling/expansion valve.
        Parameters:
            inlet_stream (Stream): The incoming thermodynamic stream object.
            P_out (float, optional): Target outlet pressure in Pascals.
            delta_P (float, optional): Pressure drop across the valve in Pascals.
        Returns:
            Stream: The updated outlet stream object.
        Raises:
            ValueError: If inlet properties are missing,
            neither P_out nor delta_P is specified,
            or if target pressure is higher than inlet pressure (invalid pressure rise).
        """
        if inlet_stream is None:
            return None
        if inlet_stream.P is None or inlet_stream.h is None:
            raise ValueError(f"[{self.name}] Inlet stream properties "
                             "(P, h) are not fully deafined.")
        # Determine target outlet pressurebased on user specification
        if P_out is not None:
            target_P= P_out
        elif delta_P is not None:
            target_P= inlet_stream.P - delta_P
        else:
            raise ValueError(f"[{self.name}] Either P_out or delta_P must be"
                             " specified for the valve.")

        # Check thermodynamic physical constraint for pressure drop
        if target_P > inlet_stream.P:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: "
                f"Outlet pressure ({target_P:.1f} Pa)"
                f"cannot be higher than inlet pressure ({inlet_stream.P:.1f} Pa) "
                "in an expansion/throttling valve."
                "Valves are passive devices and can only "
                "cause pressure drop (P_out <= P_in)."
                "If you need to increase pressure, please use"
                " a Pump or Compressor instead."
            )

        # Creat outlet stream copy assuming isenthalpic expansion (h_out = h_in)
        outlet_stream= Stream(name=f"{inlet_stream.name}_outlet",
                              fluid=inlet_stream.fluid)
        m_dot_val= getattr(inlet_stream, "m_dot", 1.0)
        outlet_stream.update_by_Ph(P=target_P, h= inlet_stream.h,
                                   m_dot=m_dot_val)

        return outlet_stream

    def calculate(self, *args, **kwargs):
        """Alias for run method to ensure structural compatibility with solvers."""
        return self.run(*args, **kwargs)
