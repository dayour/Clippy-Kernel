from clippybot._compat import alias_module, alias_submodules

alias_module(__name__, "clippyagent.utils")
alias_submodules(
    __name__,
    {
        "config": "clippyagent.utils.config",
        "files": "clippyagent.utils.files",
        "github": "clippyagent.utils.github",
        "jinja_warnings": "clippyagent.utils.jinja_warnings",
        "log": "clippyagent.utils.log",
        "patch_formatter": "clippyagent.utils.patch_formatter",
        "serialization": "clippyagent.utils.serialization",
    },
)
