from abc import ABC, abstractmethod
from qrisp import QuantumSession

class QrispCircuit(ABC):
    """Abstract base class defining the interface for Qrisp circuit implementations."""
    
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the circuit.
        
        Returns
        -------
        str
            The name of the circuit implementation
        """
        pass
    
    @abstractmethod
    def create_session(self) -> QuantumSession:
        """
        Create and return a quantum circuit implemented in Qrisp.
        
        Returns
        -------
        QuantumSession
            The quantum session containing the implemented circuit
        """
        pass
