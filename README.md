# Banking AI Governance

A small, local prototype for exploring AI governance and prompt-injection risks
in banking workflows. It includes an in-memory banking tool model, illustrative
user and injection scenarios, and notes on possible defenses.

> **Prototype only:** This repository does not connect to a bank or implement
> production-grade financial controls. Do not use it with real accounts,
> credentials, or transactions.

## Quickstart

The standalone banking demo and its dependencies are contained in
[`Banking_AI_GOV/`](Banking_AI_GOV/). Enter that directory to run it:

```powershell
cd Banking_AI_GOV
python demo.py
```

Install the project's test dependencies and run its tests:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

For background on the original AgentDojo framework code also present in this
repository, see [`src/`](src/). The banking prototype itself is in
[`Banking_AI_GOV/`](Banking_AI_GOV/).

## What's included

- `Banking_AI_GOV/banking_client.py`: in-memory account and transaction tools.
- `Banking_AI_GOV/tasks.py`: runnable benign and prompt-injection scenarios.
- `Banking_AI_GOV/pre_tool_hook.py`: exact user-task authorization check before
  tool execution.
- `Banking_AI_GOV/agents.py`: deterministic demo banking and attack agents.
- `Banking_AI_GOV/defenses.md`: candidate defense and audit-control ideas.
- `Banking_AI_GOV/demo.py`: a runnable local example.
- `Banking_AI_GOV/tests/`: tests for scenarios, tool behavior, and defense.

## Scope and limitations

The demo uses a deterministic pre-tool allowlist to block proposals that do not
exactly match the selected user task. The attack and task agents use
pre-authored fixtures; they do not invoke an LLM. This does not provide
production authentication, durable authorization, human approval, audit
storage, regulatory compliance, or integration with any banking provider. Its
floating-point amounts and in-memory state are for demonstrations only, not
financial accounting.

See [`Banking_AI_GOV/README.md`](Banking_AI_GOV/README.md) for details about the
prototype and its scenarios.
