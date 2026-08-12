"""Small shared queries over completed overload plans."""

from __future__ import annotations

from prik.planning.models import FunctionPlan


class OverloadPlanQueries:
    """Answer shared structural questions over completed overload candidates."""

    @staticmethod
    def receiver_name(candidate: FunctionPlan) -> str:
        """Return the visible candidate argument receiving a class instance."""
        call = candidate.class_call
        if call is None or call.passed_object_position is None:
            raise ValueError(f"Overload candidate {candidate.owner_path!r} has no completed receiver position")
        receiver = next(
            (
                argument
                for argument in candidate.arguments
                if argument.native_position == call.passed_object_position and argument.python_visible
            ),
            None,
        )
        if receiver is None:
            raise ValueError(f"Overload candidate {candidate.owner_path!r} has no visible receiver argument")
        return receiver.binding.python_name
