"""
Defines base classes for model outputs, snapshots, snapshot generating callback, and snapshot builder.

The snapshot builder is used to compile multiple snapshot generating callbacks into a single callable
that generates a total snapshot.

Attributes:
    Output (Union[str, Number]): Defines the types of outputs a model should generate
    Snapshot (dict[str, Output]): Defines what is considered a model snapshot
    SnapshotGeneratingCallback (Callable[[], Snapshot]): Defines the signature of a snapshot generating callable 
        (no arguments and returns a [Snapshot][dynamics_engine.snapshot_builder.Snapshot])
"""
from __future__ import annotations

# Standard package imports
Number = float|int
from typing import Callable, Union

# Local package imports
from djin.type_annotations import Self

__all__ = ['Output', 'Snapshot', 'SnapshotGeneratingCallback', 'SnapshotBuilder']

# Type Definitions
Output = Union[str, Number]
"""
Output defines what scalar types can be output from a dynamic simulation (for the purposes of type hinting).

These are defined to be either a [str][] or a [Number][numbers.Number]
"""
Snapshot = dict[str, Output]
"""
[Snapshot][dynamics_engine.snapshot_builder.Snapshot] is a dict of string keys and [Output][dynamics_engine.snapshot_builder.Output] values.
"""
SnapshotGeneratingCallback = Callable[[], Snapshot]
"""
[SnapshotGeneratingCallback][dynamics_engine.snapshot_builder.SnapshotGeneratingCallback] is a 
Nullary function (no argument function) that returns a [Snapshot][dynamics_engine.snapshot_builder.Snapshot].
"""

class SnapshotBuilder:
    """
    Registers multiple 
    [SnapshotGeneratingCallback][dynamics_engine.snapshot_builder.SnapshotGeneratingCallback]s 
    to be iteratively evaluated with 
    return values compiled into a single snapshot (dict).
    """
    def __init__(self) -> None:
        self._callbacks: list[SnapshotGeneratingCallback] = []

    def register_snapshot_generating_callback(
            self, 
            callback: SnapshotGeneratingCallback,
        ) -> Self:
        """
        Registers a snapshot generating callback to the list of internally stored callbacks

        Args:
            callback (SnapshotGeneratingCallback): A callback to be evaluated as part of the memory snapshot

        Returns:
            (Self): SnapshotBuilder instance to which the callback was registered.
        """
        # try:
        #     assert name not in self._callbacks.keys()
        # except AssertionError:
        #     raise ValueError(f'Callback {name = } conflicts with previously registered callback.  You must use a unique name.')
        # self._callbacks[name] = callback
        self._callbacks.append(callback)
        return self

    def get_snapshot(self) -> Snapshot:
        """
        Returns a cobined memory snapshot and 
        raises exception if dictionary keys conflict between snapshot generator callbacks.

        Returns:
            (Snapshot): Cobined snapshot of all registered snapshot generator callbacks.
                Raises exception if dictionary keys conflict between snapshot returns.
        """
        evaluated_callbacks = [callback() for callback in self._callbacks]
        total_snapshot = {}
        for partial_snapshot in evaluated_callbacks:
            used_keys = total_snapshot.keys()
            for key in partial_snapshot.keys():
                try:
                    assert key not in used_keys
                except AssertionError:
                    raise ValueError(f'Snapshot conflict for {key = }')
            total_snapshot.update(partial_snapshot)
        return total_snapshot