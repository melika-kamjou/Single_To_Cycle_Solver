"""Backend thermodynamic module for the industrial flash tank component.
This module handles mass and energy balances, phase-split flash evaluations,
and distinct vapor/liquid stream extraction.
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

class FlashTank(BaseComponent):
    """
    Industrial Flash Tank (Separator Drum) component.
    Industrial & Thermodynamic Constraints:
        1. Mass Balance: m_dot_in = m_dot_vapor + m_dot_liquid
        2. Global Energy Balance (Isenthalpic flash): m_in * h_in = m_vap * h_g + m_liq * h_f
        3. Pressure Constraint: P_flash must be strictly less than 
        inlet pressure (P_inlet) to induce flashing.
        4.Phase Quality Limits (0.0 <= x <= 1.0):
            - Vapor outlet stream is evaluated as the vapor phase at P_flash.
            - Liquid outlet stream is evaluated as the liquid phase at P_flash.
    """
    def __init__(self,name:str):
        super().__init__(name)
        self.vapor_outlet= None
        self.liquid_outlet= None
        self.x_flash= 0.0

    def run(self, inlet_stream: Stream, P_flash: float=None, delta_P: float= None):
        """Execute thermodynamic simulation and phase-split evaluation for the flash tank.
        Args:
            inlet_stream (Stream): The incoming feed stream object entering the flash tank.
            P_flash (float, optional): Target flash drum operating 
            pressure in Pascals. Defaults to None.
            delta_P (float, optional): Pressure drop across 
            the component in Pascals. Defaults to None.
        Returns:
            dict: A dictionary containing the separation results and optional metrics:
                _"vapor_outlet" (Stream): The vapor phase stream leaving the top of 
                the drum[span_1](start_span)[span_1](end_span).
                _"liquid_outlet" (Stream): The liquid phase stream leaving the bottom of 
                the drum[span_1](start_span)[span_2](end_span).
                _"vapor_quality" (float): The evaluated flash vapor quality (x).
                _"m_vapor" (float): Mass flow rate of the vapor product.
                _"m_liquid" (float): Mass flow rate of the liquid product.
        Raises:
            ValueError: If the inlet strem is missing, required stream properties
            are undefined, or flash pressure constraints are violated.
            """
        if inlet_stream is None:
            raise ValueError(f"[{self.name}] Inlet stream is required.")

        if inlet_stream.P is None or inlet_stream.h is None:
            raise ValueError(f"[{self.name}] Inlet stream properties"
                             "(P, h, m_dot) are not fully defined.")

        # Determine flash operating pressure with exact variable naming consistency
        p_out= None
        if P_flash is not None:
            p_out= P_flash
        if delta_P is None:
            delta_P= 0.0
        elif delta_P is not None:
            p_out = inlet_stream.P - delta_P
        if p_out is None:
            p_out= inlet_stream.P - (delta_P if delta_P is not None else 0.0)

        #Industrial Constraint 1: Pressure validation
        if p_out <= 0:
            raise ValueError(f"Thermodynamic Error [{self.name}] Industrial Error:"
                             f"Flash pressure ({p_out} Pa) cannot be zero or negative.")

        if p_out >= inlet_stream.P:
            raise ValueError(
                f"Thermodynamic Error [{self.name}]: Flash pressure ({p_out:.1f} Pa)"
                f"must be strictly lower than inlet stream pressure ({inlet_stream.P:.1f} Pa)"
                f"to induce phase separation (flashing)."
            )

        # Step 1: Perform flash state evaluation at P_out using inlet enthalpy
        # (isenthalpic expansion)
        flash_stream= Stream(name= f"{inlet_stream.name}_flash_state",
                             fluid= inlet_stream.fluid)
        flash_stream.update_by_Ph(P=p_out, h= inlet_stream.h, m_dot= inlet_stream.m_dot)

        # Extract vapor qualitty (x)
        x= getattr(flash_stream, "x", None)

        # Industrial Constraint 2: Robust phase boundary clamping
        if x is None:
            x = 0.0

        if x < 0.0:
            x= 0.0
        elif x > 1.0:
            x = 1.0

        self.x_flash= x
        m_in= inlet_stream.m_dot
        m_vapor = m_in * x
        m_liquid= m_in * (1.0 - x)

        # Step 2: Extract distinct phase enthalpies safely from
        #the flash evaluation or stream attributes
        h_vap_val= getattr(flash_stream, "h_vap",
                           getattr(flash_stream, "h", inlet_stream.h))
        h_liq_val= getattr(flash_stream, "h_liq",
                           getattr(flash_stream, "h", inlet_stream.h))
        #1. Vapor Outlet Stream (Top of the drum)
        self.vapor_outlet= Stream(name=f"{self.name}_vapor_outlet",
                                  fluid= inlet_stream.fluid)
        self.vapor_outlet.update_by_Ph(
            P= p_out,
            h= h_vap_val if x > 0 else inlet_stream.h,
            m_dot= m_vapor
        )

        #2. Liquid Outlet Stream (Bottom of the drum)
        self.liquid_outlet= Stream(name= f"{self.name}_liquid_outlet",
                                   fluid=inlet_stream.fluid)
        self.liquid_outlet.update_by_Ph(
            P= p_out,
            h= h_liq_val if x < 1 else inlet_stream.h,
            m_dot= m_liquid
        )
        return{
            "vapor_outlet": self.vapor_outlet,
            "liquid_outlet": self.liquid_outlet,
            "vapor_quality": self.x_flash,
            "m_vapor": m_vapor,
            "m_liquid": m_liquid,
   }

    def calculate(self, *args, **kwargs):
        """Alias for run method to ensure structural compatibility with solvers."""
        return self.run(*args, **kwargs)
