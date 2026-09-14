"""Backend  thermodynamic simulation module for an industrial combustion chamber.
This module implements the mass and energy balance equations, chemical heat release
calculations using fuel lower heating value (LHV) and combustion efficiency,
and pressure constraint validations for industrial combustors.
"""
# pylint: disable=invalid-name, too-many-locals, too-many-branches, too-many-statements, broad-exception-caught, raise-missing-from, too-many-arguments
import os
import sys
from base_component import BaseComponent
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..",".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

class CombustionChamber(BaseComponent):
    """
    Industrial Combustion Chamber (Combustor) Component.
    Thermodynamic & Industrial constraints:
        1. Mass balance: m_dot_out= sum(m_dot_in_i) + m_dot_fuel
        2. Energy balance: h_out= (sum(m_dot_i * h_in) + Q_combustion) / m_dot_out
        where Q_combustion = m_dot_fuel * lHV * efficiency
        3. Pressure constraint: Minor pressure drop across the combustion chamber (P_out <= min_p).
    """
    def __init__(self, name:str, combustion_efficiency:float=0.98):
        super().__init__(name)
        if not 0.5 <= combustion_efficiency <= 1.0:
            raise ValueError(f"[{self.name}] Combustion efficiency must be between 0.5 and 1.0")
        self.combustion_efficiency= combustion_efficiency
        self.Q_dot= 0.0
        self.W_dot=0.0
        self.outlet_stream= None
    def run(self, inlet_streams: list, fuel_mass_flow: float=0.1,
            fuel_lhv: float= 50000.0, P_out:float= None):
        """Run the thermodynamic simulation for the combustion chamber.
        Args:
            inlet_streams (list): List of incoming Stream objects to be mixed and burned.
            fuel_mass_flow (float): Mass flow rate of the fuel in kg/s. Default is 1.0.
            fuel_lhv (float): Lower Heating Value (LHV) of the fuel in kJ/kg. Default is 50000.0.
            P_out (float, optional): Specified outlet pressure in Pascals. If None,
            a 2% pressure drop is applied.
        Returns:
            Stream: Theresulting flue gas outlet stream object containing updated
            thermodynamic properties.
        Raises:
            ValueError: If inlet streams are missing, fluid types mismatch,
            properties are undefined, or if the outlet pressure exceeds
            the lowest inlet pressure without compression.
        """
        if not inlet_streams or len(inlet_streams) < 1:
            raise ValueError(f"[{self.name}] Combustion Chamber requires at least 1 inlet stream.")

        fluid= inlet_streams[0].fluid
        total_m_dot_in= 0.0
        energy_sum= 0.0
        min_p= float("inf")

        for idx, stm in enumerate(inlet_streams):
            if stm.P is None or stm.h is None or stm.m_dot is None:
                raise ValueError(
                    f"[{self.name}] Inlet stream {idx+1} properties"
                    " (P, h, m_dot) are not fully defined.")
            if stm.fluid != fluid:
                raise ValueError(
                    f"[{self.name}] Industrial Error: Mixing streams with different fluids"
                    f"({stm.fluid} vs {fluid} is not supported.)")
            total_m_dot_in += stm.m_dot
            energy_sum += stm.m_dot * stm.h
            if stm.P < min_p:
                min_p= stm.P

        # Calculate chemical heat release from fuel (fuel_lhv in kJ/kg converted to J/kg -> *1000)
        self.Q_dot= fuel_mass_flow * (fuel_lhv * 1000.0) * self.combustion_efficiency
        total_m_dot_out= total_m_dot_in + fuel_mass_flow

        # Tatal energy out
        Total_energy_out= energy_sum + self.Q_dot
        h_out= Total_energy_out / total_m_dot_out

        # Determine exit pressure (default 2% pressure drop if P_out is not specified)
        target_P= P_out if P_out is not None else (min_p * 0.98)
        if target_P > min_p:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]:"
                f"Outlet pressure ({target_P:.1f} Pa)"
                f"cannot exceed the lowest inlet pressure ({min_p:.1f} Pa)"
                " without external compression."
            )

        # Creat outlet flue gas stream
        self.outlet_stream= Stream(name=f"{self.name}_flue_gas_outlet", fluid=fluid)
        self.outlet_stream.update_by_Ph(P= target_P, h= h_out, m_dot=total_m_dot_out)
        return self.outlet_stream

    def calculate(self, *args, **kwargs):
        """Alias method to execute the combustion-chamber simulation
        for unified equipment interfaces."""
        return self.run(*args, **kwargs)
