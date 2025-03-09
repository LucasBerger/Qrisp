from base_qrisp_circuits import QrispCircuit
from qrisp import QuantumSession, QuantumFloat, QuantumArray, auto_uncompute, z, invert, QuantumDictionary
from qrisp.alg_primitives.iterable_processing import demux
import numpy as np
from math import factorial

from qrisp.algorithms.grover.grover_tools import grovers_alg

def swap_to_front(qa, index):
    """Swaps the entry specified by index to the first position of the QuantumArray."""
    with invert():
        demux(qa[0], index, qa, permit_mismatching_size=True)

def eval_perm(perm_specifiers):
    """Evaluates a permutation based on the given specifiers."""
    city_specifier_size = int(np.ceil(np.log2(len(perm_specifiers) + 1)))
    qa = QuantumArray(QuantumFloat(city_specifier_size), len(perm_specifiers) + 1)
    qa[:] = np.arange(len(perm_specifiers) + 1)
    
    for i in range(len(perm_specifiers)):
        swap_to_front(qa[i:], perm_specifiers[i])
    
    return qa

def create_perm_specifiers(city_amount, init_seq=None):
    """Creates quantum floats specifying the permutations."""
    perm_specifiers = []
    
    for i in range(city_amount - 1):
        qf_size = int(np.ceil(np.log2(city_amount - i)))
        perm_specifier = QuantumFloat(qf_size)
        
        if init_seq is not None:
            perm_specifier[:] = init_seq[i]
            
        perm_specifiers.append(perm_specifier)
    
    return perm_specifiers

@auto_uncompute
def eval_distance_threshold(perm_specifiers, precision, threshold, distance_matrix, method="qdict"):
    """Evaluates if a certain permutation is below a given distance threshold."""
    itinerary = eval_perm(perm_specifiers)
    
    if method == "qdict":
        distance = qdict_calc_perm_travel_distance(itinerary, precision, distance_matrix)
    else:
        distance = qpe_calc_perm_travel_distance(itinerary, precision, distance_matrix)
    
    z(distance <= threshold)

def qdict_calc_perm_travel_distance(itinerary, precision, distance_matrix):
    """Calculates permutation travel distance using quantum dictionary approach."""
    res = QuantumFloat(precision, -precision)
    city_amount = len(distance_matrix)
    
    # Fill QuantumDictionary
    qd = QuantumDictionary(return_type=res)
    for i in range(city_amount):
        for j in range(city_amount):
            qd[(i, j)] = res.truncate(distance_matrix[i, j])
    
    # Evaluate result
    for i in range(city_amount):
        trip_distance = qd[itinerary[i], itinerary[(i + 1) % city_amount]]
        res += trip_distance
        trip_distance.uncompute(recompute=True)
    
    return res

class TSPCircuit(QrispCircuit):
    """Implementation of a Traveling Salesman Problem circuit using Qrisp."""
    
    def __init__(self, city_amount: int, distance_matrix: np.ndarray, threshold: float, name: str):
        """
        Initialize TSP circuit.
        
        Parameters
        ----------
        city_amount : int
            Number of cities in the TSP problem
        distance_matrix : np.ndarray
            Matrix containing distances between cities
        threshold : float
            Distance threshold for acceptable solutions
        name : str
            Name of the TSP instance for identification
        """
        self._city_amount = city_amount
        self._distance_matrix = distance_matrix
        self._threshold = threshold
        self._name = name
        
    def name(self) -> str:
        """Return the name of the circuit."""
        return f"TSP_{self._name}"
    
    def create_session(self) -> QuantumSession:
        """
        Create a TSP solver circuit.
        
        Returns
        -------
        QuantumSession
            Quantum session containing the TSP solver circuit
        """
        # Create permutation specifiers
        perm_specifiers = create_perm_specifiers(self._city_amount)
        
        # Calculate winner state amount
        winner_state_amount = (
            2 ** sum([qv.size for qv in perm_specifiers])
            / factorial(self._city_amount)
            * self._city_amount
            * 2
        )
        
        # Apply Grover's algorithm without measurement
        grovers_alg(
            perm_specifiers,
            eval_distance_threshold,
            kwargs={
                "threshold": self._threshold,
                "precision": 5,
                "method": "qdict",
                "distance_matrix": self._distance_matrix
            },
            winner_state_amount=winner_state_amount
        )
        
        return perm_specifiers[0].qs

# Example distance matrix and parameters for a 4-city TSP
SAMPLE_4CITY_MATRIX = np.array([
    [0, 0.25, 0.125, 0.5],
    [0.25, 0, 0.625, 0.375],
    [0.125, 0.625, 0, 0.75],
    [0.5, 0.375, 0.75, 0]
]) / 4

# Example distance matrix for a smaller 3-city TSP
SAMPLE_3CITY_MATRIX = np.array([
    [0, 0.25, 0.5],
    [0.25, 0, 0.375],
    [0.5, 0.375, 0]
]) / 3 

SAMPLE_6CITY_MATRIX = np.array([
    [0, 0.25, 0.125, 0.5, 0.375, 0.75],
    [0.25, 0, 0.625, 0.375, 0.75, 0.125],
    [0.125, 0.625, 0, 0.75, 0.125, 0.5],
    [0.5, 0.375, 0.75, 0, 0.625, 0.25],
    [0.375, 0.75, 0.125, 0.625, 0, 0.25],
    [0.75, 0.125, 0.5, 0.25, 0.625, 0]
]) / 6

# CMT1_0.vrp
cmt1_0 = np.array([
    [0.000, 0.762, 1.000, 0.714],
    [0.762, 0.000, 0.262, 0.119],
    [1.000, 0.262, 0.000, 0.286],
    [0.714, 0.119, 0.286, 0.000],
]) / 4

# CMT1_1.vrp
cmt1_1 = np.array([
    [0.000, 0.548, 0.581, 1.000, 0.806],
    [0.548, 0.000, 0.161, 0.452, 0.290],
    [0.581, 0.161, 0.000, 0.516, 0.226],
    [1.000, 0.452, 0.516, 0.000, 0.323],
    [0.806, 0.290, 0.226, 0.323, 0.000],
]) / 5


# CMT1_2.vrp
cmt1_2 = np.array([
    [0.000, 1.000],
    [1.000, 0.000],
]) / 2

# CMT1_3.vrp
cmt1_3 = np.array([
    [0.000, 1.000, 0.882],
    [1.000, 0.000, 0.471],
    [0.882, 0.471, 0.000],
]) / 3

# CMT1_4.vrp
cmt1_4 = np.array([
    [0.000, 0.783, 1.000],
    [0.783, 0.000, 0.261],
    [1.000, 0.261, 0.000],
]) / 3

# CMT1_5.vrp
cmt1_5 = np.array([
    [0.000, 0.824, 0.735, 1.000, 0.912],
    [0.824, 0.000, 0.471, 0.353, 0.471],
    [0.735, 0.471, 0.000, 0.353, 0.206],
    [1.000, 0.353, 0.353, 0.000, 0.206],
    [0.912, 0.471, 0.206, 0.206, 0.000],
]) / 5

# CMT1_6.vrp
cmt1_6 = np.array([
    [0.000, 1.000],
    [1.000, 0.000],
]) / 2

# CMT1_7.vrp
cmt1_7 = np.array([
    [0.000, 1.000, 0.250],
    [1.000, 0.000, 0.875],
    [0.250, 0.875, 0.000],
]) / 3

# CMT1_8.vrp
cmt1_8 = np.array([
    [0.000, 0.875, 1.000],
    [0.875, 0.000, 0.438],
    [1.000, 0.438, 0.000],
]) / 3

# CMT1_9.vrp
cmt1_9 = np.array([
    [0.000, 0.688, 0.500, 1.000],
    [0.688, 0.000, 0.562, 0.562],
    [0.500, 0.562, 0.000, 0.562],
    [1.000, 0.562, 0.562, 0.000],
]) / 4

# CMT1_10.vrp
cmt1_10 = np.array([
    [0.000, 1.000, 0.846, 0.962],
    [1.000, 0.000, 0.231, 0.538],
    [0.846, 0.231, 0.000, 0.346],
    [0.962, 0.538, 0.346, 0.000],
]) / 4

# CMT1_11.vrp
cmt1_11 = np.array([
    [0.000, 0.742, 1.000, 0.710],
    [0.742, 0.000, 0.258, 0.194],
    [1.000, 0.258, 0.000, 0.323],
    [0.710, 0.194, 0.323, 0.000],
]) / 4

# CMT1_12.vrp
cmt1_12 = np.array([
    [0.000, 1.000, 0.857, 0.714],
    [1.000, 0.000, 0.857, 0.429],
    [0.857, 0.857, 0.000, 0.429],
    [0.714, 0.429, 0.429, 0.000],
]) / 4

# CMT1_13.vrp
cmt1_13 = np.array([
    [0.000, 0.842, 1.000, 0.684],
    [0.842, 0.000, 0.474, 0.158],
    [1.000, 0.474, 0.000, 0.579],
    [0.684, 0.158, 0.579, 0.000],
]) / 4

# CMT1_14.vrp
cmt1_14 = np.array([
    [0.000, 0.629, 0.800, 1.000],
    [0.629, 0.000, 0.200, 0.743],
    [0.800, 0.200, 0.000, 0.629],
    [1.000, 0.743, 0.629, 0.000],
]) / 4

# CMT1_15.vrp
cmt1_15 = np.array([
    [0.000, 0.955, 1.000],
    [0.955, 0.000, 0.409],
    [1.000, 0.409, 0.000],
]) / 3

# CMT1_16.vrp
cmt1_16 = np.array([
    [0.000, 1.000, 0.636, 0.909, 0.909],
    [1.000, 0.000, 0.364, 0.273, 0.485],
    [0.636, 0.364, 0.000, 0.303, 0.394],
    [0.909, 0.273, 0.303, 0.000, 0.182],
    [0.909, 0.485, 0.394, 0.182, 0.000],
]) / 5

# CMT1_17.vrp
cmt1_17 = np.array([
    [0.000, 1.000, 1.000, 0.906],
    [1.000, 0.000, 0.531, 0.312],
    [1.000, 0.531, 0.000, 0.219],
    [0.906, 0.312, 0.219, 0.000],
]) / 4

# CMT1_18.vrp
cmt1_18 = np.array([
    [0.000, 0.886, 1.000],
    [0.886, 0.000, 0.136],
    [1.000, 0.136, 0.000],
]) / 3

# CMT2_lower_cap_0.vrp
cmt2_lower_cap_0 = np.array([
    [0.000, 0.837, 0.837, 1.000],
    [0.837, 0.000, 0.093, 0.279],
    [0.837, 0.093, 0.000, 0.209],
    [1.000, 0.279, 0.209, 0.000],
]) / 4

# CMT2_lower_cap_1.vrp
cmt2_lower_cap_1 = np.array([
    [0.000, 0.781, 1.000, 0.688, 0.656],
    [0.781, 0.000, 0.219, 0.250, 0.156],
    [1.000, 0.219, 0.000, 0.375, 0.375],
    [0.688, 0.250, 0.375, 0.000, 0.281],
    [0.656, 0.156, 0.375, 0.281, 0.000],
]) / 5

# CMT2_lower_cap_2.vrp
cmt2_lower_cap_2 = np.array([
    [0.000, 0.514, 0.838, 0.757, 1.000],
    [0.514, 0.000, 0.351, 0.243, 0.514],
    [0.838, 0.351, 0.000, 0.270, 0.162],
    [0.757, 0.243, 0.270, 0.000, 0.378],
    [1.000, 0.514, 0.162, 0.378, 0.000],
]) / 5

# CMT2_lower_cap_3.vrp
cmt2_lower_cap_3 = np.array([
    [0.000, 1.000, 0.833, 0.733, 0.667],
    [1.000, 0.000, 0.300, 0.267, 0.533],
    [0.833, 0.300, 0.000, 0.200, 0.200],
    [0.733, 0.267, 0.200, 0.000, 0.333],
    [0.667, 0.533, 0.200, 0.333, 0.000],
]) / 5

# CMT2_lower_cap_4.vrp
cmt2_lower_cap_4 = np.array([
    [0.000, 0.730, 0.730, 0.919, 1.000],
    [0.730, 0.000, 0.162, 0.297, 0.297],
    [0.730, 0.162, 0.000, 0.459, 0.297],
    [0.919, 0.297, 0.459, 0.000, 0.378],
    [1.000, 0.297, 0.297, 0.378, 0.000],
]) / 5

# CMT2_lower_cap_5.vrp
cmt2_lower_cap_5 = np.array([
    [0.000, 0.500, 1.000, 0.611, 0.389],
    [0.500, 0.000, 0.500, 0.333, 0.278],
    [1.000, 0.500, 0.000, 0.556, 0.722],
    [0.611, 0.333, 0.556, 0.000, 0.611],
    [0.389, 0.278, 0.722, 0.611, 0.000],
]) / 5

# CMT2_lower_cap_6.vrp
cmt2_lower_cap_6 = np.array([
    [0.000, 1.000, 0.943, 0.857],
    [1.000, 0.000, 0.371, 0.171],
    [0.943, 0.371, 0.000, 0.429],
    [0.857, 0.171, 0.429, 0.000],
]) / 4

# CMT2_lower_cap_7.vrp
cmt2_lower_cap_7 = np.array([
    [0.000, 0.714, 0.667, 1.000],
    [0.714, 0.000, 0.333, 0.619],
    [0.667, 0.333, 0.000, 0.333],
    [1.000, 0.619, 0.333, 0.000],
]) / 4

# CMT2_lower_cap_8.vrp
cmt2_lower_cap_8 = np.array([
    [0.000, 0.909, 1.000, 0.955],
    [0.909, 0.000, 0.364, 0.136],
    [1.000, 0.364, 0.000, 0.227],
    [0.955, 0.136, 0.227, 0.000],
]) / 4

# CMT2_lower_cap_9.vrp
cmt2_lower_cap_9 = np.array([
    [0.000, 1.000, 0.429],
    [1.000, 0.000, 0.714],
    [0.429, 0.714, 0.000],
]) / 3

# CMT2_lower_cap_10.vrp
cmt2_lower_cap_10 = np.array([
    [0.000, 0.767, 0.744, 1.000, 0.953, 0.930],
    [0.767, 0.000, 0.186, 0.279, 0.279, 0.163],
    [0.744, 0.186, 0.000, 0.279, 0.209, 0.233],
    [1.000, 0.279, 0.279, 0.000, 0.093, 0.116],
    [0.953, 0.279, 0.209, 0.093, 0.000, 0.186],
    [0.930, 0.163, 0.233, 0.116, 0.186, 0.000],
]) / 6

# CMT2_lower_cap_11.vrp
cmt2_lower_cap_11 = np.array([
    [0.000, 0.857, 0.571, 1.000],
    [0.857, 0.000, 0.500, 0.357],
    [0.571, 0.500, 0.000, 0.500],
    [1.000, 0.357, 0.500, 0.000],
]) / 4

# CMT2_lower_cap_12.vrp
cmt2_lower_cap_12 = np.array([
    [0.000, 0.889, 1.000, 0.778, 0.778],
    [0.889, 0.000, 0.500, 0.333, 0.222],
    [1.000, 0.500, 0.000, 0.222, 0.667],
    [0.778, 0.333, 0.222, 0.000, 0.500],
    [0.778, 0.222, 0.667, 0.500, 0.000],
]) / 5

# CMT2_lower_cap_13.vrp
cmt2_lower_cap_13 = np.array([
    [0.000, 0.676, 0.730, 1.000, 0.757],
    [0.676, 0.000, 0.216, 0.351, 0.324],
    [0.730, 0.216, 0.000, 0.297, 0.108],
    [1.000, 0.351, 0.297, 0.000, 0.351],
    [0.757, 0.324, 0.108, 0.351, 0.000],
]) / 5

# CMT2_lower_cap_14.vrp
cmt2_lower_cap_14 = np.array([
    [0.000, 1.000, 0.500],
    [1.000, 0.000, 0.500],
    [0.500, 0.500, 0.000],
]) / 3

# CMT2_lower_cap_15.vrp
cmt2_lower_cap_15 = np.array([
    [0.000, 1.000, 0.429, 0.786],
    [1.000, 0.000, 0.714, 0.571],
    [0.429, 0.714, 0.000, 0.786],
    [0.786, 0.571, 0.786, 0.000],
]) / 4

# CMT2_lower_cap_16.vrp
cmt2_lower_cap_16 = np.array([
    [0.000, 1.000, 0.917, 0.833, 0.875],
    [1.000, 0.000, 0.167, 0.583, 0.375],
    [0.917, 0.167, 0.000, 0.417, 0.208],
    [0.833, 0.583, 0.417, 0.000, 0.208],
    [0.875, 0.375, 0.208, 0.208, 0.000],
]) / 5

# CMT2_lower_cap_17.vrp
cmt2_lower_cap_17 = np.array([
    [0.000, 0.786, 0.881, 1.000],
    [0.786, 0.000, 0.429, 0.214],
    [0.881, 0.429, 0.000, 0.524],
    [1.000, 0.214, 0.524, 0.000],
]) / 4

# CMT2_lower_cap_18.vrp
cmt2_lower_cap_18 = np.array([
    [0.000, 0.696, 1.000, 0.783, 1.000],
    [0.696, 0.000, 0.348, 0.217, 0.522],
    [1.000, 0.348, 0.000, 0.304, 0.478],
    [0.783, 0.217, 0.304, 0.000, 0.304],
    [1.000, 0.522, 0.478, 0.304, 0.000],
]) / 5

# CMT2_lower_cap_19.vrp
cmt2_lower_cap_19 = np.array([
    [0.000, 0.821, 1.000, 0.964],
    [0.821, 0.000, 0.786, 0.286],
    [1.000, 0.786, 0.000, 0.607],
    [0.964, 0.286, 0.607, 0.000],
]) / 4

# CMT2_lower_cap_20.vrp
cmt2_lower_cap_20 = np.array([
    [0.000, 0.812, 0.844, 1.000],
    [0.812, 0.000, 0.219, 0.344],
    [0.844, 0.219, 0.000, 0.156],
    [1.000, 0.344, 0.156, 0.000],
]) / 4

# CMT2_lower_cap_21.vrp
cmt2_lower_cap_21 = np.array([
    [0.000, 1.000],
    [1.000, 0.000],
]) / 2

# CMT2_lower_cap_22.vrp
cmt2_lower_cap_22 = np.array([
    [0.000, 1.000, 0.947],
    [1.000, 0.000, 0.395],
    [0.947, 0.395, 0.000],
]) / 3