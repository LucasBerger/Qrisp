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

from qrisp import QuantumFloat
from qrisp.grover import tag_state
from qrisp import quantum_counting


def oracle(qv):
    tag_dic = {qv: 2}
    tag_state(tag_dic)
    tag_dic = {qv: 3}
    tag_state(tag_dic)
    tag_dic = {qv: 4}
    tag_state(tag_dic)
    tag_dic = {qv: 5}
    tag_state(tag_dic)
    tag_dic = {qv: 0}
    tag_state(tag_dic)


qv = QuantumFloat(3, signed=False)

print(quantum_counting(qv, oracle, 5))
