# Clippy Kernel Developer Guide

## Purpose

This document is the maintainer-oriented guide for the Clippy SWE implementation in this repository. It focuses on the code that exists today, the paths and defaults that matter in practice, and the parts of the surrounding repository that affect development, testing, and maintenance.

This guide is intentionally narrower than the general project README. Use it when you are changing the Clippy SWE CLI, its configuration model, or the supporting integration code under `autogen/cli`.

## Canonical documentation set

Use these documents as the maintained Clippy SWE documentation set:

- `CLIPPY_SWE_AGENT_GUIDE.md` for user-facing CLI behavior, configuration, commands, and limitations
- `CLIPPY_KERNEL_DEVELOPER_GUIDE.md` for maintainer-facing implementation and repository guidance
- `CLIPPY_SWE_EVALS.md` for evaluation scope, assertions, and documentation checks

Earlier summary, validation, parity, and Copilot integration notes have been consolidated into these three documents.

## Repository orientation

The repository is an AG2-based codebase with Clippy SWE added as a CLI-oriented layer. The main locations relevant to Clippy SWE are:

| Path | Purpose |
| --- | --- |
| `pyproject.toml` | Packaging, extras, console script entry point, pytest, ruff, and mypy configuration. |
| `autogen/cli/` | Clippy SWE implementation and adjacent integrations. This is the primary module surface for the CLI. |
| `autogen/mcp/clippy_kernel_tools.py` | Toolkit used by `ClippySWEAgent` when web and development tools are enabled. |
| `test/cli/test_clippy_swe_agent.py` | Current direct test coverage for Clippy SWE config defaults, task-history metadata, and shared Copilot path behavior. |
| `test/mcp/test_clippy_kernel_tools.py` | Coverage for the toolkit used by the agent. |
| `scripts/` | Lint, test, docs, and quickstart scripts used by maintainers and CI-style local verification. |
| `website/` | Documentation build sources used by the docs scripts in `scripts/`. |

## Packaging and installation surface

Ground truth for installation lives in `pyproject.toml`.

- Package name: `clippy-kernel`
- Python requirement: `>=3.10,<3.14`
- Console script: `clippy-swe = "autogen.cli:main"`

Useful extras for maintainers:

| Extra | Use |
| --- | --- |
| `dev` | Full contributor environment. Pulls in lint, test, types, docs, pre-commit, detect-secrets, and uv. |
| `openai` | Adds the OpenAI client. Useful for the default Copilot SDK client path and common AG2 model setups. |
| `mcp-proxy-gen` | Required for the Typer-based CLI import path in `autogen/cli/clippy_swe_cli.py`. Without it, `clippy-swe` falls back to an error message. |
| `windows-clippy-mcp` | Windows-specific automation dependencies. |
| `docs` | MkDocs and documentation build dependencies. |
| `copilot-sdk` | Optional dependencies used by `autogen/cli/copilot_sdk_client.py` and document-processing features. |

Practical installation examples:

```bash
# Contributor baseline for Clippy SWE work
pip install -e ".[dev,openai,mcp-proxy-gen]"

# CLI-focused environment
pip install -e ".[openai,mcp-proxy-gen]"

# Windows automation work
pip install -e ".[openai,mcp-proxy-gen,windows-clippy-mcp]"

# Docs build work
pip install -e ".[docs]"
```

## Clippy SWE module map under `autogen/cli`

The code under `autogen/cli` is split into a small set of concrete modules:

| Module | Role | Notes for maintainers |
| --- | --- | --- |
| `autogen/cli/__init__.py` | CLI entry-point shim | Exports `ClippySWEAgent`, `ClippySWEConfig`, and `main()`. |
| `autogen/cli/clippy_swe_agent.py` | Core config and task execution | Defines default path resolution, `ClippySWEConfig`, task history, agent initialization, task routing, and system status. |
| `autogen/cli/clippy_swe_cli.py` | Typer command surface | Implements commands such as `task`, `status`, `history`, `interactive`, `resolve-issue`, and document-oriented helpers. |
| `autogen/cli/copilot_sdk_client.py` | Provider abstraction boundary | Wraps OpenAI, Anthropic, Google, and a placeholder GitHub Copilot provider. |
| `autogen/cli/interactive_mode.py` | REPL-style interface | Adds `@file`, `!shell`, and slash-command handling around `ClippySWEAgent.execute_task()`. |
| `autogen/cli/github_integration.py` | Issue-resolution helper | Clones repos, fetches issue metadata, asks the agent for analysis, runs heuristic test commands, and can create a patch or PR. |
| `autogen/cli/document_processor.py` | Document and asset helper | Handles document analysis, PowerPoint generation, feature-spec generation, recording analysis, and Flux-backed image generation. |

## Actual execution model

The current execution model is AG2 multi-agent orchestration, not a direct wrapper over an official GitHub Copilot agent runtime.

### Initialization flow

`ClippySWEAgent` does the following during initialization:

1. Builds a shared Copilot session config from `ClippySWEConfig`.
2. Loads task history from disk.
3. Attempts to load `LLMConfig` from `llm_config_path` using `LLMConfig.from_json(...)`.
4. Optionally initializes `CopilotSDKClient` if `use_copilot_sdk=True`.
5. Optionally initializes `ClippyKernelToolkit`, including the optional WorkIQ wrapper and Microsoft 365 Copilot SDK tools when enabled.
6. Creates four `ConversableAgent` instances:
   - `software_engineer`
   - `system_administrator`
   - `researcher`
   - `task_coordinator`
7. Registers toolkit tools onto the initialized agents when a toolkit is present.

If the `LLMConfig` file is missing, the agent logs a warning and operates in limited mode. In practice, `execute_task()` fails immediately without an LLM configuration and records the failure in task history. This behavior is covered by `test/cli/test_clippy_swe_agent.py`.

### Task execution path

`ClippySWEAgent.execute_task()` is the main task runner.

For each task it:

1. Selects a subset of the four agents based on `task_type`.
2. Builds a single task message with:
   - task description
   - optional context fields
   - workspace path
   - project path
   - platform and Python version
   - a tool-count note when the toolkit was initialized
   - a WorkIQ hint when the optional workplace-query tool is enabled
   - an M365 Copilot SDK hint when the optional stable v1 SDK tools are enabled
3. Creates an `AutoPattern` with those agents.
4. Calls:

```python
run_group_chat(
    pattern=agent_pattern,
    messages=full_task,
    max_rounds=self.config.max_iterations,
)
```

This is the key point for maintainers: the current execution engine is `run_group_chat(...)` from AG2, using an `AutoPattern` over `ConversableAgent` instances. Clippy SWE is therefore a specialized orchestration layer on top of AG2 group chat primitives.

### Task-type routing

The routing logic in `_select_agents_for_task()` currently maps task types as follows:

| Task type | Agents |
| --- | --- |
| `coding` | engineer, researcher, coordinator |
| `system` | sysadmin, engineer, coordinator |
| `research` | researcher, engineer, coordinator |
| `general` | coordinator, engineer, researcher |
| `debug` | engineer, researcher, coordinator |
| `deploy` | sysadmin, engineer, coordinator |
| `test` | engineer, coordinator |
| `review` | engineer, researcher, coordinator |

`execute_windows_task()` does not introduce a separate engine. It adds Windows-specific context and then delegates to `execute_task(..., task_type="system")`.

### History and status output

The agent records task history through `TaskHistory`, which writes JSON to disk and attaches semantic envelope metadata. `get_system_status()` reports:

- platform and Python information
- optional `psutil` resource metrics
- agent initialization status
- Copilot-related path resolution
- recent task summaries

## Copilot SDK boundary and shared `~/.copilot` path resolution

### Shared path defaults

`ClippySWEConfig` uses `Path.home() / ".copilot"` as the shared configuration root. The defaults are:

| Setting | Shared default |
| --- | --- |
| `config_dir` | `~/.copilot` |
| `custom_agents_dir` | `~/.copilot/agents` |
| `skill_directories` | `~/.copilot/skills` |
| `mcp_config_path` | `~/.copilot/mcp-config.json` |
| `task_history_path` | `~/.copilot/clippy-kernel/task-history.json` |
| `interactive_session_path` | `~/.copilot/clippy-kernel/interactive-session.json` |
| `llm_config_path` | `~/.copilot/clippy-kernel/OAI_CONFIG_LIST` |

### Legacy workspace fallback behavior

The config deliberately preserves older workspace-local behavior when legacy files already exist. `_prefer_legacy_workspace_path(...)` prefers the workspace file over the shared path when the workspace file already exists.

That means these legacy files remain authoritative if present in the current working directory:

- `OAI_CONFIG_LIST`
- `.clippy_swe_history.json`
- `.clippy_session.json`

This fallback behavior is directly tested in `test/cli/test_clippy_swe_agent.py`.

### MCP config loading

`ClippySWEConfig.resolve_mcp_servers()` loads MCP server definitions from either:

1. explicit `mcp_servers` in config, or
2. the shared file at `mcp_config_path`

`_load_mcp_servers_from_path(...)` accepts several top-level shapes:

- `{ "mcpServers": { ... } }`
- `{ "servers": { ... } }`
- a direct top-level server map

Only objects that look like MCP server definitions are kept. The detection is based on keys such as `command`, `url`, `transport`, `args`, `env`, `headers`, or `type`.

### What the Copilot integration does today

The Copilot-related config currently acts as a configuration boundary and status surface more than a full execution backend.

- `ClippySWEAgent` can initialize `CopilotSDKClient` when `use_copilot_sdk=True`.
- `build_copilot_session_config()` assembles working directory, shared Copilot directories, disabled skills, and resolved MCP servers.
- `get_system_status()` exposes those resolved paths and server names.

However, task execution still goes through AG2 `run_group_chat(...)`.

In `autogen/cli/copilot_sdk_client.py`, the provider named `github_copilot` is not implemented as a distinct backend. `_send_github_copilot(...)` logs that GitHub Copilot API support is not yet available and falls back to the OpenAI path.

For maintainers, the important boundary is:

- shared `~/.copilot` paths are real and tested
- MCP config loading is real and tested
- Copilot provider execution is only partially implemented

## CLI command surface

`autogen/cli/clippy_swe_cli.py` currently exposes these commands:

- `task`
- `windows`
- `status`
- `history`
- `init`
- `interactive`
- `resolve-issue`
- `generate-ppt`
- `analyze-doc`
- `create-spec`
- `analyze-recording`
- `generate-image`
- `models`
- `version`

Notes that matter in maintenance work:

- The CLI is built with Typer, but the import guard currently requires the `mcp-proxy-gen` optional dependency group.
- `init` writes `.clippy_swe_config.json` into the chosen workspace.
- `interactive` uses `InteractiveSession`, which supports:
  - `@file` attachments
  - `!command` shell execution
  - slash commands such as `/clear`, `/model`, `/usage`, `/cwd`, `/resume`, `/files`, and `/detach`
- Shell commands in interactive mode are run with `subprocess.run(..., shell=True, timeout=30)`.

The `models` command deserves special attention. It writes model/provider values into a local `.clippy_swe_config.json`, but most other commands do not automatically read that file unless a user explicitly passes `--config`. Treat that command as local config-file editing, not as a guaranteed global setting.

## Extension points and notable supporting code

### Core extension points

If you are extending Clippy SWE itself, the main hooks are:

- `ClippySWEConfig` for new settings and default-path behavior
- `_initialize_agents()` for new specialized agent roles
- `_select_agents_for_task()` for new task-type routing
- `_prepare_task_message()` for additional execution context
- `get_system_status()` for exposing new diagnostics

### Toolkit integration

`ClippySWEAgent` now registers `ClippyKernelToolkit` tools onto each initialized `ConversableAgent`. In the current implementation, this is the live extension seam for tool-backed behaviors inside the Clippy SWE runtime.

The new optional WorkIQ path uses that seam by wrapping the external WorkIQ CLI as a toolkit tool rather than by relying on MCP metadata alone. That keeps the integration aligned with the current synchronous AG2 task path while still making Microsoft 365 workplace queries available when explicitly enabled in config.

The new optional Agents-M365Copilot path uses the same seam, but it loads the stable Microsoft 365 Copilot Python SDK either from installed packages or from a local repo checkout. The current implementation keeps the scope honest by exposing only stable v1 surfaces through toolkit tools and normalizing SDK model responses into plain dictionaries before they are returned to the agents.

### GitHub integration caveat

`autogen/cli/github_integration.py` is present, but it is not a complete autonomous issue-fixing pipeline.

Notable current behavior:

- cloning is real
- `gh issue view` is attempted if the GitHub CLI is present
- missing `gh` falls back to a mock issue payload
- test execution is heuristic across generic commands such as `pytest`, `npm test`, and `make test`
- `_apply_changes(...)` is currently a stub that logs a message and returns an empty changed-file list

Treat this module as partial infrastructure rather than a finished maintainer workflow.

### Document processor boundary

`autogen/cli/document_processor.py` provides adjacent functionality for:

- document analysis
- PowerPoint generation
- feature-spec generation
- recording analysis
- Flux-based image generation

This module depends on optional packages declared in `copilot-sdk` and on external services for image generation. It should be maintained as a sibling workflow, not confused with the core Clippy SWE execution path.

### Notable scripts

These scripts are worth knowing when working in this area:

| Script | Use |
| --- | --- |
| `scripts/lint.sh` | Runs `ruff check` and `ruff format`. |
| `scripts/test.sh` | Base pytest wrapper with duration reporting. |
| `scripts/test-skip-llm.sh` | Runs pytest while excluding provider-dependent and many optional-dependency test markers. |
| `scripts/test-core-skip-llm.sh` | Narrows `test-skip-llm.sh` further by ignoring `test/agentchat/contrib`. |
| `scripts/test-docs.sh` | Runs docs-marked tests through `test-skip-llm.sh -m "docs"`. |
| `scripts/docs_build_mkdocs.sh` | Builds docs from `website/mkdocs` via `python docs.py build`. |
| `scripts/docs_serve_mkdocs.sh` | Serves docs locally from `website/mkdocs` via `python docs.py live`. |
| `scripts/quickstart_clippy_swe.sh` | Bash quickstart script for local setup and usage examples. Treat it as convenience guidance, not as the canonical source of implementation details. |

## Testing and verification guidance

Use repository commands that match the actual automation in the repo.

### Minimum checks for Clippy SWE changes

```bash
bash scripts/lint.sh
pytest test/cli/test_clippy_swe_agent.py -v
pytest test/mcp/test_clippy_kernel_tools.py -v
```

### Broader local verification

```bash
bash scripts/test-core-skip-llm.sh
bash scripts/test-skip-llm.sh
bash scripts/test-docs.sh
```

### Docs verification

```bash
pip install -e ".[docs]"
bash scripts/docs_build_mkdocs.sh
```

### Type checking

The repository configures mypy in `pyproject.toml` with a targeted file list rather than checking everything by default. For deeper validation, run:

```bash
mypy
```

or use the existing helper:

```bash
bash scripts/pre-commit-mypy-run.sh
```

### Important test caveats

The repo test surface is broad, but Clippy SWE-specific coverage is still narrow.

Current direct tests in `test/cli/test_clippy_swe_agent.py` verify:

- semantic metadata is written to task history
- `execute_task()` records a failure when no LLM config is available
- shared `~/.copilot` defaults are used when workspace files are absent
- legacy workspace files remain preferred when they already exist
- shared MCP server definitions are loaded into session config

The existing skip-LLM scripts also exclude many optional-dependency and provider-marked suites. Passing those scripts is useful, but it does not prove that all document, GitHub, model-provider, or Windows automation paths are working.

## Known gaps and technical debt

These are current implementation realities that should stay visible to maintainers:

1. The guide and codebase are not fully aligned on presentation quality. Several CLI and helper modules still contain decorative rich markup and emoji-style output even though the underlying engineering behavior is what matters.
2. The GitHub Copilot provider path in `copilot_sdk_client.py` is a placeholder that falls back to OpenAI.
3. The `models` command edits `.clippy_swe_config.json`, but other commands do not consistently consume that file unless `--config` is passed explicitly.
4. `GitHubIntegration._apply_changes(...)` is stubbed and does not yet apply generated edits to the cloned repository.
5. `GitHubIntegration` falls back to a mock issue payload if the GitHub CLI is unavailable.
6. `ClippySWEAgent` now registers toolkit tools onto the initialized
   `ConversableAgent` instances during startup, but task execution still depends
   on the AG2 group-chat path rather than a separate tool-runtime abstraction.
7. Interactive shell execution uses `shell=True`, which is convenient but deserves review if that path becomes a hardened maintainer workflow.
8. Several adjacent workflows rely on optional dependencies and external credentials, especially document processing, Flux image generation, and alternate model providers.

## Maintaining this guide

When you update this document, verify claims against:

- `pyproject.toml`
- `autogen/cli/*.py`
- `scripts/*.sh`
- `test/cli/test_clippy_swe_agent.py`

Do not promote aspirational behavior to documented behavior. If a feature exists only as a config surface, placeholder, fallback, or partial helper, document it as such.
