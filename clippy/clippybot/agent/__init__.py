from clippybot._compat import alias_module, alias_submodules

alias_module(__name__, "clippyagent.agent")
alias_submodules(
    __name__,
    {
        "action_sampler": "clippyagent.agent.action_sampler",
        "agents": "clippyagent.agent.agents",
        "copilot_sdk_config": "clippyagent.agent.copilot_sdk_config",
        "extra": "clippyagent.agent.extra",
        "extra.shell_agent": "clippyagent.agent.extra.shell_agent",
        "history_processors": "clippyagent.agent.history_processors",
        "hooks": "clippyagent.agent.hooks",
        "hooks.abstract": "clippyagent.agent.hooks.abstract",
        "hooks.status": "clippyagent.agent.hooks.status",
        "models": "clippyagent.agent.models",
        "problem_statement": "clippyagent.agent.problem_statement",
        "reviewer": "clippyagent.agent.reviewer",
    },
)
