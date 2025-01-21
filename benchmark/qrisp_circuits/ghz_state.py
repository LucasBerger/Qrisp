from base_qrisp_circuits import QrispCircuit
from qrisp.core.gate_application_functions import cx, h
from qrisp.core.quantum_session import QuantumSession
from qrisp.core.quantum_variable import QuantumVariable

class GHZCircuit(QrispCircuit):
    """Implementation of a GHZ state circuit using Qrisp."""
    
    def __init__(self, num_qubits: int = 3):
        """
        Initialize GHZ circuit.
        
        Parameters
        ----------
        num_qubits : int, default=3
            Number of qubits in the GHZ state
        """
        if num_qubits < 2:
            raise ValueError("GHZ state requires at least 2 qubits")
        self._num_qubits = num_qubits
    
    def name(self) -> str:
        """Return the name of the circuit."""
        return f"GHZ-{self._num_qubits}"
    
    def create_session(self) -> QuantumSession:
        """
        Create a GHZ state circuit.
        
        Returns
        -------
        QuantumSession
            Quantum session containing the GHZ state circuit
        """
        # Create a new session and quantum variable
        qv = QuantumVariable(self._num_qubits)
        
        # Apply Hadamard to first qubit
        h(qv[0])
        
        # Apply CNOTs in sequence - first qv[0] controls qv[1], 
        # then qv[0] and qv[1] control qv[2] and qv[3], etc.
        
        # First CNOT from qv[0] to qv[1]
        cx(qv[0], qv[1])
        
        # Then use previous qubits as controls for next layer
        current_qubit = 2
        num_controls = 2  # Start with 2 controls (qv[0] and qv[1])
        
        while current_qubit < self._num_qubits:
            # Use the previous num_controls qubits to control the next ones
            for i in range(num_controls):
                if current_qubit + i < self._num_qubits:
                    cx(qv[i], qv[current_qubit + i])
            
            current_qubit += num_controls
            num_controls *= 2  # Double the number of controls for next iteration
        
        return qv.qs 