"""
/********************************************************************************
* Copyright (c) 2023 the Qrisp authors
*
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0.
*
* This Source Code may also be made available under the following Secondary
* Licenses when the conditions for such availability set forth in the Eclipse
* Public License, v. 2.0 are satisfied: GNU General Public License, version 2 
* or later with the GNU Classpath Exception which is
* available at https://www.gnu.org/software/classpath/license.html.
*
* SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later WITH Classpath-exception-2.0
********************************************************************************/
"""
import numpy as np
from numpy.linalg import norm
import time
from qrisp import QuantumFloat, transpile
from qrisp.simulator import statevector_sim
from qiskit import Aer, execute


n = 6

qf1 = QuantumFloat(n, -1, signed=True)
qf2 = QuantumFloat(n, signed=True)


qf1[:] = 3
qf2[:] = 4

qf_res = qf1 * qf2

start_time = time.time()
print(qf_res)
print(time.time() - start_time)

# %%
# Testing statevector simulator performance
qc = transpile(qf1.qs.compile())

start_time = time.time()
res = statevector_sim(qc)
print("Qrisp simulator time: ", time.time() - start_time)

# %%

# Reverse qubits because of differing statevector convention
qc.qubits.reverse()
qiskit_qc = qc.to_qiskit()

start_time = time.time()
# simulator = Aer.get_backend('qasm_simulator')
simulator = Aer.get_backend("statevector_simulator")
result = execute(qiskit_qc, simulator).result()
qiskit_res = result.get_statevector(qiskit_qc).data
print("Qiskit simulator time: ", time.time() - start_time)

# adjust global phase
res = res / sum(qiskit_res) * np.abs(np.sum(qiskit_res))

print("Results equal:", norm(res - qiskit_res) < 1e-4)
