# Clippy SWE Quick Start

## What this is

Clippy SWE is the repository's CLI and API layer for software-engineering workflows in
`autogen.cli`.

This quick start stays close to the current implementation:

- task execution goes through AG2 multi-agent orchestration
- Copilot SDK support is optional and partial
- Windows-specific entry points exist, but they are not a claim of dependable unattended desktop automation
- `resolve-issue` is not the primary quick-start path and should be treated as experimental

For maintained detail, use:

- [CLIPPY_SWE_AGENT_GUIDE.md](CLIPPY_SWE_AGENT_GUIDE.md)
- [CLIPPY_KERNEL_DEVELOPER_GUIDE.md](CLIPPY_KERNEL_DEVELOPER_GUIDE.md)
- [CLIPPY_SWE_EVALS.md](CLIPPY_SWE_EVALS.md)

## Prerequisites

- Python 3.10 to 3.13
- a configured model provider if you want `task` execution to succeed
- Windows only if you plan to try the `windows` command

## Install

### Preferred path: Manual install

CLI baseline:

```bash
pip install -e ".[openai,mcp-proxy-gen]"
```

Optional extras for broader local experimentation:

```bash
pip install -e ".[openai,copilot-sdk,windows-clippy-mcp,mcp-proxy-gen,browser-use]"
```

NOTE: `pyproject.toml` does not currently define standalone `anthropic` or
`gemini` extras. Anthropic and Google support for the optional Copilot-style
client path come in through `copilot-sdk`.

## Configure model access

The agent can use an `OAI_CONFIG_LIST` JSON file. A minimal example:

```json
[
  {
    "model": "gpt-4",
    "api_key": "your-api-key"
  }
]
```

Common locations are documented in `CLIPPY_SWE_AGENT_GUIDE.md`. If no usable LLM
configuration is found, task execution fails with:

```text
Cannot execute task without LLM configuration
```

## First commands

Initialize a workspace config:

```bash
clippy-swe init --workspace .
```

Check status:

```bash
clippy-swe status
```

Run a safe research task:

```bash
clippy-swe task "Summarize the repository layout and highlight Clippy SWE entry points" --type research
```

Run with observer output if you want to inspect the local orchestration flow:

```bash
clippy-swe task "Review likely CLI files for documentation drift" --type review --observer
```

Start interactive mode:

```bash
clippy-swe interactive
```

Inspect recent history:

```bash
clippy-swe history --limit 5
```

List model presets managed by the CLI:

```bash
clippy-swe models --list
```

## Windows command

The `windows` command is a Windows-only entry point that adds Windows-focused context
to a system task.

Example:

```bash
clippy-swe windows "Summarize current system status and suggest what to inspect next"
```

Use it as a manual, implementation-dependent workflow rather than as a promise of
fully reliable native desktop automation.

## Troubleshooting

### CLI imports fail

Install the CLI dependency extra:

```bash
pip install -e ".[mcp-proxy-gen]"
```

### Task execution fails immediately

Check your LLM configuration path and contents. The most common failure is missing
model configuration.

### You need deeper usage or maintainer detail

Go to the canonical docs:

- [CLIPPY_SWE_AGENT_GUIDE.md](CLIPPY_SWE_AGENT_GUIDE.md)
- [CLIPPY_KERNEL_DEVELOPER_GUIDE.md](CLIPPY_KERNEL_DEVELOPER_GUIDE.md)
- [CLIPPY_SWE_EVALS.md](CLIPPY_SWE_EVALS.md)
