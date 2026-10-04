from dataclasses import dataclass
from typing import Sequence

if __package__ == "Banking_AI_GOV":
    from .tasks import ToolCall
else:
    from tasks import ToolCall


@dataclass(frozen=True)
class HookDecision:
    allowed: bool
    reason: str


class PreToolHook:
    """Allow each exact tool call authorized by the selected user task at most once."""

    def __init__(self) -> None:
        self._pending: list[ToolCall] = []

    def start_task(self, authorized: Sequence[ToolCall]) -> None:
        self._pending = list(authorized)

    def evaluate(self, proposed: ToolCall) -> HookDecision:
        if proposed in self._pending:
            self._pending.remove(proposed)
            return HookDecision(True, "Exact match for a tool call authorized by the user task.")
        return HookDecision(
            False,
            "No unused exact match for a user-authorized tool call; the call may be unauthorized or already used.",
        )
