# Copyright 2018 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import (
    Any,
    Optional,
)


def has_stabilizer_effect(val: Any) -> bool:
    """
    Returns whether the input has a stabilizer effect. Currently only limits to
    Pauli, H, S, CNOT and CZ gates and their Operations. Does not attempt to
    decompose a gate into supported gates. For e.g. iSWAP or X**0.5 gate will
    return False.
    """
    strats = [
        _strat_has_stabilizer_effect_from_has_stabilizer_effect,
        _strat_has_stabilizer_effect_from_gate
    ]
    for strat in strats:
        result = strat(val)
        if result is not None:
            return result

    # If you can't determine if it has stabilizer effect,  it does not.
    return False


def _strat_has_stabilizer_effect_from_has_stabilizer_effect(val: Any
                                                           ) -> Optional[bool]:
    """
    Attempts to infer whether val has stabilzer effect via its
    _has_stabilizer_effect_ method.
    """
    if hasattr(val, '_has_stabilizer_effect_'):
        result = val._has_stabilizer_effect_()
        if result is not NotImplemented:
            return result
    return None


def _strat_has_stabilizer_effect_from_gate(val: Any) -> Optional[bool]:
    """
    Attempts to infer whether val has stabilzer effect via the value of
    _has_stabilizer_effect_ method of its constituent gate.
    """
    if hasattr(val, 'gate'):
        return _strat_has_stabilizer_effect_from_has_stabilizer_effect(val.gate)
    return None