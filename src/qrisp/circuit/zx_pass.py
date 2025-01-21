from pytket import Circuit as PyTketCircuit
from pytket.passes import (
    RebaseCustom,
    DecomposeBoxes
)
import pyzx as zx
from pytket.circuit import OpType, Qubit as TketQubit
from qrisp.circuit import QuantumCircuit, Qubit, Operation, Instruction
from qrisp.circuit.operation import ControlledOperation
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
    logger.debug("ZX pass")
    logger.debug(f"Circuit contains {len(qc.data)} operations")
    
    # Remove any global phase gates
    qc_new = qc.clearcopy()
    for instr in qc.data:
        if instr.op.name != "gphase":
            qc_new.append(instr)
    qc = qc_new

    # Split circuit into segments
    segments = []
    current_segment = qc.clearcopy()
    
    for instr in qc.data:
        op = instr.op
        # Check if this is a complex gate that should be boxed
        is_complex = False
        
        # Case 1: Controlled operation with definition
        if issubclass(op.__class__, ControlledOperation) and op.definition:
            is_complex = True
            
        # Case 2: Non-standard gate with definition
        elif (op.name not in ["rxx", "rzz", "ryy", "measure", "swap", "h", "p", "x", "y", "z", 
                            "rx", "ry", "rz", "s", "s_dg", "t", "t_dg", "u3", "gphase", "cx", 
                            "cy", "cz", "cp", "sx", "sx_dg", "u1", "id", "qb_alloc", "qb_dealloc"]) and op.definition:
            is_complex = True
            
        if is_complex:
            # If current segment has operations, add it to segments
            if len(current_segment.data) > 0:
                segments.append(current_segment)
            # Add complex gate as its own segment
            complex_segment = qc.clearcopy()
            complex_segment.append(instr)
            segments.append(complex_segment)
            # Start new segment
            current_segment = qc.clearcopy()
        else:
            current_segment.append(instr)
    
    # Add final segment if it has operations
    if len(current_segment.data) > 0:
        segments.append(current_segment)
    
    # Process each segment
    result_qc = qc.clearcopy()
    
    # Add QubitAlloc instructions for all qubits first
    for qubit in qc.qubits:
        result_qc.append(QubitAlloc(), [qubit])
    
    for segment in segments:
        if len(segment.data) == 1 and segment.data[0].op.definition and (
            issubclass(segment.data[0].op.__class__, ControlledOperation) or 
            segment.data[0].op.name not in ["rxx", "rzz", "ryy", "measure", "swap", "h", "p", "x", "y", "z", 
                                          "rx", "ry", "rz", "s", "s_dg", "t", "t_dg", "u3", "gphase", "cx",
                                          "cy", "cz", "cp", "sx", "sx_dg", "u1", "id", "qb_alloc", "qb_dealloc"]):
            # Complex gate segment - keep as is
            result_qc.append(segment.data[0])
        else:
            # Regular segment - apply ZX optimization
            tket_qc = segment.to_pytket()
            
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
            
            # Convert optimized segment back to Qrisp circuit
            optimized_segment = QuantumCircuit.from_qiskit(qiskit_cir)
            
            # Map qubits back to original qubits
            qubit_map = {}
            for optimized_qubit in optimized_segment.qubits:
                for original_qubit in segment.qubits:
                    if optimized_qubit.identifier == original_qubit.identifier or optimized_qubit.identifier + ".0" == original_qubit.identifier:
                        qubit_map[optimized_qubit] = original_qubit
                        break
            
            # Add optimized operations to result circuit
            for instr in optimized_segment.data:
                mapped_qubits = [qubit_map[q] for q in instr.qubits]
                result_qc.append(instr.op, mapped_qubits)
    
    return result_qc


