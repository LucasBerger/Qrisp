from gurobipy import read
import numpy as np
from qrisp import QuantumArray, QuantumFloat, QuantumVariable, QuantumCircuit, cyclic_shift, h, x
from qrisp.alg_primitives.iterable_processing import demux
from qrisp.algorithms.qaoa import (
    QAOAProblem,
    RX_mixer,
    create_QUBO_cl_cost_function,
    create_QUBO_cost_operator,
)
from qrisp.default_backend import def_backend
from base_qrisp_circuits import QrispCircuit
from qrisp.core.quantum_session import QuantumSession
from qrisp.environments import invert

# Create a function that generates a state of superposition of all permutations
def swap_to_front(qa, index):
    with invert():
        # The keyword ctrl_method = "gray_pt" allows the controlled swaps to be synthesized
        # using Margolus gates. These gates perform the same operation as a regular Toffoli
        # but add a different phase for each input. This phase will not matter though,
        # since it will be reverted once the ancilla values of the oracle are uncomputed.
        demux(qa[0], index, qa, permit_mismatching_size=True)


def eval_perm_old(perm_specifiers, city_amount, qa=None):
    N = len(perm_specifiers)

    # To filter out the cyclic permutations, we impose that the first city is always city 0
    # We will have to consider this assumption later when calculating the route distance
    # by manually adding the trip distance of the first trip (from city 0) and the
    # last trip (to city 0)
    if qa is None:
        qa = QuantumArray(QuantumFloat(int(np.ceil(np.log2(city_amount)))), city_amount)

    add = np.arange(0, city_amount)

    for i in range(city_amount):
        qa[i] += int(add[i])

    for i in range(N):
        swap_to_front(qa[i:], perm_specifiers[i])

    return qa

# Create function that returns QuantumFloats specifying the permutations (these will be in uniform superposition)
def create_perm_specifiers(city_amount, init_seq=None) -> list[QuantumFloat]:
    perm_specifiers = []

    for i in range(city_amount - 1):
        qf_size = int(np.ceil(np.log2(city_amount - i)))

        if i == 0:
            continue

        temp_qf = QuantumFloat(qf_size)

        if not init_seq is None:
            temp_qf[:] = init_seq[i - 1]

        perm_specifiers.append(temp_qf)

    return perm_specifiers

class QUBOCircuit(QrispCircuit):
    """Implementation of a QUBO solver circuit using Qrisp."""
    
    def __init__(self, lp_file_path: str, name: str, depth: int = 2, after_iterations: int = 50):
        """
        Initialize QUBO circuit.
        
        Parameters
        ----------
        lp_file_path : str
            Path to the .lp file containing the QUBO problem
        name : str
            Name of the QUBO instance for identification
        """
        self._lp_file_path = lp_file_path
        self._name = name
        self._depth = depth
        self._after_iterations = after_iterations
        
        # Load and process the LP file
        m = read(lp_file_path)
        vars = [x.VarName for x in m.getVars() if x.VType == "B"]
        qubo_size = len(vars)
        self._size = int(np.sqrt(qubo_size))
        
        # Create QUBO matrix
        self._qubo = np.zeros((qubo_size, qubo_size))
        obj = m.getObjective()
        
        for term in range(obj.size()):
            num = obj.getCoeff(term)
            i = vars.index(obj.getVar1(term).VarName)
            j = vars.index(obj.getVar2(term).VarName)
            self._qubo[i, j] = num
    
    def name(self) -> str:
        """Return the name of the circuit."""
        return f"QUBO_{self._name}_{self._depth}_{self._after_iterations}"
    
    def create_session(self) -> QuantumSession:
        """
        Create a QUBO solver circuit.
        
        Returns
        -------
        QuantumSession
            Quantum session containing the QUBO solver circuit
        """
        def init_func(qarg: QuantumArray):
            perm_specifiers = create_perm_specifiers(self._size)
            for qv in perm_specifiers:
                h(qv)
            perm = QuantumArray(QuantumFloat(int(np.ceil(np.log2(self._size)))), self._size)
            eval_perm_old(perm_specifiers, city_amount=self._size, qa=perm)

            for i in range(self._size * self._size):
                x_pos = int(i % self._size)
                if x_pos == 0:
                    x(qarg[i])

            for i in range(self._size):
                cyclic_shift(qarg[i * self._size : (i + 1) * self._size], shift_amount=perm[i])

            for i in reversed(range(len(perm_specifiers))):
                demux(perm[i], perm_specifiers[i], perm[i:], permit_mismatching_size=True)

            for i in range(len(perm)):
                perm[i] -= i

            perm.delete()

        # Create QAOA problem instance
        problem = QAOAProblem(
            create_QUBO_cost_operator(self._qubo),
            RX_mixer,
            create_QUBO_cl_cost_function(self._qubo),
        )
        problem.set_init_function(init_func)

        # Create quantum array for the problem
        qarg = QuantumArray(qtype=QuantumVariable(1), shape=(len(self._qubo)))
        
        depth = self._depth
        after_iterations = self._after_iterations
        
        if after_iterations == 0:
            param_qc, symbols = problem.compile_circuit(qarg, depth=depth)
            param_qc: QuantumCircuit = param_qc
            # random init point
            init_point = np.pi * np.random.rand(2 * depth)/2
            subs_dic = {symbols[i] : init_point[i] for i in range(len(symbols))}
            qc: QuantumCircuit = param_qc.bind_parameters(subs_dic)
            return qc
        else:
            optimal_theta = problem.optimization_routine(qarg, depth, mes_kwargs={"backend": def_backend}, max_iter=after_iterations)
            
            h(qarg)

            # Apply p layers of phase separators and mixers    
            for i in range(depth):                          
                problem.cost_operator(qarg, optimal_theta[i])
                problem.mixer(qarg, optimal_theta[i+depth])
            return qarg.qs
        
        
        