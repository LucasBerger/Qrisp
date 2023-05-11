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

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model_ import Model
from openapi_server.models.qubit import Qubit
from openapi_server import util

from openapi_server.models.qubit import Qubit  # noqa: E501

class ConnectivityEdge(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, qb1=None, qb2=None):  # noqa: E501
        """ConnectivityEdge - a model defined in OpenAPI

        :param qb1: The qb1 of this ConnectivityEdge.  # noqa: E501
        :type qb1: Qubit
        :param qb2: The qb2 of this ConnectivityEdge.  # noqa: E501
        :type qb2: Qubit
        """
        self.openapi_types = {
            'qb1': Qubit,
            'qb2': Qubit
        }

        self.attribute_map = {
            'qb1': 'qb1',
            'qb2': 'qb2'
        }

        self._qb1 = qb1
        self._qb2 = qb2

    @classmethod
    def from_dict(cls, dikt) -> 'ConnectivityEdge':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ConnectivityEdge of this ConnectivityEdge.  # noqa: E501
        :rtype: ConnectivityEdge
        """
        return util.deserialize_model(dikt, cls)

    @property
    def qb1(self):
        """Gets the qb1 of this ConnectivityEdge.


        :return: The qb1 of this ConnectivityEdge.
        :rtype: Qubit
        """
        return self._qb1

    @qb1.setter
    def qb1(self, qb1):
        """Sets the qb1 of this ConnectivityEdge.


        :param qb1: The qb1 of this ConnectivityEdge.
        :type qb1: Qubit
        """
        if qb1 is None:
            raise ValueError("Invalid value for `qb1`, must not be `None`")  # noqa: E501

        self._qb1 = qb1

    @property
    def qb2(self):
        """Gets the qb2 of this ConnectivityEdge.


        :return: The qb2 of this ConnectivityEdge.
        :rtype: Qubit
        """
        return self._qb2

    @qb2.setter
    def qb2(self, qb2):
        """Sets the qb2 of this ConnectivityEdge.


        :param qb2: The qb2 of this ConnectivityEdge.
        :type qb2: Qubit
        """
        if qb2 is None:
            raise ValueError("Invalid value for `qb2`, must not be `None`")  # noqa: E501

        self._qb2 = qb2
