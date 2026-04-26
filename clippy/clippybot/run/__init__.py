from clippybot._compat import alias_module, alias_submodules

alias_module(__name__, "clippyagent.run")
alias_submodules(
    __name__,
    {
        "_progress": "clippyagent.run._progress",
        "batch_instances": "clippyagent.run.batch_instances",
        "common": "clippyagent.run.common",
        "compare_runs": "clippyagent.run.compare_runs",
        "extract_pred": "clippyagent.run.extract_pred",
        "hooks": "clippyagent.run.hooks",
        "hooks.abstract": "clippyagent.run.hooks.abstract",
        "hooks.apply_patch": "clippyagent.run.hooks.apply_patch",
        "hooks.open_pr": "clippyagent.run.hooks.open_pr",
        "hooks.swe_bench_evaluate": "clippyagent.run.hooks.swe_bench_evaluate",
        "inspector_cli": "clippyagent.run.inspector_cli",
        "merge_predictions": "clippyagent.run.merge_predictions",
        "quick_stats": "clippyagent.run.quick_stats",
        "remove_unfinished": "clippyagent.run.remove_unfinished",
        "run": "clippyagent.run.run",
        "run_batch": "clippyagent.run.run_batch",
        "run_replay": "clippyagent.run.run_replay",
        "run_shell": "clippyagent.run.run_shell",
        "run_single": "clippyagent.run.run_single",
        "run_traj_to_demo": "clippyagent.run.run_traj_to_demo",
    },
)
