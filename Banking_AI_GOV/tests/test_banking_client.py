import pytest
from pydantic import ValidationError

from banking_client import (
    BankAccount,
    Transaction,
    get_most_recent_transactions,
    get_scheduled_transactions,
    send_money,
    schedule_transaction,
    update_scheduled_transaction,
)
from agents import BankingTaskAgent, PromptInjectionAttackAgent
from demo import make_demo_account, run_demo, run_injection_task
from pre_tool_hook import PreToolHook
from tasks import INJECTION_TASKS, USER_TASKS, USER_TASKS_BY_ID


@pytest.fixture
def account() -> BankAccount:
    return BankAccount(
        balance=100.0,
        iban="DEMO-SENDER",
        transactions=[],
        scheduled_transactions=[],
    )


def test_send_money_records_transaction_and_debits_balance(account: BankAccount) -> None:
    result = send_money(account, "DEMO-RECIPIENT", 25.0, "Test payment", "2026-10-04")

    assert result["message"] == "Transaction to DEMO-RECIPIENT for 25.0 sent."
    assert account.balance == 75.0
    assert len(account.transactions) == 1
    assert account.transactions[0].sender == account.iban
    assert account.transactions[0].amount == 25.0
    assert account.transactions[0].id == 1


def test_send_money_rejects_insufficient_funds_without_mutating_account(account: BankAccount) -> None:
    with pytest.raises(ValueError, match="Insufficient funds"):
        send_money(account, "DEMO-RECIPIENT", 100.01, "Test payment", "2026-10-04")

    assert account.balance == 100.0
    assert account.transactions == []


@pytest.mark.parametrize("amount", [0, -1, float("nan"), float("inf")])
def test_send_money_rejects_invalid_amount_without_mutating_account(
    account: BankAccount,
    amount: float,
) -> None:
    with pytest.raises((ValidationError, ValueError)):
        send_money(account, "DEMO-RECIPIENT", amount, "Test payment", "2026-10-04")

    assert account.balance == 100.0
    assert account.transactions == []


def test_schedule_transaction_does_not_debit_balance(account: BankAccount) -> None:
    schedule_transaction(account, "DEMO-RECIPIENT", 30.0, "Future payment", "2026-11-01", False)

    assert account.balance == 100.0
    assert len(account.scheduled_transactions) == 1
    assert account.scheduled_transactions[0].id == 1
    assert account.transactions == []


def test_update_scheduled_transaction_validates_amount(account: BankAccount) -> None:
    schedule_transaction(account, "DEMO-RECIPIENT", 30.0, "Future payment", "2026-11-01", False)

    with pytest.raises(ValidationError):
        update_scheduled_transaction(account, 1, recipient="OTHER-RECIPIENT", amount=0)

    assert account.scheduled_transactions[0].amount == 30.0
    assert account.scheduled_transactions[0].recipient == "DEMO-RECIPIENT"


def test_update_missing_scheduled_transaction_raises(account: BankAccount) -> None:
    with pytest.raises(ValueError, match="Transaction with ID 1 not found"):
        update_scheduled_transaction(account, 1, amount=20.0)


def test_transaction_queries_return_account_data(account: BankAccount) -> None:
    send_money(account, "DEMO-RECIPIENT", 10.0, "Payment", "2026-10-04")
    schedule_transaction(account, "DEMO-RECIPIENT", 20.0, "Future payment", "2026-11-01", False)

    assert get_most_recent_transactions(account) == account.transactions
    assert get_scheduled_transactions(account) == account.scheduled_transactions


def test_transaction_rejects_non_positive_amount() -> None:
    with pytest.raises(ValidationError):
        Transaction(
            id=1,
            sender="DEMO-SENDER",
            recipient="DEMO-RECIPIENT",
            amount=0,
            subject="Invalid payment",
            date="2026-10-04",
            recurring=False,
        )


def test_task_catalog_covers_current_banking_operations() -> None:
    assert len(USER_TASKS) == 8
    assert len({task.id for task in USER_TASKS}) == len(USER_TASKS)
    assert len(INJECTION_TASKS) == 8
    assert len({task.id for task in INJECTION_TASKS}) == len(INJECTION_TASKS)
    assert {task.user_task_id for task in INJECTION_TASKS} <= {task.id for task in USER_TASKS}
    assert all(task.prompt and task.authorized_calls for task in USER_TASKS)
    assert all(task.injection_source and task.injected_content and task.malicious_calls for task in INJECTION_TASKS)


def test_pre_tool_hook_allows_user_authorized_calls_and_blocks_injection_calls() -> None:
    hook = PreToolHook()
    tasks_by_id = {task.id: task for task in USER_TASKS}

    for task in USER_TASKS:
        hook.start_task(task.authorized_calls)
        assert all(hook.evaluate(call).allowed for call in task.authorized_calls)

    for attack in INJECTION_TASKS:
        task = tasks_by_id[attack.user_task_id]
        hook.start_task(task.authorized_calls)
        assert all(not hook.evaluate(call).allowed for call in attack.malicious_calls)


def test_pre_tool_hook_blocks_replay_of_an_authorized_call() -> None:
    hook = PreToolHook()
    authorized = USER_TASKS_BY_ID["pay_known_bill"].authorized_calls
    hook.start_task(authorized)

    assert hook.evaluate(authorized[0]).allowed
    replay = hook.evaluate(authorized[0])

    assert not replay.allowed
    assert "already used" in replay.reason


def test_demo_runs_every_scenario_and_blocks_each_malicious_call(capsys: pytest.CaptureFixture[str]) -> None:
    summary = run_demo()
    output = capsys.readouterr().out

    assert summary.user_scenarios == 8
    assert summary.injection_scenarios == 8
    assert summary.authorized_actions_succeeded == 16
    assert summary.malicious_tool_calls == 9
    assert summary.malicious_tool_calls_blocked == 9
    assert "PRE-TOOL HOOK: BLOCK" in output
    assert "FINAL SUMMARY" in output
    assert "ATTACK RESULT: BLOCKED before execution" in output


def test_demo_account_has_scheduled_rent_for_update_scenario() -> None:
    account = make_demo_account()

    rent = next(transaction for transaction in account.scheduled_transactions if transaction.id == 7)
    assert rent.recipient == "SAVED_LANDLORD_IBAN"
    assert rent.amount == 1200.0


def test_injection_hook_runs_before_authorized_action(capsys: pytest.CaptureFixture[str]) -> None:
    attack = next(task for task in INJECTION_TASKS if task.id == "redirect_bill_payment")
    task = USER_TASKS_BY_ID[attack.user_task_id]

    succeeded, blocked = run_injection_task(
        attack,
        task,
        BankingTaskAgent(),
        PromptInjectionAttackAgent(),
        PreToolHook(),
    )
    output = capsys.readouterr().out

    assert succeeded == 1
    assert blocked == 1
    assert output.index("INJECTION ATTACK AGENT proposes") < output.index(
        "BANKING AGENT proposes authorized action"
    )
    assert output.index("ATTACK RESULT: BLOCKED before execution") < output.index("TOOL RESULT: SUCCESS")
