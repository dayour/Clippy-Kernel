# Clippy SWE Evals Guide

## Purpose and scope

This document describes how to validate the Clippy SWE surface that exists in this repository today.

It is intentionally narrower and more factual than the older parity-style validation story:

- It separates Clippy SWE checks from broader repository health checks.
- It distinguishes automated evidence from manual behavior checks.
- It calls out surfaces that are incomplete, experimental, or only lightly exercised.
- It does not claim the project has a dedicated SWE benchmark or eval harness, because it does not.

Use this guide when you need an engineering answer to "what evidence do we actually have that Clippy SWE works?" and "what still needs manual proof?"

## Validation layers

| Layer | What it covers | Main evidence in repo | What it does not prove |
| --- | --- | --- | --- |
| SWE-specific automated checks | Clippy SWE config defaults, task-history schema metadata, and a deterministic failure path when no LLM config is present | `validate_clippy_swe.py`, `test/cli/test_clippy_swe_agent.py` | Real end-to-end task execution, interactive UX, Windows automation, or GitHub issue resolution |
| Broader AG2/repository confidence checks | Generic Python test suites, marker-based no-LLM runs, lint/format health | `scripts/test-core-skip-llm.sh`, `scripts/test-skip-llm.sh`, `scripts/test.sh`, `scripts/lint.sh` | That Clippy SWE behavior is correct in live use |
| Manual behavior checks | CLI entrypoints and human-visible flows such as `init`, `status`, `interactive`, Windows tasks, and task execution with or without model config | Manual commands listed below | Repeatable regression coverage unless someone records and reviews results |
| Experimental or partial surfaces | Workflows that exist in code but are not yet backed by strong automated proof | `autogen/cli/clippy_swe_cli.py`, `autogen/cli/github_integration.py` | Production readiness |

## Environment setup

Run all commands from the repository root:

```powershell
Set-Location E:\clippy-kernel
```

Recommended local setup for Clippy SWE validation:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test,mcp-proxy-gen]"
```

Why these extras matter:

- `.[test]` is required for pytest-based validation in this repo.
- `.[mcp-proxy-gen]` supplies CLI dependencies such as `typer`.
- Installing plain `pytest` is not enough, because `pyproject.toml` sets global pytest `addopts` with `--cov=autogen --cov-append --cov-branch --cov-report=xml -m "not conda"`. That means `pytest-cov` must be installed or pytest startup will fail before it reaches the tests.

Optional extras depending on what you are validating:

```powershell
python -m pip install -e ".[openai,mcp-proxy-gen,copilot-sdk,windows-clippy-mcp]"
```

Use runtime extras only when you are intentionally validating live-model or Windows automation behavior. They are not required for the deterministic smoke checks below.

## Fast local smoke workflow

This is the fastest practical sequence for checking the current Clippy SWE implementation without claiming more confidence than the repo actually earns.

### 1. Structural validation

```powershell
python .\validate_clippy_swe.py
```

What it checks:

- Python syntax for Clippy SWE files and example code
- Presence of required classes and functions in key files
- Presence of `clippy-swe = "autogen.cli:main"` in `pyproject.toml`
- Presence of required sections in `CLIPPY_SWE_AGENT_GUIDE.md`

Important caveats:

- This script is structural, not behavioral. It does not verify that commands actually work.
- It checks documentation structure and selected wording invariants for the top-level Clippy SWE docs, but it still does not exercise live CLI behavior.

### 2. Targeted Clippy SWE pytest coverage

```powershell
python -m pytest .\test\cli\test_clippy_swe_agent.py -q
```

What this currently proves:

- `TaskHistory.add_task` records schema and semantic metadata
- `ClippySWEAgent.execute_task` records a deterministic failure when no LLM config is available
- `ClippySWEConfig` correctly chooses shared Copilot defaults and still prefers legacy workspace-local files when present
- `build_copilot_session_config()` includes MCP server definitions from shared config

What it does not prove:

- Successful live task execution against a real model
- Interactive mode behavior
- Windows automation behavior
- `resolve-issue` end-to-end GitHub workflows

### 3. Lint and formatting sanity check

The repo lint wrapper is Bash-based:

```bash
bash scripts/lint.sh
```

This currently runs:

- `ruff check`
- `ruff format`

Use Git Bash or WSL on Windows if `bash` is not on your PATH.

### 4. Optional repository smoke suite without LLM-backed tests

If you want broader confidence that local changes did not destabilize the surrounding AG2 codebase, run one of the repository-level test wrappers:

```bash
bash scripts/test-core-skip-llm.sh
bash scripts/test-skip-llm.sh
```

Notes:

- `scripts/test-core-skip-llm.sh` delegates to `scripts/test-skip-llm.sh --ignore=test/agentchat/contrib`.
- `scripts/test-skip-llm.sh` builds a pytest marker filter that excludes LLM-backed and many optional-dependency surfaces before delegating to `scripts/test.sh`.
- `scripts/test.sh` is the thin wrapper over pytest:

```bash
bash scripts/test.sh -m "not openai"
```

These commands are useful for repository confidence, but they are not Clippy SWE evals by themselves.

## Manual behavioral checks

Automated Clippy SWE coverage in this repo is narrow. For user-facing behavior, manual checks still matter.

### Manual check set A: CLI wiring and local file outputs

Validate the CLI entrypoint and local config behavior:

```powershell
clippy-swe --help
clippy-swe init --workspace .\tmp-clippy-swe
clippy-swe status
```

Expected outcomes:

- `clippy-swe --help` loads the Typer app without import errors
- `init` writes `.clippy_swe_config.json` in the requested workspace
- `status` prints system and agent status instead of crashing
- `status` does not prove that the workspace config written by `init` is active, because this command currently builds its own default config and does not accept `--config`

Relevant code:

- `autogen/cli/__init__.py`
- `autogen/cli/clippy_swe_cli.py`

### Manual check set B: deterministic failure path without model config

The current automated test suite explicitly covers the failure path when no LLM config is available. It is still useful to verify the CLI presents that condition coherently:

```powershell
clippy-swe task "Investigate failing task" --type debug
clippy-swe history --limit 1 --verbose
```

Expected outcome:

- The task should fail cleanly rather than pretending success.
- A recent history entry should exist and show the failed result.

This aligns with `test/cli/test_clippy_swe_agent.py`, which asserts the failure message `Cannot execute task without LLM configuration`.

### Manual check set C: live task execution with a configured model

Only run this when you have intentionally provisioned a supported model config:

```powershell
clippy-swe task "Summarize the workspace layout" --type research --verbose
```

Record:

- provider and model used
- config source used for `OAI_CONFIG_LIST`
- whether the result was actually useful
- whether task history was written

This is a manual behavior check, not a benchmark.

### Manual check set D: interactive mode

```powershell
clippy-swe interactive
```

Manual checks inside the session:

- plain prompt handling
- `@file` attachment flow
- `!command` shell command flow
- slash command behavior such as `/help` or `/clear`
- session persistence on restart if you pass `--session`

There is currently no dedicated automated test file for this mode under `test/`.

### Manual check set E: Windows automation

```powershell
clippy-swe windows "Open Notepad and report the result"
```

Treat this as manual-only validation unless and until a deterministic Windows test harness exists. Record:

- Windows version
- automation dependencies installed
- whether the agent actually interacted with the target application
- whether observer mode output matched what happened

### Manual check set F: WorkIQ integration

Only run this when Node.js, WorkIQ access, EULA acceptance, and tenant consent are already in place.

Before running the task, make sure the config file you intend to use actually enables WorkIQ. For example:

```json
{
  "enable_workiq": true
}
```

Then run a command that explicitly consumes that file:

```powershell
clippy-swe task "Use WorkIQ to summarize my upcoming meetings this week." --type research --config .\.clippy_swe_config.json --verbose
```

Record:

- whether `enable_workiq` was enabled in `.clippy_swe_config.json`
- whether the same command invocation used `--config .\.clippy_swe_config.json`
- whether the agent used `ask_work_iq` and returned a grounded workplace answer
- any prerequisite failures such as missing `npx`, missing EULA acceptance, or missing tenant consent

Do not rely on `clippy-swe status` as proof here. `status` does not load a workspace-local `.clippy_swe_config.json`, so it cannot confirm that a file edited by `init` is active for the WorkIQ test.

### Manual check set G: Agents-M365Copilot SDK integration

Only run this when Azure authentication, Microsoft 365 Copilot licensing, and SDK availability are already in place.

Before running the task, make sure the config file you intend to use actually enables Microsoft 365 Copilot support. For example:

```json
{
  "enable_m365_copilot": true
}
```

Then run a command that explicitly consumes that file:

```powershell
clippy-swe task "Use the Microsoft 365 Copilot SDK tools to list recent Copilot interactions." --type research --config .\.clippy_swe_config.json --verbose
```

Record:

- whether `enable_m365_copilot` was enabled in `.clippy_swe_config.json`
- whether the same command invocation used `--config .\.clippy_swe_config.json`
- whether the runtime loaded the SDK from installed packages or `m365_copilot_repo_path`
- whether the agent used the expected toolkit tools such as `m365_copilot_list_interactions` or `m365_copilot_retrieve`
- whether authentication succeeded through the configured credential mode
- whether retrieval returned the upstream SDK preview/deprecation warning as expected
- any tenant, licensing, or permission failures

As with WorkIQ, do not use `clippy-swe status` as the main evidence that the workspace config was applied. That command does not currently read `.clippy_swe_config.json` automatically.

## Broader repo confidence checks

These checks matter when a Clippy SWE change might have affected the larger AG2 codebase, packaging, or shared tooling.

### Test wrappers

```bash
bash scripts/test-core-skip-llm.sh
bash scripts/test-skip-llm.sh
bash scripts/test.sh
```

Suggested use:

- use `test-core-skip-llm.sh` for a faster, narrower non-LLM regression pass
- use `test-skip-llm.sh` for broader non-LLM regression coverage
- use `test.sh` only when you deliberately want full pytest control and understand the marker/dependency impact

### Lint and formatting

```bash
bash scripts/lint.sh
```

This is useful for catching repository-wide style or syntax drift that Clippy SWE-specific tests will not catch.

### CI reference

This repository currently includes `azure-pipelines.yml`, but it is not a Clippy SWE eval pipeline. The visible pipeline content is a PoliCheck pass and post-analysis gate, which is useful for compliance and text scanning, not for proving SWE behavior.

No `.github/workflows` directory is present in this checkout, so there is no dedicated GitHub Actions-based Clippy SWE eval workflow to point to here.

## Experimental or partial surfaces

Do not over-claim confidence on these areas.

### `resolve-issue` is not a fully proven SWE-agent equivalent

The CLI exposes:

```powershell
clippy-swe resolve-issue owner/repo 123 --create-pr
```

But the implementation in `autogen/cli/github_integration.py` is currently partial:

- `_fetch_issue()` falls back to a mock issue if `gh` CLI is unavailable.
- `_apply_changes()` is a placeholder and logs that changes would be applied based on LLM output.
- `_run_tests()` cycles through a few generic test commands rather than using repo-specific fixture logic.
- PR creation depends on Git, `gh`, authentication, and successful prior steps.

Treat `resolve-issue` as experimental until the repo has fixture-based end-to-end tests and a reproducible benchmark harness.

### Interactive and Windows features are lightly evidenced

The repo contains CLI code for:

- `interactive`
- `windows`
- `status`
- `history`

But the automated Clippy SWE test coverage currently lives only in `test/cli/test_clippy_swe_agent.py`, and that file does not provide end-to-end coverage for those commands.

### Structural validation is not behavior validation

`validate_clippy_swe.py` is useful as a quick guardrail, but passing it does not mean:

- the CLI imports every optional dependency correctly
- live model execution works
- GitHub integration works
- Windows automation works

## Evidence checklist

For a credible Clippy SWE validation result, capture the following:

### Minimum evidence for a code-only change

- `python .\validate_clippy_swe.py`
- `python -m pytest .\test\cli\test_clippy_swe_agent.py -q`
- `bash scripts/lint.sh`

### Recommended evidence for a higher-risk Clippy SWE change

- one of `bash scripts/test-core-skip-llm.sh` or `bash scripts/test-skip-llm.sh`
- manual `clippy-swe --help`, `init`, and `status` checks
- manual failure-path check for `clippy-swe task` without model config

### Required additional evidence for live-runtime changes

- manual live-model task execution with provider and model recorded
- manual interactive-mode transcript or notes
- manual Windows run notes if Windows automation code changed
- explicit note if `resolve-issue` was touched, because there is no dedicated harness for it yet

When reporting results, separate:

- passed automated SWE-specific checks
- passed broader repo checks
- passed manual behavior checks
- untested or partially tested surfaces

## Known gaps and future work

1. There is no dedicated Clippy SWE benchmark or eval harness yet.
   - No fixture-based task corpus
   - No repeatable scoring rubric
   - No golden-output comparison for task quality
   - No end-to-end `resolve-issue` harness against controlled repositories

2. `validate_clippy_swe.py` should be hardened.
   - Open files with explicit UTF-8 encoding
   - Separate syntax validation from documentation checks
   - Avoid treating structural checks as behavioral proof

3. Clippy SWE needs true CLI end-to-end coverage.
   - `task`
   - `status`
   - `history`
   - `init`
   - `interactive`
   - `windows`
   - `resolve-issue`

4. Experimental flows need fixture-based testing.
   - fake GitHub repo and issue fixtures
   - deterministic patch application tests
   - PR creation mocked behind a contract boundary
   - Windows automation abstraction that can be simulated in CI

5. Repository CI should distinguish Clippy SWE evidence from general repo health.
   - add a dedicated SWE eval job
   - publish manual-check guidance alongside automated results
   - avoid parity claims unless a benchmark actually exists
