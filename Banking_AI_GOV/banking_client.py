from pydantic import BaseModel, ConfigDict, Field


class Transaction(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: int = Field(..., title="ID of the transaction")
    sender: str = Field(..., title="IBAN of the sender")
    recipient: str = Field(..., title="IBAN of the recipient")

    amount: float = Field(..., gt=0, allow_inf_nan=False, title="Amount of the transaction")
    subject: str = Field(..., title="Subject of the transaction")

    date: str = Field(..., title="Date of the transaction")
    recurring: bool = Field(..., title="Is the transaction recurring")


class BankAccount(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    balance: float = Field(..., ge=0, allow_inf_nan=False)
    iban: str
    transactions: list[Transaction]
    scheduled_transactions: list[Transaction]


def next_id(account: BankAccount) -> int:
    return (
        max([t.id for t in account.transactions] + [t.id for t in account.scheduled_transactions], default=0) + 1
    )


def get_iban(account: BankAccount) -> str:
    return account.iban


def send_money(account: BankAccount, recipient: str, amount: float, subject: str, date: str) -> dict:
    if amount > account.balance:
        raise ValueError("Insufficient funds.")

    transaction = Transaction(
        id=next_id(account),
        sender=get_iban(account),
        recipient=recipient,
        amount=amount,
        subject=subject,
        date=date,
        recurring=False,
    )
    account.balance -= amount
    account.transactions.append(transaction)
    return {"message": f"Transaction to {recipient} for {amount} sent."}


def schedule_transaction(account: BankAccount, recipient: str, amount: float, subject: str, date: str, recurring: bool) -> dict:
    transaction = Transaction(
        id=next_id(account),
        sender=get_iban(account),
        recipient=recipient,
        amount=amount,
        subject=subject,
        date=date,
        recurring=recurring,
    )
    account.scheduled_transactions.append(transaction)
    return {"message": f"Transaction to {recipient} for {amount} scheduled."}


def update_scheduled_transaction(account: BankAccount, id: int, recipient: str | None = None, amount: float | None = None, subject: str | None = None, date: str | None = None, recurring: bool | None = None) -> dict:
    transaction = next((t for t in account.scheduled_transactions if t.id == id), None)
    if transaction:
        updates = {
            key: value
            for key, value in {
                "recipient": recipient,
                "amount": amount,
                "subject": subject,
                "date": date,
                "recurring": recurring,
            }.items()
            if value is not None
        }
        validated = Transaction.model_validate(transaction.model_dump() | updates)

        if recipient is not None:
            transaction.recipient = validated.recipient
        if amount is not None:
            transaction.amount = validated.amount
        if subject is not None:
            transaction.subject = validated.subject
        if date is not None:
            transaction.date = validated.date
        if recurring is not None:
            transaction.recurring = validated.recurring
    else:
        raise ValueError(f"Transaction with ID {id} not found.")
    return {"message": f"Transaction with ID {id} updated."}


def get_balance(account: BankAccount) -> float:
    return account.balance


def get_most_recent_transactions(account: BankAccount, n: int = 100) -> list[Transaction]:
    return [t for t in account.transactions[-int(n) :]]


def get_scheduled_transactions(account: BankAccount) -> list[Transaction]:
    return [t for t in account.scheduled_transactions]
