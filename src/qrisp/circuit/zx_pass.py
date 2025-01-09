from pytket import Circuit as PyTketCircuit
from pytket.passes import (
    RebaseCustom,
    DecomposeBoxes
)
import pyzx as zx
from pytket.circuit import OpType, Qubit as TketQubit
from qrisp.circuit import QuantumCircuit, Qubit, Operation, Instruction
from qrisp.circuit.standard_operations import QubitAlloc
from pytket.extensions.qiskit import tk_to_qiskit
from pytket.extensions.pyzx import pyzx_to_tk, tk_to_pyzx
from contextlib import contextmanager
import logging
from dataclasses import dataclass
from typing import Generator
logger = logging.getLogger(__name__)

@dataclass
class CircuitContainer:
    """Container for circuit that can be modified within context."""
    circuit: PyTketCircuit
    
    def update(self, new_circuit: PyTketCircuit):
        """Update the contained circuit."""
        self.circuit = new_circuit

@contextmanager
def simplified_circuit(tket_qc: CircuitContainer) -> Generator[CircuitContainer, None, None]:
    """
    Context manager for handling circuit simplification and restoration.
    
    Parameters
    ----------
    tket_qc : PyTketCircuit
        The original tket circuit with complex registers
        
    Yields
    ------
    tuple
        (circuit_container, qubit_map, original_registers)
        - circuit_container: Container holding the simplified circuit
        - qubit_map: Dictionary mapping original qubits to simple qubits
        - original_registers: List of original quantum registers
    """
    try:
        # Store original structure
        original_registers = [qr.__copy__() for qr in tket_qc.circuit.q_registers]
        original_qubits = [qb for qr in original_registers for qb in qr.to_list()]
        qubit_map = {}
        
        # Create simplified circuit
        simple_qc = PyTketCircuit(len(tket_qc.circuit.qubits))
        
        # Create mapping
        for i, qb in enumerate(original_qubits):
            new_qb = TketQubit('q', i)
            qubit_map[qb] = new_qb
        
        # Copy commands with remapped qubits
        for cmd in tket_qc.circuit.get_commands():
            new_qubits = [qubit_map[qb] for qb in cmd.qubits]
            simple_qc.add_gate(cmd.op, new_qubits)
        
        # Create container for the circuit
        container = CircuitContainer(simple_qc)
        
        yield container
        
        # After yield, restore the circuit using the potentially modified circuit
        # Create reverse mapping
        reverse_map = {v: k for k, v in qubit_map.items()}
        
        # Create new circuit with original structure
        final_qc = PyTketCircuit()
        
        # Restore original registers
        for qr in original_registers:
            final_qc.add_q_register(qr)
        
        # Copy commands with original qubit names
        for cmd in container.circuit.get_commands():
            original_qubits = [reverse_map[qb] for qb in cmd.qubits]
            final_qc.add_gate(cmd.op, original_qubits)
        
        # Update the input circuit
        tket_qc.update(final_qc)
        
    finally:
        logger.debug("Exiting simplified circuit context")

def zx_pass(qc: QuantumCircuit):
    logger.info("ZX pass")
    logger.info(f"Circuit contains {len(qc.data)} operations")
    
    # Remove any global phase gates
    qc_new = qc.clearcopy()
    for instr in qc.data:
        if instr.op.name != "gphase":
            qc_new.append(instr)
    qc = qc_new
    
    tket_qc: PyTketCircuit = qc.to_pytket()
    
    logger.debug(f"To-Be-Transpiled circuit contains {len(tket_qc.qubits)} qubits and {len(tket_qc.bits)} classical bits")
    logger.debug(f"To-Be-Transpiled circuit contains {len(tket_qc.get_commands())} operations")
    
    # First decompose any custom boxes
    DecomposeBoxes().apply(tket_qc)
    
    # Define allowed gates and replacements
    allowed_gates = {
        OpType.noop, OpType.X,
        OpType.CX, OpType.SWAP, OpType.H,
        OpType.Z, OpType.Rz, OpType.CZ
    }
    
    # Create a simple CX circuit for testing
    cx_circ = PyTketCircuit(2)
    cx_circ.CX(0,1)
    
    def sq(a, b, c):
        circ = PyTketCircuit(1)
        if c != 0:
            circ.Rz(c, 0)
        circ.H(0)
        if b != 0:
            circ.Rz(b, 0)
        circ.H(0)
        if a != 0:
            circ.Rz(a, 0)
        return circ
    
    # Create rebase pass with replacements
    rebase = RebaseCustom(
        allowed_gates,
        cx_replacement=cx_circ,
        tk1_replacement=sq
    )
    
    # Apply rebasing
    rebase.apply(tket_qc)
    
    container = CircuitContainer(tket_qc)
    
    # Use context manager for circuit simplification
    with simplified_circuit(container) as circuit_container:
        # Apply ZX optimization
        try:
            zx_diagram = tk_to_pyzx(circuit_container.circuit)
            graph = zx_diagram.to_graph()
            zx.full_reduce(graph, quiet=True)
            graph.normalize()
            zx_diagram = zx.extract_circuit(graph.copy())
            optimized_qc = pyzx_to_tk(zx_diagram)
            
            # Update the circuit in the container
            circuit_container.update(optimized_qc)
            
        except Exception as e:
            logger.error(f"Error applying pyzx transformation: {e}")
            raise e
    
    # tket_qc is now automatically restored with the optimized circuit
    tket_qc = container.circuit
    
    qiskit_cir = tk_to_qiskit(tket_qc)
    
    logger.debug(f"Qiskit circuit contains {len(qiskit_cir.qubits)} qubits and {len(qiskit_cir.clbits)} classical bits")
    logger.debug(f"Qiskit circuit contains {len(qiskit_cir.data)} operations")
    
    # Store original qubits for reference
    original_qubits: list[Qubit] = qc.qubits
    
    # Create empty copy of original circuit
    result_qc = qc.clearcopy()
    
    transpiled_qc = QuantumCircuit.from_qiskit(qiskit_cir)
    
    # Map transpiled qubits back to original qubits by name
    qubit_map = {}
    for transpiled_qubit in transpiled_qc.qubits:
        tr_qubit: Qubit = transpiled_qubit
        # Find original qubit with matching name
        for original_qubit in original_qubits:
            if tr_qubit.identifier == original_qubit.identifier:
                qubit_map[transpiled_qubit] = original_qubit
                break
            
    for qubit in original_qubits:
        result_qc.append(QubitAlloc(), [qubit])
    
    # Transfer instructions using original qubit references
    for instr in transpiled_qc.data:
        instruction: Instruction = instr
        operation: Operation = instruction.op
        mapped_qubits = [qubit_map[q] for q in instruction.qubits]
        result_qc.append(operation, mapped_qubits)
    
    logger.info(f"Transpiled circuit contains {len(transpiled_qc.qubits)} qubits and {len(transpiled_qc.clbits)} classical bits")
    logger.info(f"Transpiled circuit contains {len(transpiled_qc.data)} operations")
    
    return result_qc


