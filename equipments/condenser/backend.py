"""Backend thermodynamic module for the industrial condenser component.
This module handles mass and energy balances, phase-state validations,
and heat rejection calculations for condenser.
"""
# pylint: disable=invalid-name,too-many-branches, too-many-statements, broad-exception-caught, raise-missing-from, too-many-arguments, wrong-import-position, too-many-locals
import os
import sys
from base_component import BaseComponent
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..",".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

class Condenser(BaseComponent):
    """
    Condenser Component (Heat Exchanger - Heat Rejection).
    Thermodynamic constraints and industrial validation:
        1. Inlet phase validation: Condenser inlet must be vapor or superheated vapor.
        If the inlet is already in the liquid or subcooled region, 
        a strict industrial/thermodynamic error is raised.
        2. Pressure drop constraint: Outlet pressure cannot exceed inlet pressure 
        (P_out <= P_in, supports explicit P_out or delta_P specification).
        3. Effectiveness mode: Component effectiveness (epsilon) must be within 
        valid industrial limits [0.50, 1.00].
        Actual enthalpy drop is computed via effectiveness
        relative to the ideal saturation/subcooling state.
        4. First & Second Law compliance: Heat rejection Q_dot < 0, h_out < h_in.
        5. No work transfer (W_dot = 0.).
    """
    def __init__(self, name: str,effectiveness:float= 0.90):
        super().__init__(name)
        if not 0.5 <= effectiveness <= 1.0:
            raise ValueError(
                f"Thermodynamic Error [{name}]: Condenser effictiveness ({effectiveness})"
                f"is out of industrial limits [0.50, 1.00]."
            )
        self.effectiveness= effectiveness
        self.Q_dot= 0.0
        self.W_dot= 0.0

    def run(
        self,
        inlet_stream:Stream,
        P_out: float= None,
        delta_P: float= None,
        target_subcooling: float= 0.0,
        effectiveness: float= None
    ):
        """Execute thermodynamic simulation for the condenser component."""
        if inlet_stream is None:
            return None

        # optional runtime effectiveness update with strict validation
        current_effectiveness= self.effectiveness
        if effectiveness is not None:
            if not 0.5 <= effectiveness <= 1.0:
                raise ValueError(
                    f"Thermodynamic Error [{self.name}]: Provided effectiveness ({effectiveness})"
                    f"is out of industrial limits [0.50, 1.00]."
                )
            current_effectiveness= effectiveness
        if inlet_stream.P is None or inlet_stream.h is None:
            raise ValueError(f"[{self.name}] Inlet stream properties (P, h) are not fully defined.")

        fluid= inlet_stream.fluid
        P_in= inlet_stream.P
        h_in= inlet_stream.h
        m_dot= getattr(inlet_stream, "m_dot", 1.0)

        # Determine target outlet pressure based on user specification (P_out or delta_P)
        if P_out is not None:
            target_P= P_out
        elif delta_P is not None:
            target_P= P_in- delta_P
        else:
            target_P= P_in # Defualt to isobaric process if neither is specified

        # Constraint 1: Enforce physical pressure drop limit (P_out <= P_in)
        if target_P > P_in:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: Outlet pressure ({target_P:.1f} Pa)"
                f"cannot be higher than inlet pressure ({P_in:.1f} Pa) in a condenser."
                "Condensers are passive heat rejection devices and can only cause"
                f"pressure drop or operate isobarically (P_out <= P_in)."
            )
        # Costraint 2: Inlet phase validation (Condenser inlet cannot be subcooled liquid)
        try:
            sat_liquid= Stream(name= f"{self.name}_sat_check", fluid=fluid)
            sat_liquid.update_by_Px(P=P_in, x= 0.0)
            if inlet_stream.T is not None and sat_liquid.T is not None :
                if inlet_stream.T < sat_liquid.T:
                    raise ValueError(
                        f"Thermodynamic Error [{self.name}]: Inlet stream temperature"
                        f"({inlet_stream.T - 273.15:.2f}°C) is below the saturation temperature"
                        f"({sat_liquid.T - 273.15:.2f} °C)."
                        " Condenser inlet cannot be subcooled liquid!"
                    )
        except Exception as e:
            if "Thermodynamic Error" in str(e):
                raise e
        # Calculate ideal condensaition state at target pressure (saturated liquid or subcooled)
        try:
            sat_stream= Stream(name=f"{self.name}_sat", fluid=fluid)
            sat_stream.update_by_Px(P= target_P, x=0.0)
            T_sat= sat_stream.T
            h_sat_liquid= sat_stream.h

            if target_subcooling > 0.0:
                subcooled_stream = Stream(name=f"{self.name}_subcooled", fluid= fluid)
                subcooled_stream.update_by_PT(P= target_P, T= T_sat - target_subcooling)
                h_ideal_out= subcooled_stream.h
            else:
                h_ideal_out= h_sat_liquid
        except Exception as e:
            raise ValueError(f"[{self.name}] Stream calculation failed for ideal state: {str(e)}")

        # Validate that inlet enthalpy is higher than the ideal condensation enthalpy
        if h_in <= h_ideal_out:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: Inlet enthalpy"
                f" ({h_in / 1000.0:.2f} kJ/kg)"
                "is already lower than or equal to the ideal condensation enthalpy"
                f" ({h_ideal_out / 1000.0:.2f} kJ/kg)."
            )

        # 1. Maximum possible enthalpy drop (delta_h_max) from inlet to ideal state
        delta_h_max= h_in - h_ideal_out
        # 2. Actual enthalpy drop computed via component effectiveness
        delta_h_actual= current_effectiveness * delta_h_max
        # 3. Real outlet enthalpy
        h_out= h_in- delta_h_actual
        # 4. Total heat transfer rate (Q_dot < 0) for heat rejection in condenser
        self.Q_dot= m_dot* (h_out - h_in)
        self.W_dot= 0.0
        # Enforce Second Law / Enthalpy reduction check
        if h_out >= h_in:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: Outlet enthalpy ({h_out/1000.0:.2f} kJ/kg)"
                f"cannot be greater than or equal to inlet enthalpy ({h_in/1000.0:.2f} kJ/kg)"
            )

        # Creat and update outlet stream object
        outlet_stream= Stream(name=f"{inlet_stream.name}_outlet", fluid=fluid)
        outlet_stream.update_by_Ph(P=target_P, h= h_out, m_dot=m_dot)

        return outlet_stream

    def calculate(self, *args, **kwargs):
        """Alias for run method to ensure structural compatibility with solvers."""
        return self.run(*args, **kwargs)
