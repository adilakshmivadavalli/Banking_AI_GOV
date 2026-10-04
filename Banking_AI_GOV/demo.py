import json
from dataclasses import dataclass
from typing import Any

if __package__ == "Banking_AI_GOV":
    from .agents import BankingTaskAgent, PromptInjectionAttackAgent
    from .banking_client import (
        BankAccount,
        Transaction,
        get_balance,
        get_most_recent_transactions,
        get_scheduled_transactions,
        schedule_transaction,
        send_money,
        update_scheduled_transaction,
    )
    from .pre_tool_hook import HookDecision, PreToolHook
    from .tasks import INJECTION_TASKS, USER_TASKS, InjectionTaskExample, ToolCall, UserTaskExample
else:
    from agents import BankingTaskAgent, PromptInjectionAttackAgent
    from banking_client import (
        BankAccount,
        Transaction,
        get_balance,
        get_most_recent_transactions,
        get_scheduled_transactions,
        schedule_transaction,
        send_money,
        update_scheduled_transaction,
    )
    from pre_tool_hook import HookDecision, PreToolHook
    from tasks import INJECTION_TASKS, USER_TASKS, InjectionTaskExample, ToolCall, UserTaskExample


@dataclass(frozen=True)
class DemoSummary:
    user_scenarios: int
    injection_scenarios: int
    authorized_actions_succeeded: int
    malicious_tool_calls: int
    malicious_tool_calls_blocked: int


def make_demo_account() -> BankAccount:
    return BankAccount(
        balance=5000.00,
        iban="DEMO-CHECKING-001",
        transactions=[
            Transaction(
                id=1,
                sender="DEMO-CHECKING-001",
                recipient="SAVED_GROCERY_IBAN",
                amount=64.25,
                subject="Groceries",
                date="2026-10-01",
                recurring=False,
            ),
            Transaction(
                id=2,
                sender="DEMO-CHECKING-001",
                recipient="SAVED_CAFE_IBAN",
                amount=18.50,
                subject="Coffee",
                date="2026-10-02",
                recurring=False,
            ),
            Transaction(
                id=3,
                sender="SAVED_FRIEND_IBAN",
                recipient="DEMO-CHECKING-001",
                amount=45.00,
                subject="Dinner reimbursement",
                date="2026-10-03",
                recurring=False,
            ),
        ],
        scheduled_transactions=[
            Transaction(
                id=7,
                sender="DEMO-CHECKING-001",
                recipient="SAVED_LANDLORD_IBAN",
                amount=1200.00,
                subject="Monthly rent",
                date="2026-11-01",
                recurring=True,
            ),
        ],
    )


def execute_tool_call(account: BankAccount, call: ToolCall) -> Any:
    tools = {
        "get_balance": get_balance,
        "get_most_recent_transactions": get_most_recent_transactions,
        "get_scheduled_transactions": get_scheduled_transactions,
        "send_money": send_money,
        "schedule_transaction": schedule_transaction,
        "update_scheduled_transaction": update_scheduled_transaction,
    }
    try:
        tool = tools[call.name]
    except KeyError as error:
        raise ValueError(f"Unknown banking tool: {call.name}") from error
    return tool(account, **call.arguments)


def render_result(result: Any) -> str:
    if isinstance(result, list):
        result = [item.model_dump() if hasattr(item, "model_dump") else item for item in result]
    return json.dumps(result, indent=2, default=str)


def log_hook_decision(call: ToolCall, decision: HookDecision) -> bool:
    status = "ALLOW" if decision.allowed else "BLOCK"
    print(f"  PRE-TOOL HOOK: {status} {call}")
    print(f"    Reason: {decision.reason}")
    return decision.allowed


def run_user_task(task: UserTaskExample, agent: BankingTaskAgent, hook: PreToolHook) -> int:
    account = make_demo_account()
    hook.start_task(task.authorized_calls)
    print(f"\n{'=' * 78}\nUSER SCENARIO: {task.id}")
    print(f"User: {task.prompt}")
    succeeded = 0

    for call in agent.propose(task):
        print(f"  BANKING AGENT proposes: {call}")
        decision = hook.evaluate(call)
        if not log_hook_decision(call, decision):
            print("  TOOL RESULT: Not executed (blocked before the banking function).")
            continue
        try:
            result = execute_tool_call(account, call)
        except (TypeError, ValueError) as error:
            print(f"  TOOL RESULT: FAILED - {error}")
            continue
        succeeded += 1
        print(f"  TOOL RESULT: SUCCESS\n{render_result(result)}")

    print(f"  USER TASK RESULT: {'SUCCESS' if succeeded == len(task.authorized_calls) else 'FAILED'}")
    return succeeded


def run_injection_task(
    attack: InjectionTaskExample,
    task: UserTaskExample,
    agent: BankingTaskAgent,
    attack_agent: PromptInjectionAttackAgent,
    hook: PreToolHook,
) -> tuple[int, int]:
    account = make_demo_account()
    hook.start_task(task.authorized_calls)
    print(f"\n{'=' * 78}\nINJECTION SCENARIO: {attack.id} (user task: {task.id})")
    print(f"User: {task.prompt}")
    print(f"Untrusted source: {attack.injection_source}")
    print(f"Injected content: {attack.injected_content}")

    blocked = 0
    malicious_calls = attack_agent.propose(attack)
    for call in malicious_calls:
        print(f"  INJECTION ATTACK AGENT proposes: {call}")
        decision = hook.evaluate(call)
        if not log_hook_decision(call, decision):
            blocked += 1
            print("  ATTACK RESULT: BLOCKED before execution; account state unchanged by this call.")
            continue
        result = execute_tool_call(account, call)
        print(f"  ATTACK RESULT: EXECUTED (unexpected for this fixture)\n{render_result(result)}")

    succeeded = 0
    for call in agent.propose(task):
        print(f"  BANKING AGENT proposes authorized action: {call}")
        decision = hook.evaluate(call)
        if not log_hook_decision(call, decision):
            print("  TOOL RESULT: Not executed (blocked before the banking function).")
            continue
        try:
            result = execute_tool_call(account, call)
        except (TypeError, ValueError) as error:
            print(f"  TOOL RESULT: FAILED - {error}")
            continue
        succeeded += 1
        print(f"  TOOL RESULT: SUCCESS\n{render_result(result)}")

    print(
        "  SCENARIO RESULT: "
        f"{'AUTHORIZED TASK SUCCEEDED' if succeeded == len(task.authorized_calls) else 'AUTHORIZED TASK FAILED'}; "
        f"{blocked}/{len(malicious_calls)} malicious tool call(s) blocked"
    )
    return succeeded, blocked


def run_demo() -> DemoSummary:
    banking_agent = BankingTaskAgent()
    attack_agent = PromptInjectionAttackAgent()
    hook = PreToolHook()

    print("BANKING AI GOVERNANCE - PRE-TOOL INJECTION DEFENSE DEMO")
    print("Local, deterministic simulation only. No LLM, external API, or real account is used.")
    print(
        f"Running {len(USER_TASKS)} user scenarios and "
        f"{len(INJECTION_TASKS)} prompt-injection scenarios."
    )

    actions_succeeded = sum(run_user_task(task, banking_agent, hook) for task in USER_TASKS)
    attack_actions = 0
    blocked_actions = 0
    for attack in INJECTION_TASKS:
        task = next(task for task in USER_TASKS if task.id == attack.user_task_id)
        succeeded, blocked = run_injection_task(attack, task, banking_agent, attack_agent, hook)
        actions_succeeded += succeeded
        attack_actions += len(attack_agent.propose(attack))
        blocked_actions += blocked

    summary = DemoSummary(
        user_scenarios=len(USER_TASKS),
        injection_scenarios=len(INJECTION_TASKS),
        authorized_actions_succeeded=actions_succeeded,
        malicious_tool_calls=attack_actions,
        malicious_tool_calls_blocked=blocked_actions,
    )
    print(f"\n{'=' * 78}\nFINAL SUMMARY")
    print(f"User scenarios: {summary.user_scenarios}")
    print(f"Prompt-injection scenarios: {summary.injection_scenarios}")
    print(f"Authorized banking actions succeeded: {summary.authorized_actions_succeeded}")
    print(f"Malicious tool-call attempts: {summary.malicious_tool_calls}")
    print(f"Malicious tool-call attempts blocked pre-execution: {summary.malicious_tool_calls_blocked}")
    return summary


if __name__ == "__main__":
    run_demo()
