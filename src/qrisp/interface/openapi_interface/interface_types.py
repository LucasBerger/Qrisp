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


from qrisp.interface.openapi_interface.codegen.client.openapi_client.models import (
    Clbit as PortableClbit,
)
from qrisp.interface.openapi_interface.codegen.client.openapi_client.models import (
    Instruction as PortableInstruction,
)
from qrisp.interface.openapi_interface.codegen.client.openapi_client.models import (
    Operation as PortableOperation,
)
from qrisp.interface.openapi_interface.codegen.client.openapi_client.models import (
    QuantumCircuit as PortableQuantumCircuit,
)
from qrisp.interface.openapi_interface.codegen.client.openapi_client.models import (
    Qubit as PortableQubit,
)
from qrisp.interface.openapi_interface.codegen.server.openapi_server.models import (
    BackendStatus,
    ConnectivityEdge,
)
