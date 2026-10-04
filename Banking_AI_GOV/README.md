# Banking_AI_GOV

Minimal extract from AgentDojo for BFSI AI governance benchmarking and defenses.

Contents:
- `banking_client.py`: sandboxed banking tool implementations.
- `tasks.py`: example user & injection tasks for benchmarking.
- `defenses.md`: notes and pointers to integrate detection and tool filters.

Usage:
- Review and harden `banking_client.py` before connecting to any real services.
- Use `tasks.py` injection cases as unit tests for prompt-injection defenses.
