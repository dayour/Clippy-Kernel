# clippybot command line interface

All functionality of clippybot is available via the command line interface via the `clippybot` command.

You can run `clippybot --help` to see all subcommands.

## Running clippybot

* `clippybot run`: Run clippybot on a single issue ([tutorial](hello_world.md)).
* `clippybot run-batch`: Run clippybot on a batch of issues ([tutorial](batch_mode.md)).
* `clippybot run-replay`: Replay a trajectory file or a demo file. This means that you take all actions from the trajectory and execute them again in the environment. Useful for debugging your [tools](../config/tools.md) or for building new [demonstrations](../config/demonstrations.md).

## Inspecting runs

* `clippybot inspect` or `clippybot i`: Open the command line inspector ([more information](inspector.md)).
* `clippybot inspector` or `clippybot I`: Open the web-based inspector ([more information](inspector.md)).
* `clippybot quick-stats` or `clippybot qs`: When executed in a directory with trajectories, displays a summary of `exit_status` and more

## Advanced scripts

* `clippybot merge-preds`: Merge multiple prediction files into a single file.
* `clippybot traj-to-demo`: Convert a trajectory file to an easy to edit demo file ([more information on demonstrations](../config/demonstrations.md)).
* `clippybot remove-unfinished`: Remove unfinished trajectories
