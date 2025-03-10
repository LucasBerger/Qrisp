from base_qrisp_circuits import QrispCircuit
from qrisp import QuantumSession, QuantumBool, auto_uncompute, z, mcx, x
import sympy as sp
from sympy.logic.utilities.dimacs import load_file

from qrisp.algorithms.grover.grover_tools import grovers_alg


def invert_bitstring(bs: str) -> str:
    """Invert a bitstring (e.g., '0010' -> '1101')."""
    return ''.join('1' if c == '0' else '0' for c in bs)

@auto_uncompute
def oracle(input_qbls, logical_expr=None):
    """Oracle function for the SAT solver."""
    # Evaluate logical expression
    temp = q_eval_bl_expression(logical_expr, input_qbls)
    # Perform phase tag
    z(temp)

def q_eval_bl_expression(expr, qbls):
    """Evaluate a boolean logic expression using quantum operations."""
    # If the expression is a symbol, return the associated QuantumBool
    if isinstance(expr, sp.Symbol):
        for qbl in qbls:
            if qbl.name == expr.name:
                return qbl
        raise Exception(f"Could not find {expr.name} in given QuantumBool list.")

    # Prepare the list of arguments as QuantumBools
    qbools = []
    ctrl_state = ""

    for arg in expr.args:
        if isinstance(arg, sp.Not):
            subexpr = arg.args[0]
            ctrl_state += "0"
        else:
            subexpr = arg
            ctrl_state += "1"

        qbools.append(q_eval_bl_expression(subexpr, qbls))

    # Evaluate the logic
    res = QuantumBool()

    if isinstance(expr, sp.And):
        mcx(qbools, res, ctrl_state=ctrl_state, method="balauca")
    elif isinstance(expr, sp.Or):
        mcx(qbools, res, ctrl_state=invert_bitstring(ctrl_state), method="balauca")
        x(res)
    else:
        raise Exception(f"Unsupported expression type: {type(expr)}")

    return res

class SATCircuit(QrispCircuit):
    """Implementation of a SAT solver circuit using Qrisp."""
    
    def __init__(self, dimacs_path: str, name: str):
        """
        Initialize SAT solver circuit.
        
        Parameters
        ----------
        dimacs_path : str
            Path to the DIMACS format file representing the SAT problem
        name : str
            Name of the SAT instance for identification
        """
        self._dimacs = load_file(dimacs_path)
        self._logical_expr = self._dimacs
        self._free_symbols = list(self._logical_expr.free_symbols)
        self._name = name
        
    def name(self) -> str:
        """Return the name of the circuit."""
        return f"SAT_{self._name}"
    
    def create_session(self) -> QuantumSession:
        """
        Create a SAT solver circuit.
        
        Returns
        -------
        QuantumSession
            Quantum session containing the SAT solver circuit
        """
        # Create quantum boolean variables
        qbls = [QuantumBool(name=symb.name) for symb in self._free_symbols]
        
        # Apply Grover's algorithm without measurement
        grovers_alg(qbls, oracle, kwargs={"logical_expr": self._logical_expr})
        
        return qbls[0].qs 