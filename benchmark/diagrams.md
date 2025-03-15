i successfully implemented the ZX calculus inside Qrisp (a quantum programming language). i made a benchmark, that determines how much better or worse the circuits get compared to the no-compiler-use, normal-qrisp-compiler and zx-enhanced-qrisp-compiler. i want to get good meaningful diagrams from these results. i have 270 of those jsons in "results_01/". 
The circuits tested can be categorised into the following:
- SAT problems (feature models as SAT problem, solved using grover, the result files start with "SAT_")
- TSP problems
    - CMT1 and CMT2 clustered into smaller instances and solved using Grover (starting with "TSP_")
    - CMT1 clustered, transformed into a QUBO and solved using QAOA (files in this format "QUBO_{self._name}_{self._depth}_{self._iterations}")
- a 3 and a 10 GHZ circuit starting with "GHZ-"
- the rest without any prefix are well known benchmarking circuits

I specifically investigated the reduction of T-count, CNOT-count and CNOT-depth. There is also the time it took to make the compilation and the number of qubits in the circuit.

technologies:
- python
- pandas
- plotting library (matplotlib or seaborn)
