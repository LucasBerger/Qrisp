"""
\********************************************************************************
* Copyright (c) 2024 the Qrisp authors
*
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0.
*
* This Source Code may also be made available under the following Secondary
* Licenses when the conditions for such availability set forth in the Eclipse
* Public License, v. 2.0 are satisfied: GNU General Public License, version 2
* with the GNU Classpath Exception which is
* available at https://www.gnu.org/software/classpath/license.html.
*
* SPDX-License-Identifier: EPL-2.0 OR GPL-2.0 WITH Classpath-exception-2.0
********************************************************************************/
"""

from qrisp.misc.spin import *

threshold = 1e-9

#pauli_table = {(1,1):(0,1),(1,2):(3,1j),(1,3):(2,-1j),
#            (2,1):(3,-1j),(2,2):(0,1),(2,3):(1,1j),
#            (3,1):(2,1j),(3,2):(1,-1j),(3,3):(1,1)}

pauli_table = {("X","X"):("I",1),("X","Y"):("Z",1j),("X","Z"):("Y",-1j),
            ("Y","X"):("Z",-1j),("Y","Y"):("I",1),("Y","Z"):("X",1j),
            ("Z","X"):("Y",1j),("Z","Y"):("X",-1j),("Z","Z"):("I",1)}

#
# Helper functions
#

def set_bit(n,k):
    return n | (1 << k)   

def pauli_mul(P1,P2):
    if P1=="I":
        return (P2,1)
    if P2=="I":
        return (P1,1)
    return pauli_table[(P1,P2)]

def mul_paulis(pauli1,pauli2):
    result_list = []
    result_coeff = 1
    pauli_dict1 = dict(pauli1)
    pauli_dict2 = dict(pauli2)
    keys = set()
    keys.update(set(pauli_dict1.keys()))
    keys.update(set(pauli_dict2.keys()))
    for key in sorted(keys):
        pauli, coeff = pauli_mul(pauli_dict1.get(key,"I"),pauli_dict2.get(key,"I"))
        if pauli!="I":
            result_list.append((key,pauli))
        result_coeff *= coeff
    return tuple(result_list), result_coeff

#
# Commutativity checks
#

def commute_qw(a,b):
    """
    Check if two Pauli products commute qubit-wise.
 
    Parameters
    ----------
    a : dict
        A dictionary encoding a Pauli product.
    b : dict
        A dictionary encoding a Pauli product.

    Returns
    -------

    """
    keys = set()
    keys.update(set(a.keys()))
    keys.update(set(b.keys()))

    for key in keys:
        if a.get(key,"I")!="I" and b.get(key,"I")!="I" and a.get(key,"I")!=b.get(key,"I"):
            return False
    return True

def commute(a,b):
    """
    Check if two Pauli products commute.

    Parameters
    ----------
    a : dict
        A dictionary encoding a Pauli product.
    b : dict
        A dictionary encoding a Pauli product.

    """

    keys = set()
    keys.update(set(a.keys()))
    keys.update(set(b.keys()))

    # Count non-commuting Pauli operators
    commute = True

    for key in keys:
        if a.get(key,"I")!="I" and b.get(key,"I")!="I" and a.get(key,"I")!=b.get(key,"I"):
            commute = not commute
    return commute

#
# Evaluate observable
#

def evaluate_observable(observable: int, x: int):
    """
    This method evaluates an observable that is a tensor product of Pauli-:math:`Z` operators
    with respect to a measurement outcome. 
        
    A Pauli operator of the form :math:`\prod_{i\in I}Z_i`, for some finite set of indices :math:`I\subset \mathbb N`, 
    is identified with an integer:
    We identify the Pauli operator with the binary string that has ones at positions :math:`i\in I`
    and zeros otherwise, and then convert this binary string to an integer.
        
    Parameters
    ----------
        
    observable : int
        The observable represented as integer.
     x : int 
        The measurement outcome represented as integer.
        
    Returns
    -------
    int
        The value of the observable with respect to the measurement outcome.
        
    """
        
    if bin(observable & x).count('1') % 2 == 0:
        return 1
    else:
        return -1    

#
# PauliOperator
#

class PauliOperator:

    def __init__(self, arg=None, constant=0):
        """

        Parameters
        ----------
        arg : dict or sympy.Basic
            The 
        constant : float

        """

        if arg is None:
            self.pauli_dict = {}
            self.constant = constant
        elif isinstance(arg, dict):
            self.pauli_dict = arg
            self.constant = constant
        elif isinstance(arg, sympy.Basic):
            pauli_dict, constant = to_pauli_dict(arg)
            self.pauli_dict = pauli_dict
            self.constant = constant     
        else:
            raise TypeError("TYPE ERROR")

    @classmethod
    def from_expr(cls, expr):
        pauli_dict, constant = to_Pauli_dict(expr)
        return cls(pauli_dict, constant)

    
    def inpl_add(self,other,factor=1):

        if not isinstance(other, PauliOperator):
            raise TypeError("TYPE ERROR")

        for pauli,coeff in other.pauli_dict.items():
            self.pauli_dict[pauli] = self.pauli_dict.get(pauli,0)+coeff*factor
            if abs(self.pauli_dict[pauli])<threshold:
                del self.pauli_dict[pauli]
        self.constant += other.constant*factor
    

    def __add__(self,other):
        """
        
        """

        if isinstance(other,(int,float,complex)):
            return self.scalar_add(other)
        if not isinstance(other, PauliOperator):
            raise TypeError("TYPE ERROR")

        result = PauliOperator()
        res_pauli_dict = {}
        result.constant = self.constant+other.constant

        for pauli,coeff in self.pauli_dict.items():
            res_pauli_dict[pauli] = res_pauli_dict.get(pauli,0)+coeff
            if abs(res_pauli_dict[pauli])<threshold:
                del res_pauli_dict[pauli]
    
        for pauli,coeff in other.pauli_dict.items():
            res_pauli_dict[pauli] = res_pauli_dict.get(pauli,0)+coeff
            if abs(res_pauli_dict[pauli])<threshold:
                del res_pauli_dict[pauli]
        
        result.pauli_dict = res_pauli_dict
        return result

    def __mul__(self,other):
        """
        
        """

        if isinstance(other,(int,float,complex)):
            return self.scalar_mul(other)
        if not isinstance(other, PauliOperator):
            raise TypeError("TYPE ERROR")

        result = PauliOperator()
        res_pauli_dict = {}
        result.constant = self.constant*other.constant

        for pauli1, coeff1 in self.pauli_dict.items():
            for pauli2, coeff2 in other.pauli_dict.items():
                curr_tuple, curr_coeff = mul_paulis(pauli1,pauli2)
                if len(curr_tuple)>0:
                    res_pauli_dict[curr_tuple] = res_pauli_dict.get(curr_tuple,0) + curr_coeff*coeff1*coeff2
                else:
                    result.constant += curr_coeff*coeff1*coeff2

        if self.constant!=0:
            for pauli, coeff in other.pauli_dict.items():
                res_pauli_dict[pauli] = res_pauli_dict.get(pauli,0) + coeff*self.constant
    
        if other.constant!=0:
            for pauli, coeff in other.pauli_dict.items():
                res_pauli_dict[pauli] = res_pauli_dict.get(pauli,0) + coeff*other.constant

        result.pauli_dict = res_pauli_dict
        return result

    def scalar_add(self,constant):
        result = PauliOperator()
        res_pauli_dict = {}
        result.constant = self.constant+constant

        for pauli,coeff in self.pauli_dict.items():
            res_pauli_dict[pauli] = res_pauli_dict.get(pauli,0)+coeff
            if abs(res_pauli_dict[pauli])<threshold:
                del res_pauli_dict[pauli]
        
        result.pauli_dict = res_pauli_dict
        return result

    def scalar_mul(self,constant):
        result = PauliOperator()
        res_pauli_dict = {}
        result.constant = self.constant*constant
        for pauli,coeff in self.pauli_dict.items():
            res_pauli_dict[pauli] = coeff*constant
            if abs(res_pauli_dict[pauli])<threshold:
                del res_pauli_dict[pauli]
        result.pauli_dict = res_pauli_dict
        return result
    
    def apply_threshold(self,threshold):
        delete_list = []
        for pauli,coeff in self.pauli_dict.items():
            if abs(coeff)<threshold:
                delete_list.append(pauli)
        for pauli in delete_list:
            del self.pauli_dict[pauli]

    def to_expr(self):
        """
        

        """
        
        expr = self.constant

        def to_spin(P, index):
            if P=="I":
                return 1
            if P=="X":
                return X(index)
            if P=="Y":
                return Y(index)
            else:
                return Z(index)
        
        for pauli,coeff in self.pauli_dict.items():
            curr_expr = coeff
            for item in pauli:
                curr_expr *= to_spin(item[1],item[0])
            expr += curr_expr

        return expr

    #
    # Measurement settings
    #

    def get_measurement_settings(self, qarg, method=None):
        """
        todo 

        Parameters
        ----------
        qarg : QuantumVariable or QuantumArray
            The argument the spin operator is evaluated on.
        method : string, optional
            The method for evaluating the expected value of the Hamiltonian.
            Available is ``QWC``: Pauli terms are grouped based on qubit-wise commutativity.
            The default is None: The expected value of each Pauli term is computed independently.

        Returns
        -------
        measurement_circuits : list[QuantumCircuit]
    
        measurement_ops : list[list[int]]
    
        measurement_coeffs : list[list[float]]

        constant_term : float
            The constant term in the quantum Hamiltonian.

        """

        if method=='QWC':
            return self.qubit_wise_commutativity(qarg)

        # No grouping (default):

        from qrisp import QuantumVariable, QuantumArray, QuantumCircuit

        if isinstance(qarg, QuantumArray):
            num_qubits = sum(qv.size for qv in list(qarg.flatten()))
        else:
            num_qubits = qarg.size
        
        measurement_circuits = []
        measurement_coeffs = []
        measurement_ops = []
        constant_term = float(self.constant.real)

        for pauli,coeff in self.pauli_dict.items():
            qc = QuantumCircuit(num_qubits)
            meas_op = 0
            for item in pauli:
                if item[0] >= num_qubits:
                    raise Exception("Insufficient number of qubits")
                if item[1]=="X":
                    qc.ry(-np.pi/2,item[0])
                if item[1]=="Y":
                    qc.rx(np.pi/2,item[0])
                
                meas_op = set_bit(meas_op, item[0])

            measurement_circuits.append(qc)
            measurement_ops.append([meas_op])
            measurement_coeffs.append([float(coeff.real)])

        return measurement_circuits, measurement_ops, measurement_coeffs, constant_term    
    
    def qubit_wise_commutativity(self, qarg):
        """
        todo

        Parameters
        ----------

        Returns
        -------

        """

        from qrisp import QuantumVariable, QuantumArray, QuantumCircuit

        if isinstance(qarg, QuantumArray):
            num_qubits = sum(qv.size for qv in list(qarg.flatten()))
        else:
            num_qubits = qarg.size

        pauli_dicts = [] # A list of Pauli products represented as dictionaries
        measurement_circuits = []
        measurement_coeffs = []
        measurement_ops = []
        constant_term = float(self.constant.real)

        for pauli,coeff in self.pauli_dict.items():
            meas_op = 0
            for item in pauli:
                meas_op = set_bit(meas_op, item[0])

            # Number of distict meaurement settings
            settings = len(pauli_dicts)
            commute_bool = False
            curr_dict = dict(pauli)

            if settings > 0:   
                for k in range(settings):
                    # check if Pauli terms commute qubit-wise 
                    commute_bool = commute_qw(pauli_dicts[k],curr_dict)
                    if commute_bool:
                        pauli_dicts[k].update(curr_dict)
                        measurement_ops[k].append(meas_op)
                        measurement_coeffs[k].append(float(coeff.real))
                        break
            if settings==0 or not commute_bool: 
                pauli_dicts.append(curr_dict)
                measurement_ops.append([meas_op])
                measurement_coeffs.append([float(coeff.real)])

        # construct change of basis circuits
        for pauli in pauli_dicts:
            qc = QuantumCircuit(num_qubits)
            for index,axis in pauli.items():
                if axis=="X":
                    qc.ry(-np.pi/2,index)
                if axis=="Y":
                    qc.rx(np.pi/2,index)  
            measurement_circuits.append(qc)    

        return measurement_circuits, measurement_ops, measurement_coeffs, constant_term

    #
    # Tools
    #

    def to_matrix(self):
        """
        Matrix representation of the PauliOperator.
    
        Returns
        -------
        M : numpy.array
            A matrix representation of the quantum Hamiltonian.

        Examples
        --------

        """

        from numpy import kron as TP

        I = np.array([[1,0],[0,1]])

        def get_matrix(P):
            if P=="I":
                return np.array([[1,0],[0,1]])
            if P=="X":
                return np.array([[0,1],[1,0]])
            if P=="Y":
                return np.array([[0,-1j],[1j,0]])
            else:
                return np.array([[1,0],[0,-1]])

        def recursive_TP(keys,pauli_dict):
            if len(keys)==1:
                return get_matrix(pauli_dict.get(keys[0],"I"))
            return TP(get_matrix(pauli_dict.get(keys.pop(0),"I")),recursive_TP(keys,pauli_dict))

        self.pauli_dict
        self.constant

        pauli_dicts = []
        coeffs = []

        keys = set()
        for pauli,coeff in self.pauli_dict.items():
            curr_dict = dict(pauli)
            keys.update(set(curr_dict.keys()))
            pauli_dicts.append(curr_dict)    
            coeffs.append(coeff)

        keys = set()
        for item in pauli_dicts:
            keys.update(set(item.keys()))
        keys = sorted(keys)
        dim = len(keys)

        m = len(coeffs)
        M = complex(self.constant)*np.identity(2**dim).astype(np.complex128)
        for k in range(m):
            M += complex(coeffs[k])*recursive_TP(keys.copy(),pauli_dicts[k])

        return M

    def to_sparse_matrix(self):
        """
        Matrix representation of the PauliOperator.
    
        Returns
        -------
        M : numpy.array
            A matrix representation of the quantum Hamiltonian.

        Examples
        --------

        """

        #from numpy import kron as TP
        import scipy.sparse as sp
        from scipy.sparse import kron as TP, csr_matrix

        I = csr_matrix([[1,0],[0,1]])

        def get_matrix(P):
            if P=="I":
                return csr_matrix([[1,0],[0,1]])
            if P=="X":
                return csr_matrix([[0,1],[1,0]])
            if P=="Y":
                return csr_matrix([[0,-1j],[1j,0]])
            else:
                return csr_matrix([[1,0],[0,-1]])

        def recursive_TP(keys,pauli_dict):
            if len(keys)==1:
                return get_matrix(pauli_dict.get(keys[0],"I"))
            return TP(get_matrix(pauli_dict.get(keys.pop(0),"I")),recursive_TP(keys,pauli_dict))

        self.pauli_dict
        self.constant

        pauli_dicts = []
        coeffs = []

        keys = set()
        for pauli,coeff in self.pauli_dict.items():
            curr_dict = dict(pauli)
            keys.update(set(curr_dict.keys()))
            pauli_dicts.append(curr_dict)    
            coeffs.append(coeff)

        keys = set()
        for item in pauli_dicts:
            keys.update(set(item.keys()))
        keys = sorted(keys)
        dim = len(keys)

        m = len(coeffs)
        M = complex(self.constant)*sp.identity(2**dim, format='csr')
        for k in range(m):
            M += complex(coeffs[k])*recursive_TP(keys.copy(),pauli_dicts[k])

        return M

    def ground_state_energy(self):
        """
        Calculates the ground state energy of a PauliOperator classically.
    
        Returns
        -------
        E : float
            The ground state energy. 

        """

        from scipy.sparse.linalg import eigsh

        M = self.to_sparse_matrix()
        # Compute the smallest eigenvalue
        eigenvalues, _ = eigsh(M, k=1, which='SA')  # 'SA' stands for smallest algebraic
        E = eigenvalues[0]

        return E