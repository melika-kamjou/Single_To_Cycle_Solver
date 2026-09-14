"""Backend thermodynamic model for the Stream Splitter equipment.
Handles mass and adiabatic energy balances, as well as constant pressure splitting.
"""
import os
import sys
from base_component import BaseComponent
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..",".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

class Splitter(BaseComponent):
    """
    Industrial Stream Splitter Component.
    Thermodynamic & Industrial constraints:
        1.Mass balance: m_dot_in = sum(m_dot_i)
        2.Energy balance (Adiabatic): Enthalpy remains constant across
            all split outlets sum(m_dot_i * (h_out_i))= h_in * m_dot_in
        3.Pressure constraint:
            Outlet pressures match the inlet pressure (P_out_i = P_in)
    """
    def __init__(self, name:str):
        super().__init__(name)
        self.Q_dot= 0.0
        self.W_dot= 0.0
        self.outlet_streams= []

    def run(self, inlet_stream: Stream, split_ratios: list):
        """
        Executes the stream splitting simulation based on given mass flow ratios.
        Parameters:
            inlet_stream (Stream): The incoming main stream object.
            split_ratios (list): List of fractional ratios for each outlet (must sum to 1.0).
        Returns:
            list of Streams: A list of generated outlet stream objects.
        Raises:
            ValueError: If  inlet stream is missing, fewer than two ratios are provided,
            ratios do not sum to 1.0, or inlet properties are undefined.
        """
        if inlet_stream is None:
            raise ValueError(f"[{self.name}] Splitter requires a valid inlet stream.")
        if not split_ratios or len(split_ratios) < 2:
            raise ValueError(f"[{self.name}] Splitter "
                             "requires at least 2 outlet split fractions.")

        total_ratio= sum(split_ratios)
        if round(total_ratio, 2) != 1.0:
            raise ValueError(f"[{self.name}] Split ratios must sum up "
                             f"to 1.0 (current sum: {total_ratio}).")

        if inlet_stream.P is None or inlet_stream.h is None or inlet_stream.m_dot is None:
            raise ValueError(f"[{self.name}] Inlet stream propetrties"
                             " (P, h, m_dot) are not fully defined.")

        self.outlet_streams= []
        for idx, ratio in enumerate(split_ratios):
            m_dot_out= inlet_stream.m_dot* ratio
            outlet= Stream(name=f"{self.name}_outlet_{idx+1}",
                           fluid=inlet_stream.fluid)
            outlet.update_by_Ph(P=inlet_stream.P, h= inlet_stream.h,
                                m_dot=m_dot_out)
            self.outlet_streams.append(outlet)
        return self.outlet_streams

    def calculation(self, *args, **kwargs):
        """Alias for run method to ensure structural compatibility with solvers."""
        return self.run(*args, **kwargs)
