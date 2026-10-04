if __package__ == "Banking_AI_GOV":
    from .tasks import InjectionTaskExample, ToolCall, UserTaskExample
else:
    from tasks import InjectionTaskExample, ToolCall, UserTaskExample


class BankingTaskAgent:
    """Demo agent that maps a selected scenario to its user-authorized tool calls."""

    def propose(self, task: UserTaskExample) -> tuple[ToolCall, ...]:
        return task.authorized_calls


class PromptInjectionAttackAgent:
    """Adversarial test agent that turns a fixture into proposed tool calls."""

    def propose(self, task: InjectionTaskExample) -> tuple[ToolCall, ...]:
        return task.malicious_calls
