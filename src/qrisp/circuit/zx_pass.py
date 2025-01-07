from pytket import Circuit as PyTketCircuit
from pytket.passes import (
    ZXGraphlikeOptimisation, 
    RebaseCustom,
    DecomposeBoxes, 
    FullPeepholeOptimise,
    RemoveRedundancies
)
from pytket.circuit import OpType
from qrisp.circuit import QuantumCircuit, Qubit, Operation, Instruction
from qrisp.circuit.standard_operations import QubitAlloc
from pytket.extensions.qiskit import tk_to_qiskit
import logging

logger = logging.getLogger(__name__)

def zx_pass(qc: QuantumCircuit):
    logger.info("ZX pass")
    if len(qc.clbits) > 0:
        logger.info("Circuit contains classical bits")
        return qc
    logger.info(f"Circuit contains {len(qc.data)} operations")
    # logger.info(f"Circuit contains {qc.cnot_count()} CNOTs")
    # logger.info(f"Circuit contains {qc.t_depth()} T depth")
    
    tket_qc: PyTketCircuit = qc.to_pytket()
    
    logger.debug(f"To-Be-Transpiled circuit contains {len(tket_qc.qubits)} qubits and {len(tket_qc.bits)} classical bits")
    logger.debug(f"To-Be-Transpiled circuit contains {len(tket_qc.get_commands())} operations")
    
    # First decompose any custom boxes
    DecomposeBoxes().apply(tket_qc)
    
    # Define allowed gates and replacements
    allowed_gates = {
        OpType.noop, OpType.Rx, OpType.X,
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
        if b != 0:
            circ.Rx(b, 0)
        if a != 0:
            circ.Rz(a, 0)
        return circ
    
    # Create rebase pass with replacements
    rebase = RebaseCustom(
        allowed_gates,
        cx_replacement=cx_circ,  # Use CX directly
        tk1_replacement=sq  # Standard Euler decomposition
    )
    
    # Apply rebasing
    rebase.apply(tket_qc)
    logger.debug(f"After Rebase circuit contains {len(tket_qc.qubits)} qubits and {len(tket_qc.bits)} classical bits")
    logger.debug(f"After Rebase circuit contains {len(tket_qc.get_commands())} operations")
    
    # # Now we can apply ZX optimization
    ZXGraphlikeOptimisation().apply(tket_qc)
    logger.debug(f"After ZXGraphlikeOptimisation circuit contains {len(tket_qc.qubits)} qubits and {len(tket_qc.bits)} classical bits")
    logger.debug(f"After ZXGraphlikeOptimisation circuit contains {len(tket_qc.get_commands())} operations")
    
    # # Final cleanup and optimization
    RemoveRedundancies().apply(tket_qc)
    logger.debug(f"After RemoveRedundancies circuit contains {len(tket_qc.qubits)} qubits and {len(tket_qc.bits)} classical bits")
    logger.debug(f"After RemoveRedundancies circuit contains {len(tket_qc.get_commands())} operations")
        
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
    # logger.info(f"Transpiled circuit contains {transpiled_qc.cnot_count()} CNOTs")
    # logger.info(f"Transpiled circuit contains {transpiled_qc.t_depth()} T depth")
        
    
    return result_qc


