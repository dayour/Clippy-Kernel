# clippybot

clippybot is a hybrid agent toolkit.

Today, the most mature part of the repository is the local autonomous runtime in `clippyagent`: tool-using agents, environment control, and software-engineering oriented execution loops. Alongside that, `clippybot` now includes newer Microsoft-platform acceleration work for Copilot, Copilot Studio, Power Platform, Teams, Dynamics, and Microsoft 365 scenarios.

The intended direction is not "just an autonomous SWE runtime" and not yet "a fully proven hosted Copilot Studio runtime." It is a practical bridge between:

- a mature local runtime layer for agent execution and experimentation
- a newer platform layer for planning, design, research, analysis, and solution scaffolding across Microsoft business applications

## What this repo is for

clippybot is being shaped to augment teams working in:

- Power Platform
- Dynamics 365
- Copilot Studio
- Microsoft Teams
- Microsoft 365

The onboarding experience is increasingly centered on planner, designer, researcher, and analyst workflows, especially where teams need help turning requirements into agent specs, flows, integrations, governance checks, and rollout artifacts.

## Current architecture at a glance

- `clippyagent/`
  - Mature local runtime and tool execution layer
  - Best fit today for autonomous local workflows and SWE-style agent operations
- `clippybot/`
  - Copilot wrappers and agent abstractions
  - Copilot Studio builder flows and supporting swarms
  - Power Platform, Dataverse, Teams, and publishing adapters
  - Early platform-acceleration layer for Microsoft ecosystem scenarios

## Technical honesty

What the codebase supports today:

- local agent execution and orchestration
- Copilot-oriented wrappers and client integrations
- Copilot Studio builder scaffolding and supporting platform adapters
- Teams, Dataverse, and Power Platform helper modules

What the codebase does not claim yet:

- a complete, production-proven hosted Copilot Studio runtime
- fully validated end-to-end deployment coverage for every Microsoft channel
- finished product parity across planner, designer, researcher, and analyst experiences

## Recommended reading

- `Architecture.md` for the current hybrid architecture and boundaries
- `clippybot/agents/cs_builder/README.md` for the Copilot Studio builder flow

In short: this repository already contains a solid local runtime foundation, and it is actively expanding into a broader Microsoft platform augmentation toolkit.
