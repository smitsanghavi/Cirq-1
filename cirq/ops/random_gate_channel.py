# Copyright 2020 The Cirq Developers
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

import numbers
from typing import Tuple, TYPE_CHECKING, Dict, Any, cast, SupportsFloat, \
    Optional

import numpy as np

from cirq import protocols, value
from cirq.ops import raw_types
from cirq._compat import proper_repr

if TYPE_CHECKING:
    import cirq


@value.value_equality(approximate=True)
class RandomGateChannel(raw_types.Gate):
    """Applies a sub gate with some probability."""

    def __init__(self, *, sub_gate: 'cirq.Gate', probability: value.TParamVal):
        if isinstance(probability, numbers.Number) and not 0 <= float(
                cast(SupportsFloat, probability)) <= 1:
            raise ValueError("not 0 <= probability <= 1")

        self.sub_gate = sub_gate
        self.probability = probability

        # Auto flatten.
        if isinstance(self.sub_gate, RandomGateChannel):
            self.probability *= self.sub_gate.probability
            self.sub_gate = self.sub_gate.sub_gate

    def _qid_shape_(self) -> Tuple[int, ...]:
        return protocols.qid_shape(self.sub_gate)

    def _value_equality_values_(self):
        return self.sub_gate, self.probability

    def _has_unitary_(self):
        return False

    def _has_mixture_(self):
        return not self._is_parameterized_() and protocols.has_mixture(
            self.sub_gate)

    def _has_channel_(self):
        return not self._is_parameterized_() and protocols.has_channel(
            self.sub_gate)

    def _is_parameterized_(self):
        return not isinstance(self.probability,
                              numbers.Number) or protocols.is_parameterized(
                                  self.sub_gate)

    def _resolve_parameters_(self, resolver):
        return RandomGateChannel(
            sub_gate=protocols.resolve_parameters(self.sub_gate, resolver),
            probability=protocols.resolve_parameters(self.probability,
                                                     resolver),
        )

    def _mixture_(self):
        if self._is_parameterized_():
            return NotImplemented

        mixture = protocols.mixture_channel(self.sub_gate, None)
        if mixture is None:
            return None

        do_nothing = np.eye(np.product(protocols.qid_shape(self.sub_gate)),
                            dtype=np.float64)
        result = [(p * float(self.probability), m) for p, m in mixture]
        result.append((1 - float(self.probability), do_nothing))
        return result

    def _channel_(self):
        if self._is_parameterized_():
            return NotImplemented

        channel = protocols.channel(self.sub_gate, None)
        if channel is None:
            return NotImplemented

        do_nothing = np.eye(np.product(protocols.qid_shape(self.sub_gate)),
                            dtype=np.float64)
        result = [e * np.sqrt(self.probability) for e in channel]
        result.append(np.sqrt(1 - float(self.probability)) * do_nothing)
        return result

    def _trace_distance_bound_(self) -> float:
        result = protocols.trace_distance_bound(self.sub_gate)
        if not self._is_parameterized_():
            result *= float(self.probability)
        return result

    def _json_dict_(self) -> Dict[str, Any]:
        return protocols.obj_to_dict_helper(self, ['sub_gate', 'probability'])

    @classmethod
    def _from_json_dict_(cls, sub_gate, probability, **kwargs):
        return cls(sub_gate=sub_gate, probability=probability)

    def _circuit_diagram_info_(self, args: 'cirq.CircuitDiagramInfoArgs'
                              ) -> Optional['cirq.CircuitDiagramInfo']:
        result = protocols.circuit_diagram_info(self.sub_gate, args, None)
        if result is None:
            return None
        wires = list(result.wire_symbols)
        if wires:
            wires[0] += f'[prob={args.format_real(self.probability)}]'
        return result.with_wire_symbols(wires)

    def __str__(self):
        return f'{self.sub_gate}[prob={self.probability}]'

    def __repr__(self):
        if self.probability == 1:
            return (f'cirq.RandomGateChannel('
                    f'sub_gate={self.sub_gate!r}, '
                    f'probability=1)')
        return (f'{self.sub_gate!r}.with_probability('
                f'{proper_repr(self.probability)})')
