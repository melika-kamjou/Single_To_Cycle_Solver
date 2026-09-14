"""Industrial Mixing Chamber (Mixer) Component.
Thermodynamic & Industrial constraints:
    1. Mass balance: m_dot_out= sum(m_dot_i)
    2. Energy balance (Adiabatic): h_out= sum(m_dot_i * h_in_i) / m_dot_out
    3. Pressure constraint: P_out is determined by the lowes inlet pressure or
    specified common operating pressure.
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

class MixingChamber(BaseComponent):
    """
    Industrial Mixing Chamber (Mixer) Component.
    Thermodynamic & Industrial constraints:
        1. Mass balance: m_dot_out = sum(m_dot_in_i)
        2. Energy balance (Adiabatic): sum(m_dot_i * h_in) / m_dot_out
        3. Pressure constraint: P_out is determined by the lowest inlet pressure
        or specified common operating pressure.
    """
    def __init__(self, name:str):
        super().__init__(name)
        self.Q_dot= 0.0
        self.W_dot= 0.0
        self.outlet_stream= None

    def run(self, inlet_streams: list, P_out: float= None):
        """Execute thermodynamic simulation and adiabatic mixing for the mixing chamber.
        Args:
            inlet_streams (list of Stream): A list of incoming Stream objects to be mixed.
            P_out (float, optional): Specified common outlet pressure in Pascals.
            Defaults to None.

        Returns:
            Stream: The mixed outlet stream object.
        Raises:
            ValueError: If fewer than 2 inlet streams are provided,
            strem properties are undifined,
            inlet fluids are incompatible, or outlet pressure exceeds
            the lowest inlet pressure.
            """
        if not inlet_streams or len(inlet_streams) < 2:
            raise ValueError(f"[{self.name}] Mixing Chamber requires at "
                             "least 2 inlet streams.")

        fluid= inlet_streams[0].fluid
        total_m_dot= 0.0
        energy_sum= 0.0
        min_p= float("inf")

        for idx, stm in enumerate(inlet_streams):
            if stm.P is None or stm.h is None or stm.m_dot is None:
                raise ValueError(f"[{self.name}] Inlet stream {idx+1} "
                                 "properties (P, h, m_dot) are not fully defined.")
            if stm.fluid != fluid:
                raise ValueError(f"[{self.name}] Industrial Error: Mixing streams"
                                 " with different fluids"
                                 f" ({stm.fluid} vs {fluid}) is not supported.")

            total_m_dot+= stm.m_dot
            energy_sum += stm.m_dot*stm.h
            if stm.P < min_p:
                min_p= stm.P

        # Determine exit pressure
        target_P= P_out if P_out is not None else min_p
        if target_P > min_p:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]:"
                f"Outlet pressure ({target_P:.1f} Pa)"
                f"cannot exceed the lowest inlet pressure"
                f"({min_p:.1f} Pa) without external pumping."
            )

        # Calculate mixed enthalpy
        h_out= energy_sum / total_m_dot

        # Creat mixed outlet stream
        self.outlet_stream= Stream(name=f"{self.name}_mixed_outlet", fluid= fluid)
        self.outlet_stream.update_by_Ph(P=target_P, h=h_out, m_dot= total_m_dot)

        return self.outlet_stream
    def calculate(self, *args, **kwargs):
        """Alias for run method to ensure structural compatibility with solvers."""
        return self.run(*args, **kwargs)
