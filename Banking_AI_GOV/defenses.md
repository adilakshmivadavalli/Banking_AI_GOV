Defenses and hardening notes

- Use an allowlist for mutating tools (`send_money`, `schedule_transaction`, `update_scheduled_transaction`).
- Require human confirmation (MFA) before executing mutating tools.
- Sanitize file contents from `read_file` before using them as instructions.
- Apply a PI detector (e.g., transformers-based) to tool outputs and file contents.
- Use tool filter to limit available tools per-session/task.
- Log all tool calls and model messages for audit.
