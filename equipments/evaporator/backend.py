"""Backend thermodynamic module for the industrial evaporator component.
This module handles mass and energy balance, phase-state validations,
and heate addition calculations for evaporators.
"""
# pylint: disable=invalid-name,too-many-branches, too-many-statements, broad-exception-caught, raise-missing-from, too-many-locals, too-many-arguments
import os
import sys
from base_component import BaseComponent
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..",".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

class Evaporator(BaseComponent):
    """
    Evaporator Component (Heat Exchanger - Heat Addition).
    Thermodynamic constraints and industrial validation:
        1. Inlet phase validation: Evaporator inlet must be liquid,
        saturated liquid, or tow_phase mixture.
            if the inlet is already in superheated vapor region,
            a strict industrial/thermodynamic error is raised.
        2. Pressure drop constraint: Outlet pressure cannot exceed inlet pressure
        (P_out <= P_in, supports explicit P_out or delta_P specification).
        3. Effectiveness mode: Component effectiveness (epsilon) must 
        within valid industrial limits [0.5, 1.0].
            Actual enthalpy rise is computed via effectiveness relative 
            to the ideal saturation/superheat state.
        4.First & Secind Law compliance: Heat addition Q_dot > 0, h_out > h_in.
        5. No work transfer (W_dot = 0).
    """
    def __init__(self, name: str, effectiveness: float=0.90):
        super().__init__(name)
        if not 0.5 <= effectiveness <= 1.0:
            raise ValueError(
                f"Thermodynamic Error [{name}]: Evaporator effectiveness"
                f"({effectiveness}) is out of industrial limits [0.50, 1.0]"
            )
        self.effectiveness= effectiveness
        self.Q_dot= 0.0
        self.W_dot= 0.0

    def run(
        self,
        inlet_stream: Stream,
        P_out: float=None,
        delta_P: float=None,
        target_superheat: float= None,
        effectiveness: float= None
    ):
        """Execute thermodynamic simulation for the evaporator componenet.
        Args:
            inlet_stream (Stream): The inlet stream object entering the evaporator.
            P_out (float, optional): Target outlet pressure in Pascals. Defaults to None.
            delta_P (float,optional): Pressure drop across the component in Pascals.
            Defaults to None.
            target_superheat (float, optional):Degrees of superheat above
            saturation temperature at outlet. Defaults to None.
            effectiveness (float, optional):Runtime override for component
            effectiveness [0.50, 1.00]. Defaults to None.
        Returns:
            Stream: The updated outlet stream object, or None if the inlet stream is None.
        Raises:
            ValueError: If thermodynamic constraints
            (Such as inlet phase,pressure limits, or enthalpy bounds) are violated.
            """
        if inlet_stream is None:
            return None
        current_effectiveness= self.effectiveness
        if effectiveness is not None:
            if not 0.5 <= effectiveness <= 1.0:
                raise ValueError(
                    f"Thermodynamic Error [{self.name}]:"
                    f"Provided effectiveness ({effectiveness})"
                    f"is out of industrial limits [0.50, 1.00]"
                )
        current_effectiveness=effectiveness

        if inlet_stream.P is None or inlet_stream.h is None:
            raise ValueError(f"[{self.name}] Inlet stream properties (P, h)"
                             " are not fully defined.")

        fluid= inlet_stream.fluid
        P_in= inlet_stream.P
        h_in= inlet_stream.h
        m_dot= inlet_stream.m_dot

        if P_out is not None:
            target_P= P_out
        elif delta_P is not None:
            target_P= P_in - delta_P
        else:
            target_P= P_in

        if target_P > P_in :
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: Outlet pressure ({target_P:.1f} Pa)"
                f"cannot be higher than inlet pressure ({P_in:.1f} Pa) in evaporator."
                "Evaporators are passive heat addition devices and can only cause"
                "pressure drop or operate isobarically (P_out <= P_in)."
            )

        # Constraint 1: Inlet phase validation (Evaporator inlet cannot be superheated vapor)
        try:
            sat_vapor= Stream(name=f"{self.name}_sat_check", fluid=fluid)
            sat_vapor.update_by_Px(P=P_in, x=1.0)
            if inlet_stream.T is not None and sat_vapor.T is not None:
                if inlet_stream.T > sat_vapor.T:
                    raise ValueError(
                        f"Thermodynamic Error [{self.name}]: Inlet stream temperature"
                        f"({inlet_stream.T - 273.15:.2f}°C) is above the saturation temperature"
                        f"({sat_vapor.T - 273.15:.2f}°C). "
                        "Evaporator inlet stream cannot be superheated vapor!"
                    )
        except Exception as e:
            if "Thermodynamic Error" in str(e):
                raise e
        # Calculate ideal evaporation state at target pressure (saturated vapor or superheated)
        try:
            sat_stream= Stream(name=f"{self.name}_sat", fluid=fluid)
            sat_stream.update_by_Px(P= target_P, x= 1.0)
            T_sat= sat_stream.T
            h_sat_vapor= sat_stream.h

            if target_superheat > 0.0:
                superheated_stream= Stream(name=f"{self.name}_superheated", fluid=fluid)
                superheated_stream.update_by_PT(P=target_P, T= T_sat + target_superheat)
                h_ideal_out= superheated_stream.h
            else:
                h_ideal_out= h_sat_vapor
        except Exception as e:
            raise ValueError(f"[{self.name}] Stream calculation failed for ideal state:"
                             f" {str(e)}")

        if h_in >= h_ideal_out:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]:"
                f"Inlet enthalpy ({h_in / 1000.0:.2f} kJ/kg)"
                "is already higher than or equal to the ideal"
                f"evaporation enthalpy ({h_ideal_out / 1000.0:.2f} kJ/kg)."
            )

        delta_h_max= h_ideal_out - h_in
        delta_h_actual= current_effectiveness * delta_h_max
        h_out= h_in + delta_h_actual

        self.Q_dot= m_dot* (h_out - h_in)
        self.W_dot= 0.0

        if h_out <= h_in:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]:"
                f"Outlet enthalpy ({h_out/1000.0:.2f} kJ/kg)"
                "cannot be less than or equal to inlet enthalpy"
                f"({h_in / 1000.0:.2f} kJ/kg)."
            )
        outlet_stream= Stream(name= f"{inlet_stream.name}_outlet", fluid=fluid)
        outlet_stream.update_by_Ph(P=target_P, h=h_out, m_dot=m_dot)

        return outlet_stream
    def calculate(self, *args, **kwargs):
        """Alias for run method to ensure structural compatibility with solvers."""
        return self.run(*args, **kwargs)
