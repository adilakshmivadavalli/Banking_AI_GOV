# Banking AI Governance Demo

A self-contained local demo of banking assistant tasks, prompt-injection
attempts, and a deterministic pre-tool defense hook. It creates synthetic
accounts and never connects to a bank, an LLM provider, or an external service.

## Run the full demo

From this directory:

```powershell
python demo.py
```

The demo runs all eight benign banking tasks and all eight injection scenarios.
For each scenario it prints the user request, any untrusted injected content,
the agent's proposed tool calls, the pre-tool hook's allow/block decision, tool
results, and a final summary. One injection case makes two malicious call
proposals, so the summary reports nine attempted malicious calls.

To run the tests:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

Only the `pydantic` runtime dependency and `pytest` test dependency are needed.

## Demo agents and defense

- `agents.py` contains a deterministic banking task agent and an injection
  attack agent. These scenario-driven agents make the demo reproducible and do
  not call an LLM.
- `pre_tool_hook.py` checks every proposed call before execution. A call is
  allowed only when its tool name and complete arguments exactly match an
  unused call authorized by the selected user task. Each authorization can be
  consumed only once, preventing a duplicate-call replay.
- `demo.py` runs the user-authorized actions and then runs adversarial proposals
  against the same authorization policy, printing an auditable trace.
- `tasks.py` defines eight user tasks and eight related injection scenarios.
- `banking_client.py` provides the in-memory banking tools and models.
- `tests/` checks account behavior, the allow/block decisions, and the full
  demo summary.

## Scope and limitations

This is a hackathon demonstration, not a production banking control. Its agent
proposals are pre-authored fixtures rather than model-generated decisions.
The pre-tool hook demonstrates exact task-scoped allowlisting; it is not a
general-purpose prompt-injection detector and does not provide identity
verification, durable authorization, human approval, audit storage, or
regulatory compliance. A production design would require independently enforced
authorization and policy checks at the trusted tool boundary.

The folder is self-contained and can be copied or submitted as the root of a
standalone repository. The parent repository currently also contains the
upstream AgentDojo project; its files are not needed to run this demo.
