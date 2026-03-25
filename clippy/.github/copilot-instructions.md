# Copilot Instructions for clippybot

## Project Overview
clippybot is an AG2/AutoGen-based autonomous clippy agent swarm framework. It integrates GitHub Copilot SDK as an LLM client, enabling autonomous software engineering workflows.

## Architecture
- `clippybot/` - Core package: Copilot LLM client, clippy agent, swarm manager
- `clippyagent/` - clippy-agent tools (bash, edit, search) and environment management
- `copilot-sdk-main/` - Copilot SDK integration layer
- `tests/` - Pytest test suite
- `config/` - YAML-based agent configuration
- `docs/` - MkDocs documentation

## Code Style
- Python 3.10+, async-first design, type hints throughout
- Follow AG2 conventions for agent and tool registration
- pre-commit hooks enforced; test with pytest
- See pyproject.toml for dependencies
