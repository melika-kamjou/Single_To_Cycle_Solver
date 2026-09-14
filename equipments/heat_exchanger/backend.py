"""Backend thermodynamic module for the industrial heat exchanger component.
This module handles energy balances, effectiveness calculations,
and distinct hot/cold stream extractions for heat exchanfer.
"""
#pylint: disable= invalid-name, too-many-arguments
import os
import sys
from base_component import BaseComponent
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..",".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

class HeatExchanger(BaseComponent):
    """
    Industrial Heat Exchanger Component (Recuperator / HX).
    Thermodynamic & Industrial constraints:
        1. Mass balance: m_hot_out = m_hot_in , m_cold_out= m_cold_in
        2. Energy balance: Q= m_hot * (h_hot_in - h_hot_out) = 
        m_cold * (h_cold_out - h_cold_in)
        3. Effectiveness model: Q= effectiveness * Q_max
    """
    def __init__(self, name: str, effectiveness: float= 0.80):
        super().__init__(name)
        if not 0.1 <= effectiveness <= 1.0:
            raise ValueError(f"[{self.name}] Heat exchanger effectiveness must"
                             " be between 0.1 and 1.0.")
        self.effectiveness= effectiveness
        self.Q_dot= 0.0
        self.hot_outlet_stream= None
        self.cold_outlet_stream= None

    def run(self, hot_inlet: Stream, cold_inlet: Stream,
            Q_specified: float=None, P_drop_hot: float=0.0,
            P_drop_cold: float=0.0):
        """Execute thermodynamic simulation and heat exchanger for the heat exchanger.
        Args:
            hot_inlet (Stream): The hot inlet stream object entering the HX.
            cold_inlet (Stream): The cold inlet stream object entering the HX.
            Q_specified (float, optional): Specified heat transfer rate in Watts.
            Defaults to None.
            P_drop_hot (float, optional): Pressure drop for the hot side in Pascals.
            Defaults to 0.0.
            P_drop_cold (float, optional): Pressure drop for the cold side in Pascals.
            Deafaults to 0.0.
        Returns:
            tuple: A tuple containing (hot_outlet_stream, cold_outlet_stream).
        Raises:
            ValueError: If either inlet stream is missing, properties are undefined,
            temperature constraints are violated, or outlet pressures are invalid.
            """
        if hot_inlet is None or cold_inlet is None:
            raise ValueError(f"[{self.name}] Heat Exchanger"
                             "requires both hot and cold inlet streams.")

        if hot_inlet.P is None or hot_inlet.h is None or hot_inlet.m_dot is None:
            raise ValueError(f"[{self.name}] Hot inlet stream"
                             " properties are not fully defined.")
        if cold_inlet.P is None or cold_inlet.h is None or cold_inlet.m_dot is None:
            raise ValueError(f"[{self.name}] Cold inlet stream"
                             " properties are not fully defined.")

        if hot_inlet.T <= cold_inlet.T:
            raise ValueError(f"[{self.name}] Hot inlet temperature"
                             " must be higher than cold inlet temperature.")

        # Calculate heat transfer rate (Q_dot)
        if Q_specified is not None:
            self.Q_dot= Q_specified
        else:
            C_hot= hot_inlet.m_dot * hot_inlet.cp
            C_cold= cold_inlet.m_dot * cold_inlet.cp
            C_min= min(C_hot, C_cold)

            delta_T_max= hot_inlet.T - cold_inlet.T
            Q_max= C_min * delta_T_max
            self.Q_dot= self.effectiveness* Q_max

        # Enthalpy calculations
        h_hot_out= hot_inlet.h - (self.Q_dot / hot_inlet.m_dot)
        h_cold_out= cold_inlet.h + (self.Q_dot / cold_inlet.m_dot)

        # Pressure drops
        P_hot_out= hot_inlet.P - P_drop_hot
        P_cold_out= cold_inlet.P - P_drop_cold

        if P_hot_out <= 0 or P_cold_out <= 0:
            raise ValueError(f"[{self.name}] Outlet pressures cannot be zero or negative.")

        # Creat outlet streams
        self.hot_outlet_stream= Stream(name= f"{self.name}_hot_outlet",
                                       fluid=hot_inlet.fluid)
        self.hot_outlet_stream.update_by_Ph(P=P_hot_out, h= h_hot_out,
                                            m_dot=hot_inlet.m_dot)

        self.cold_outlet_stream= Stream(name= f"{self.name}_cold_outlet",
                                        fluid=cold_inlet.fluid)
        self.cold_outlet_stream.update_by_Ph(P=P_cold_out, h= h_cold_out,
                                             m_dot=cold_inlet.m_dot)

        return self.hot_outlet_stream, self.cold_outlet_stream
    def calculate(self, *args, **kwargs):
        """Alias for run method to ensure structural compatibility with solvers."""
        return self.run(*args, **kwargs)
