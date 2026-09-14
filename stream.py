"""Thermodynamic stream module using CoolProp for property evaluations."""
# pylint: disable=invalid-name
# pylint: disable= too-many-arguments
# pylint: disable=invalid-name, too-many-instance-attributes

from CoolProp.CoolProp import PropsSI

class Stream:
    """Represent a thrmodynamic stream contaning physical properties
    
    and flow rates, evaluated using CoolProp.
    """
    def __init__(self, name: str, fluid: str, m_dot: float= None,V_dot: float= None,P: float= None,
            T: float= None,h: float= None, s: float= None,x: float= None):
        """Initialize the thermodynamic stream."""
        self.fluid= fluid
        self.name= name
        self.m_dot= m_dot  #Mass flow rate [kg/s]
        self.V_dot= V_dot  #Volumetric flow rate [m^3/s]
        # Thermodynamic State Variables
        self.P= P  # Pressure [Pa]
        self.T= T  # Temperature [K]
        self.h= h  # Specific Enthalpy [J/kg]
        self.s= s  # Specific Entropy [J/kg.K]
        self.rho= None  #Density [kg/m^3]
        self.x= x  # Vapor Quality [-] (0 to 1 within dom, -1 inside)
        self.cp= None
    def _update_flow_rates(self):
        """Internal method to synchronize mass and volumetric flow rates
        
        using the calculated thermodynamic density.
        """
        if self.rho is not None and self.rho>0:
            if self.m_dot is not None and self.V_dot is None:
                self.V_dot= self.m_dot/self.rho
            elif self.V_dot is not None and self.m_dot is None:
                self.m_dot= self.V_dot*self.rho
    def _calc_properties(self, prop1_name: str, prop1_val: float,
                         prop2_name: str, prop2_val: float):
        """Internal helper to fetch all thermodynamic properties from CoolProp."""
        self.P= PropsSI("P", prop1_name, prop1_val, prop2_name, prop2_val, self.fluid)
        self.T= PropsSI("T", prop1_name, prop1_val, prop2_name, prop2_val, self.fluid)
        self.h= PropsSI("H", prop1_name, prop1_val, prop2_name, prop2_val, self.fluid)
        self.s= PropsSI("S", prop1_name, prop1_val, prop2_name, prop2_val, self.fluid)
        self.rho= PropsSI("D", prop1_name, prop1_val, prop2_name, prop2_val, self.fluid)
        self.cp= PropsSI("Cpmass", prop1_name, prop1_val, prop2_name,prop2_val, self.fluid)
        # CoolProp throws an error if quality (Q) is requested sor single_phase states
        try:
            self.x= PropsSI("Q", prop1_name,prop1_val,prop2_name,prop2_val, self.fluid)
        except ValueError:
            # For single_phase (subcooled liquid or superheated vapor), quality is not applicable
            self.x= -1.0
        # Synchroniz flow rates once density is known
        self._update_flow_rates()
    def update_by_PT(self, P: float, T:float,m_dot: float = None, V_dot : float = None):
        """ Update stream state using Peressure [Pa] and Temprature [K]."""
        if m_dot is not None:
            self.m_dot= m_dot
        if V_dot is not None:
            self.V_dot= V_dot
        self._calc_properties('P', P,'T', T)
    def update_by_Ps (self, P: float, s: float, m_dot: float= None, V_dot: float =None):
        """ Update stream state using pressure [Pa] and Specific Entropy [J/kg.K]."""
        if m_dot is not None:
            self.m_dot= m_dot
        if V_dot is not None:
            self.V_dot= V_dot
        self._calc_properties('P',P,'S',s)
    def update_by_Ph(self, P: float, h: float, m_dot: float= None, V_dot: float= None):
        """ Update stream state using pressure [Pa] and Spcific Enthalpy [J/kg]."""
        if m_dot is not None:
            self.m_dot= m_dot
        if V_dot is not None:
            self.V_dot= V_dot
        self._calc_properties("P",P,'H',h)
    def update_by_Px(self, P: float, x: float, m_dot: float= None, V_dot: float= None):
        """Update syream state using pressure [Pa] and Vapor Quality x [0 to 1]."""
        if m_dot is not None:
            self.m_dot= m_dot
        if V_dot is not None:
            self.V_dot= V_dot
        self._calc_properties('P', P, 'Q', x)
    def __repr__(self) -> str:
        """Formatted diplay of the stream properties."""
        P_bar= self.P/1e5 if self.P else 0
        t_c= self.T -273.15 if self.T else 0
        h_kj= self.h /1e3 if self.h else 0
        s_kj= self.s/1e3 if self.s else 0
        v_dot_lps= (self.V_dot*1000) if self.V_dot else 0
        return (
            f"---Stream({self.fluid})---\n"
            f"  m_dot : {self.m_dot:.4f} kg/s \n"
            f"  V_dot : {v_dot_lps:.6f} L/s \n"
            f"  rho : {self.rho:.2f} kg/m^3 \n"
            f"  P : {P_bar:.2f} bar \n"
            f"  T : {t_c:2f} \u00b0C \n"
            f"  h : {h_kj:.2f} kJ/kg \n"
            f"  s : {s_kj:.4f} kJ/kg.K \n"
            f"  x : {self.x} \n"
        )
