# Clippy SWE Agent Guide

## What Clippy SWE is

Clippy SWE is a Python CLI and API layer in `autogen.cli` for running multi-agent software engineering workflows on top of clippy-kernel. It exposes task execution, an interactive session, task history, basic GitHub issue workflow automation, a Windows-oriented task entry point, and several document or media helper commands.

The implementation is centered on:

- `autogen/cli/clippy_swe_cli.py` for CLI commands
- `autogen/cli/clippy_swe_agent.py` for configuration, task orchestration, history, and status
- `autogen/cli/interactive_mode.py` for the interactive shell
- `autogen/cli/github_integration.py` for `resolve-issue`
- `autogen/cli/document_processor.py` for document and media helpers

This guide is intentionally conservative. It documents what the current code does, and it calls out areas that are partial, placeholder-level, or dependent on optional extras.

## Current capability summary

Implemented and usable:

- Task execution through `clippy-swe task`
- Interactive mode with:
  - plain prompts
  - `@file` attachments
  - `!command` local shell execution
  - slash commands such as `/clear`, `/model`, `/usage`, `/cwd`, `/resume`, `/files`, `/detach`, `/help`
- Task history and status inspection
- Workspace config bootstrap with `init`
- Model listing and local default selection with `models`
- Version display with `version`
- Document and media helper commands:
  - `generate-ppt`
  - `analyze-doc`
  - `create-spec`
  - `analyze-recording`
  - `generate-image`

Implemented but partial or experimental:

- `resolve-issue`
- `windows`
- background mode flag on `task`
- interactive `/model`
- recording transcription when no transcript file is supplied
- PowerPoint outline generation and diagram or image insertion flows

## Installation

## Base CLI

The CLI depends on the `mcp-proxy-gen` extra for Typer and related command-line dependencies.

```bash
pip install -e ".[mcp-proxy-gen]"
```

If that extra is missing, the command falls back to an error telling you to install:

```bash
pip install -e ".[mcp-proxy-gen]"
```

## Provider and SDK extras

Install only the extras that exist in `pyproject.toml` and match the path you
plan to exercise.

```bash
pip install -e ".[mcp-proxy-gen,openai]"
pip install -e ".[mcp-proxy-gen,copilot-sdk]"
```

Notes:

- `openai` installs the OpenAI SDK used by the common `OAI_CONFIG_LIST` path and
  the optional client wrapper.
- `copilot-sdk` pulls in Anthropic, Google, and document-processing
  dependencies used by the optional Copilot-style client path and the media
  commands.
- There are no standalone `anthropic` or `gemini` extras in the current
  `pyproject.toml`.
- `use_copilot_sdk` is optional. The agent can also load an `OAI_CONFIG_LIST` via `LLMConfig.from_json(...)`.

## Windows and browser-related extras

```bash
pip install -e ".[mcp-proxy-gen,windows-clippy-mcp]"
pip install -e ".[mcp-proxy-gen,browser-use]"
```

Notes:

- `windows-clippy-mcp` installs dependencies associated with Windows MCP integration.
- The current `windows` command does not directly drive a native automation runtime by itself; see limitations below.
- `browser-use` is optional and not required for the documented core commands.

## Suggested full install for local evaluation

```bash
pip install -e ".[mcp-proxy-gen,openai,copilot-sdk,windows-clippy-mcp,browser-use]"
```

## Configuration

## Shared Copilot defaults

`ClippySWEConfig` resolves several defaults from the shared Copilot home directory:

- `~/.copilot/clippy-kernel/OAI_CONFIG_LIST`
- `~/.copilot/clippy-kernel/task-history.json`
- `~/.copilot/clippy-kernel/interactive-session.json`
- `~/.copilot/mcp-config.json`
- `~/.copilot/skills`
- `~/.copilot/agents`

These defaults come from:

- `_default_llm_config_path()`
- `_default_task_history_path()`
- `_default_interactive_session_path()`
- `_default_mcp_config_path()`
- `_default_skill_directories()`
- `_default_custom_agents_dir()`

## Legacy workspace fallback

For backward compatibility, existing workspace-local files are preferred over the shared paths when they already exist:

- `./OAI_CONFIG_LIST`
- `./.clippy_swe_history.json`
- `./.clippy_session.json`

That fallback is implemented by `_prefer_legacy_workspace_path(...)`.

Important distinction:

- shared defaults are used automatically when no legacy workspace file exists
- `clippy-swe init` still writes `./.clippy_swe_config.json` in the target workspace
- `clippy-swe models` also reads and writes `./.clippy_swe_config.json`
- most commands still construct `ClippySWEConfig()` directly and do not automatically consume `./.clippy_swe_config.json`
- use `--config` on commands that support it when you want that workspace-local file to drive runtime behavior

## Initialize a workspace config

```bash
clippy-swe init --workspace .
```

This writes `.clippy_swe_config.json` in the chosen workspace and prints the resolved `OAI_CONFIG_LIST` path plus the shared Copilot config root.

Use `--force` to overwrite an existing workspace config.

## Minimal configuration example

```json
{
  "llm_config_path": "C:/Users/you/.copilot/clippy-kernel/OAI_CONFIG_LIST",
  "use_copilot_sdk": false,
  "copilot_model": "gpt-4",
  "copilot_provider": "openai",
  "observer_mode": false,
  "background_mode": false,
  "max_iterations": 50,
  "workspace_path": ".",
  "enable_windows_automation": true,
  "enable_app_interaction": true,
  "enable_web_tools": true,
  "enable_workiq": false,
  "workiq_command": "npx",
  "workiq_package": "@microsoft/workiq@latest",
  "workiq_tenant_id": null,
  "workiq_timeout": 120,
  "enable_m365_copilot": false,
  "m365_copilot_repo_path": null,
  "m365_copilot_tenant_id": null,
  "m365_copilot_client_id": null,
  "m365_copilot_credential_mode": "default",
  "m365_copilot_default_user_id": null,
  "m365_copilot_scopes": ["https://graph.microsoft.com/.default"],
  "enable_code_execution": true,
  "save_conversation_history": true
}
```

## LLM configuration

If you are not using direct provider keys through the Copilot SDK path, create an `OAI_CONFIG_LIST` JSON file. Example:

```json
[
  {
    "model": "gpt-4",
    "api_key": "your-api-key"
  }
]
```

If the resolved LLM config file is missing, the agent logs a warning and task execution runs in limited mode. In practice, `task` and related commands that need model execution will fail with:

```text
Cannot execute task without LLM configuration
```

## MCP configuration

If `mcp_servers` is not set directly in `.clippy_swe_config.json`, the config attempts to load MCP server definitions from `~/.copilot/mcp-config.json`.

Recognized layouts include:

- `{ "mcpServers": { ... } }`
- `{ "servers": { ... } }`
- a top-level server map

If the file exists but is not a recognized JSON object, it is ignored with a warning.

## Optional WorkIQ integration

Clippy SWE can expose a WorkIQ-backed `ask_work_iq` tool through the runtime toolkit when `enable_workiq` is set to `true`.

Prerequisites:

- Node.js 18+ so `npx` is available
- access to the WorkIQ CLI package
- accepted WorkIQ EULA
- tenant consent for the required Microsoft 365 permissions

Relevant config fields:

- `enable_workiq`
- `workiq_command`
- `workiq_package`
- `workiq_tenant_id`
- `workiq_timeout`

Example:

```json
{
  "enable_workiq": true,
  "workiq_command": "npx",
  "workiq_package": "@microsoft/workiq@latest",
  "workiq_tenant_id": "your-tenant-id",
  "workiq_timeout": 120
}
```

When enabled, the task runtime can use `ask_work_iq` for Microsoft 365 workplace questions about emails, meetings, documents, Teams messages, and people.

## Optional Agents-M365Copilot SDK integration

Clippy SWE can also expose stable Microsoft 365 Copilot SDK tools through the runtime toolkit when `enable_m365_copilot` is set to `true`.

This support is intentionally scoped to the stable v1 Python SDK surfaces that can be supported honestly in the current runtime:

- retrieval
- usage reports
- AI users
- interaction history
- admin settings
- user online meetings

Prerequisites:

- `azure-identity` available in the environment
- Microsoft 365 Copilot API access in the target tenant
- a valid Azure credential source
  - Azure CLI sign-in for `m365_copilot_credential_mode: "default"`, or
  - device-code auth with `m365_copilot_client_id`
- Microsoft 365 Copilot licensing in the tenant and user context
- either:
  - installed `microsoft-agents-m365copilot` and `microsoft-agents-m365copilot-core` packages, or
  - a local `Agents-M365Copilot` checkout referenced by `m365_copilot_repo_path`

Relevant config fields:

- `enable_m365_copilot`
- `m365_copilot_repo_path`
- `m365_copilot_tenant_id`
- `m365_copilot_client_id`
- `m365_copilot_credential_mode`
- `m365_copilot_default_user_id`
- `m365_copilot_scopes`

Example:

```json
{
  "enable_m365_copilot": true,
  "m365_copilot_repo_path": "E:/Agents-M365Copilot",
  "m365_copilot_tenant_id": "your-tenant-id",
  "m365_copilot_client_id": "your-app-client-id",
  "m365_copilot_credential_mode": "device_code",
  "m365_copilot_default_user_id": "your-ai-user-id",
  "m365_copilot_scopes": ["https://graph.microsoft.com/.default"]
}
```

When enabled, the runtime toolkit can expose:

- `m365_copilot_retrieve`
- `m365_copilot_list_users`
- `m365_copilot_get_user`
- `m365_copilot_list_interactions`
- `m365_copilot_list_user_online_meetings`
- `m365_copilot_get_admin_settings`
- `m365_copilot_get_usage_report`

Notes:

- the retrieval builder in the upstream SDK currently emits a preview/deprecation warning; Clippy surfaces that warning instead of hiding it
- this integration does not claim beta endpoint coverage or change-notification webhook support
- if the SDK is not installed, `m365_copilot_repo_path` should point at the local `Agents-M365Copilot` repo root or its `python/packages` directory

## Core commands

## `task`

Runs a multi-agent workflow.

```bash
clippy-swe task "Summarize this Python package" --type research
clippy-swe task "Review auth.py for bugs" --type review --project .
clippy-swe task "Draft a test plan for the CLI" --type test --observer
```

Supported task types in the code:

- `general`
- `coding`
- `system`
- `research`
- `debug`
- `deploy`
- `test`
- `review`

Notes:

- agent selection is a fixed mapping in `_select_agents_for_task(...)`
- observer mode only prints progress text to stdout
- the `--background` flag only suppresses some foreground UI printing; it does not start a detached background worker or true asynchronous job

Background caveat:

- `task` still creates `ClippySWEAgent(...)` and calls `agent.execute_task(...)` synchronously
- there is no queue, worker process, PID handoff, or resumable job handle
- treat `--background` as a reduced-output mode, not real background execution

## `interactive`

Starts a local interactive shell.

```bash
clippy-swe interactive
clippy-swe interactive --session ./.session.json
```

Supported features:

- normal prompts routed through `agent.execute_task(...)`
- `@file.py` to attach files for context
- `!git status` or other local shell commands
- slash commands:
  - `/clear`
  - `/model [name]`
  - `/usage`
  - `/cwd`
  - `/resume`
  - `/files`
  - `/detach`
  - `/help`

Important caveats:

- `!command` runs through `subprocess.run(..., shell=True, timeout=30)`, so it is local, synchronous, and capped at 30 seconds
- attached file contents are truncated to 5000 characters per file when added to context
- `/model` only updates `self.current_model` inside the interactive session UI state
- `/model` does not reconfigure the underlying agent instance, reload provider settings, or switch the runtime model used by `execute_task(...)`

Use `/model` as a session note only, not as a reliable runtime model switch.

## `resolve-issue`

Attempts a GitHub issue workflow:

```bash
clippy-swe resolve-issue owner/repo 123 --no-pr
clippy-swe resolve-issue owner/repo 123 --create-pr --token YOUR_TOKEN
```

What the current implementation actually does:

1. clones the repository into a temporary workspace
2. fetches issue data with `gh issue view ...` when available
3. falls back to a mock issue body if `gh` is unavailable
4. asks the agent to analyze the issue and propose a solution
5. runs a placeholder `_apply_changes(...)`
6. tries common test commands
7. generates a patch from `git diff HEAD`
8. optionally creates a branch, commit, push, and PR

Important caveats:

- this command is partial and experimental
- `_apply_changes(...)` is explicitly a simplified stub and currently does not parse LLM output into file edits
- `changed_files` will generally remain empty
- PR creation only proceeds when a patch exists and tests pass
- issue fetching may use a mock issue object if `gh` is not available

Treat `resolve-issue` as an experimental scaffold, not a dependable unattended issue-fixing pipeline.

## `windows`

Routes a task through the system-task path with Windows-oriented context.

```bash
clippy-swe windows "Open Notepad and summarize a log file"
clippy-swe windows "Check current CPU usage" --app "Task Manager"
```

What it currently does:

- validates that Windows automation is enabled and the OS is Windows
- adds context such as:
  - `platform: Windows`
  - `app_interaction: true/false`
  - `target_application` when `--app` is provided
- calls `execute_task(..., task_type="system")`

Important caveat:

- this is not a full native automation layer in the current implementation
- the command does not directly invoke a concrete Windows UI automation backend from `clippy_swe_cli.py` or `clippy_swe_agent.py`
- it is best understood as a Windows-focused prompt wrapper around the same multi-agent execution path

## `status`

Shows runtime and environment status.

```bash
clippy-swe status
clippy-swe status --verbose
```

Current output includes:

- platform and Python version
- whether the agent initialized
- whether an LLM config loaded
- autonomous mode flag
- agent count
- CPU and memory when `psutil` is available
- recent tasks in verbose mode

## `history`

Reads task history stored in the configured history file.

```bash
clippy-swe history
clippy-swe history --limit 20
clippy-swe history --id 3 --verbose
```

Notes:

- default history path is shared under `~/.copilot/clippy-kernel/task-history.json`
- an existing workspace-local `.clippy_swe_history.json` is preferred over that shared path

## `init`

Bootstraps a workspace-local `.clippy_swe_config.json`.

```bash
clippy-swe init --workspace .
clippy-swe init --workspace . --force
```

Use this when you want a workspace-specific config even though some defaults now resolve through `~/.copilot`.

Important caveat:

- `init` creates the file, but it does not make that file active everywhere
- `task` and `interactive` only use it when you pass `--config`
- `status` does not accept `--config` and reports the default runtime config for that invocation

## `models`

Lists hard-coded model names and stores a local default in `.clippy_swe_config.json`.

```bash
clippy-swe models --list
clippy-swe models --set gpt-4 --provider openai
clippy-swe models --current
```

Current behavior:

- `--list` prints a hard-coded provider-to-model map
- `--set` writes `copilot_model`, `copilot_provider`, and `use_copilot_sdk: true` into `./.clippy_swe_config.json`
- `--current` reads `./.clippy_swe_config.json` if present, otherwise prints built-in defaults

Caveats:

- this command writes only to the workspace-local config file
- most other commands still ignore that file unless you pass `--config`
- it does not validate that credentials exist for the chosen provider
- it does not probe the provider API for actual availability
- interactive `/model` and `clippy-swe models --set ...` are separate mechanisms

## `version`

Prints the package version.

```bash
clippy-swe version
```

This reads `autogen.version.__version__` when available and otherwise prints a development-version message.

## Document and media commands

These commands are implemented in `document_processor.py`. They are useful helpers, but several parts are lightweight or placeholder-driven.

## `generate-ppt`

Creates a `.pptx` from text, files, or a mix of both.

```bash
clippy-swe generate-ppt notes.md --title "Sprint summary" --output sprint-summary.pptx
clippy-swe generate-ppt brief.txt metrics.xlsx --no-images --output report.pptx
```

What it currently supports:

- text and markdown files as direct text sources
- PDF and DOCX via document analysis
- image files as source inputs
- basic title slide and generated content slides via `python-pptx`

Caveats:

- slide outline generation is only partially implemented
- `_generate_presentation_outline(...)` currently falls back to a fixed 8-slide placeholder structure rather than robustly parsing model output
- generated images require a Flux API key
- image slide helpers use simple temp-file handling and basic layouts
- if you need predictable output, prefer `--no-images` and concise source material

## `analyze-doc`

Analyzes a document and prints a summary plus extracted key points.

```bash
clippy-swe analyze-doc design.pdf
clippy-swe analyze-doc roadmap.docx --output roadmap-analysis.txt
```

File handling currently includes:

- PDF
- Word `.docx` and `.doc`
- Excel `.xlsx` and `.xls`
- PowerPoint `.pptx` and `.ppt`
- plain text-like files including `.txt`, `.md`, `.py`, `.js`, `.java`

Notes:

- extraction is basic text extraction per file type
- unsupported file types are reported as `"Unsupported file type: <suffix>"` and then still passed through the analysis path
- the model only sees the first 5000 characters of extracted content in the analysis prompt

## `create-spec`

Generates a Markdown feature specification.

```bash
clippy-swe create-spec "Add SSO to the admin portal" --output sso-spec.md
clippy-swe create-spec "Add CSV import flow" --no-diagrams --output import-spec.md
```

What it does:

- asks the agent for a structured feature spec
- optionally requests diagrams through the Flux image path
- writes a Markdown file

Caveats:

- section count is reported as a fixed `12`
- generated diagrams depend on the same Flux API path used by `generate-image`
- diagram generation is additive and best-effort, not guaranteed

## `analyze-recording`

Analyzes an audio or video recording, optionally using an existing transcript file.

```bash
clippy-swe analyze-recording meeting.mp4 --transcript meeting.txt
clippy-swe analyze-recording call.mp3 --output call-analysis.md
```

Important caveat:

- if `--transcript` is not supplied, transcription is placeholder-level
- `_generate_transcript(...)` currently returns a fixed string saying a transcript would be generated
- duration is returned as `"N/A"`
- speaker identification is returned as an empty list

This means recording analysis is only realistically useful today when you already have a transcript and provide it with `--transcript`.

## `generate-image`

Calls the Flux API and writes an image file.

```bash
clippy-swe generate-image "Simple architecture diagram" --flux-key YOUR_KEY --output architecture.png
clippy-swe generate-image "UI wireframe" --flux-key YOUR_KEY --width 1280 --height 720
```

Notes:

- requires a Flux API key
- if no key is provided, the command returns `"Flux API key not configured"`
- success depends on network access and remote API behavior

## Python API quickstart

## Basic task execution

```python
from autogen.cli import ClippySWEAgent, ClippySWEConfig

config = ClippySWEConfig(
    llm_config_path=r"C:\Users\you\.copilot\clippy-kernel\OAI_CONFIG_LIST",
    observer_mode=False,
    max_iterations=20,
)

agent = ClippySWEAgent(config=config)

result = agent.execute_task(
    task_description="Summarize the repository layout",
    task_type="research",
)

print(result["status"])
print(result.get("result", ""))
```

## Using provider settings through the config

```python
from autogen.cli import ClippySWEAgent, ClippySWEConfig

config = ClippySWEConfig(
    use_copilot_sdk=True,
    copilot_provider="openai",
    copilot_model="gpt-4",
    openai_api_key="your-key",
)

agent = ClippySWEAgent(config=config)
result = agent.execute_task("Draft test cases for the CLI", task_type="test")
print(result["status"])
```

## Document processing API

```python
from pathlib import Path

from autogen.cli import ClippySWEAgent, ClippySWEConfig
from autogen.cli.document_processor import DocumentProcessor, PowerPointSpec

agent = ClippySWEAgent(ClippySWEConfig())
processor = DocumentProcessor(agent, flux_api_key="your-flux-key")

analysis = processor.analyze_document(Path("report.pdf"))
print(analysis.summary)

ppt_result = processor.generate_powerpoint(
    content_sources=[Path("notes.md"), "Short summary text"],
    output_path=Path("report.pptx"),
    spec=PowerPointSpec(title="Report"),
    generate_images=False,
)
print(ppt_result)
```

## Known limitations

This section summarizes the most important caveats from the current implementation.

## Task execution

- `--background` does not provide true async background execution.
- observer mode is console printing, not a separate monitoring UI.
- successful execution depends on a valid LLM configuration or provider setup.

## Interactive mode

- `/model` is not a real runtime model switch.
- `!command` is local shell execution with `shell=True` and a 30-second timeout.
- attached file contents are truncated before being passed to the task context.

## GitHub issue workflow

- `resolve-issue` is partial and experimental.
- `_apply_changes(...)` is a stub.
- fetched issue data may fall back to a mock issue if `gh` is unavailable.
- patch or PR creation is not a reliable end-to-end autonomous flow yet.

## Windows path

- `windows` is not a full native automation layer in the current implementation.
- it primarily adds Windows-related context and then calls the standard task executor.

## Document and media helpers

- PowerPoint outline generation is simplified and can fall back to placeholder slides.
- diagram and image generation depend on an external Flux API.
- recording transcription without a supplied transcript is placeholder-level.
- document extraction is basic text extraction, not a full-fidelity parser.

## Model management

- `models --list` is a hard-coded catalog, not a live provider query.
- `models --set` edits only the local `.clippy_swe_config.json`.

## Troubleshooting

## `clippy-swe` says extra dependencies are required

Install the CLI extra:

```bash
pip install -e ".[mcp-proxy-gen]"
```

## LLM config not found

Symptoms:

```text
LLM config file not found: ...
Agent will operate in limited mode
Cannot execute task without LLM configuration
```

Actions:

1. create the resolved `OAI_CONFIG_LIST`
2. or point `llm_config_path` at a valid file in `.clippy_swe_config.json`
3. or use `use_copilot_sdk` with matching provider credentials

## Interactive shell command times out

`!command` uses a 30-second timeout. For longer operations:

- run the command outside interactive mode
- or use `clippy-swe task ...` and describe the intended action instead of using `!`

## `models --set` worked but execution still fails

`models --set` only updates the workspace-local config file. It does not create provider credentials. Verify:

- API keys or tokens are actually configured
- `use_copilot_sdk` is appropriate for your environment
- the provider SDK extra is installed

## `resolve-issue` does not modify files

That is an expected limitation of the current implementation. The command scaffolds the workflow, but file application is not yet fully implemented.

## `analyze-recording` returns a weak transcript

Provide `--transcript path/to/transcript.txt`. The built-in transcript generator is currently a placeholder.

## `windows` does not directly automate applications

That is expected in the current code path. Use the command as a Windows-specific task wrapper, not as a guaranteed UI automation engine.

## Practical usage guidance

- Prefer `task` for core SWE workflows.
- Use `interactive` for exploratory back-and-forth and quick file attachments.
- Use `models` to set workspace defaults, but do not rely on interactive `/model` as a real switch.
- Use `resolve-issue` only for experimentation or as a starting scaffold.
- Use `analyze-recording` with an existing transcript whenever possible.
- Use `generate-ppt` and `create-spec` with images disabled when you need more predictable output.

## Related files

- `CLIPPY_KERNEL_DEVELOPER_GUIDE.md`
- `CLIPPY_SWE_EVALS.md`
- `README.md`
- `QUICKSTART_SWE.md`
- `README_WINDOWS_CLIPPY_MCP.md`
- `autogen/cli/clippy_swe_cli.py`
- `autogen/cli/clippy_swe_agent.py`
- `autogen/cli/interactive_mode.py`
- `autogen/cli/github_integration.py`
- `autogen/cli/document_processor.py`
