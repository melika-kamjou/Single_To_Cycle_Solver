"""Industrial Boiler equipment backend module for thermodynamic calculations."""
# pylint: disable=invalid-name, too-many-locals, too-many-branches, too-many-statements, broad-exception-caught, raise-missing-from, too-many-arguments
import os
import sys
from base_component import BaseComponent
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..",".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


class Boiler(BaseComponent):
    """
    Industrial Boiler (Steam Generator) Component.
    Strict thermodynamic & industrial validation:
      1. Feedwater validation: Inlet must be subcooled or saturated liquid.
      2. Pressure drop check: P_out <= P_in.
      3. Effectiveness limits: 0.50 <= epsilon <= 1.0.
      4. First & Second Law compliance: Q_dot > 0, h_out > h_in, W_dot= 0.
    """
    def __init__(self, name: str, effectiveness: float= 0.90):
        super().__init__(name)
        if not 0.50 <= effectiveness <= 1.0:
            raise ValueError(
                f"Thermodynamic Error [{name}]: Boiler effectiveness ({effectiveness})"
                f"is out of industrial limits [0.5, 1.0]"
            )
        self.effectiveness= effectiveness
        self.Q_dot= 0.0
        self.W_dot= 0.0

    def run(
        self,
        inlet_stream: Stream,
        P_out: float=None,
        delta_P: float= None,
        target_superheat: float= 20.0,
        effectiveness: float= None
    ):
        """
        Execute the boiler thermodynamic simulation and compute outlet stream properties.
        Args:
            inlet_stream (Stream): The incoming feedwater thermodynamic  stream.
            P_out (float, optional): Target outlet pressure in Pascals.
            delta_P (float, optional): Pressure drop across the boiler in Pascals.
            target_superheat (float): Target superheat temperature above saturation in Celsius.
            effectiveness (float, optional): Thermal effectiveness override for this run.
        
        Returns:
            Stream: The generated outlet stream, or None if the input stream is invalid.
        """
        if inlet_stream is None:
            return None
        current_effectiveness= self.effectiveness
        if effectiveness is not None:
            if not 0.5 <= effectiveness <= 1.0:
                raise ValueError(
                    f"Thermodynamic Error [{self.name}]: Provided effectiveness ({effectiveness})"
                    f"is out of industrial limits [0.5, 1.0]"
                )
            current_effectiveness= effectiveness
        if inlet_stream.P is None or inlet_stream.h is None:
            raise ValueError(f"[{self.name}] Inlet stream properties (P, h) are not fully defined.")

        fluid= inlet_stream.fluid
        P_in= inlet_stream.P
        h_in= inlet_stream.h
        m_dot= inlet_stream.m_dot

        if P_out is not None:
            target_P = P_out
        elif delta_P is not None:
            target_P= P_in - delta_P
        else:
            target_P= P_in

        if target_P > P_in:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: Outlet pressure ({target_P:.1f} Pa)"
                f"cannot be higher than inlet stream ({P_in:.1f} Pa)"
            )

        # Industrial Constraint: Feedwater phase verification
        try:
            sat_vapor= Stream(name= f"{self.name}_sat_check", fluid= fluid)
            sat_vapor.update_by_Px(P=P_in, x=1.0)

            if inlet_stream.T is not None and sat_vapor.T is not None:
                if inlet_stream.T > sat_vapor.T:
                    raise ValueError(
                        F"Thermodynamic Error [{self.name}]: Inlet stream temperature"
                        f"({inlet_stream.T - 273.15:.2f} °C) exceeds saturation temperature"
                        f"({sat_vapor.T - 273.15:.2f} °C)."
                        " Industrial Error: Boiler feedwater must be liquid/two-phase."
                    )
        except Exception as e:
            if "Thermodynamic Error" in str(e):
                raise e

        # Calculate ideal boiler state at target pressure
        try:
            sat_stream= Stream(name=f"{self.name}_sat", fluid= fluid)
            sat_stream.update_by_Px(P=target_P, x= 1.0)
            T_sat= sat_stream.T

            if target_superheat > 0.0:
                superheated_stream= Stream(name= f"{self.name}_superheated", fluid= fluid)
                superheated_stream.update_by_PT(P= target_P, T= T_sat + target_superheat)
                h_ideal_out= superheated_stream.h
            else:
                h_ideal_out= sat_stream.h
        except Exception as e:
            raise ValueError (f"[{self.name}] Stream calculation failed for ideal state: {str(e)}")

        if h_in >= h_ideal_out:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: Inlet enthalpy"
                f" ({h_in / 1000.0:.2f} kJ/kg)"
                f"is already higher than or equal to ideal boiler target"
                f" enthalpy ({h_ideal_out / 1000.0:.2f} kJ/kg)."
            )

        delta_h_max= h_ideal_out - h_in
        delta_h_actual= current_effectiveness* delta_h_max
        h_out= h_in + delta_h_actual

        self.Q_dot= m_dot* (h_out - h_in)
        self.W_dot= 0.0

        if h_out <= h_in:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: Outlet enthalpy ({h_out / 1000.0:.2f} kJ/kg)"
                f"cannot be less than or equal to inlet enthalpy."
           )

        outlet_stream= Stream(name=f"{inlet_stream.name}_outlet", fluid= fluid)
        outlet_stream.update_by_Ph(P= target_P, h= h_out, m_dot=m_dot)

        return outlet_stream

    def calculate(self, *args, **kwargs):
        """Alias method to execute the boiler simulation for unified equipment interfaces."""
        return self.run(*args, **kwargs)
