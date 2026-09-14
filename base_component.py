"""Base component module for thermodynamic equipment systems."""
# pylint: disable=invalid-name
# pylint: disable= too-few-public-methods
class BaseComponent:
    """Base class for all thermodynamic component in the system."""
    def __init__(self, name: str):
        self.name= name
        self.W_dot= 0.0 #Power produced (+) or consumed (-) in kW
        self.Q_dot= 0.0 # Heat added (+) or removed (-) in kW
        self.eta_s = None #Isentropic efficiency (0 to 1.0)
    def __repr__(self) -> str:
        return(
            f"<{self.__class__.__name__}: {self.name} |"
            f" Work: {self.W_dot:.2f} kW | Heat: {self.Q_dot:.2f} kW>"
        )
