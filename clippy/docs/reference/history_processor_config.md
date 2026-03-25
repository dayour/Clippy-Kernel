# History processor configuration

History processors can filter the history/trajectory to query the model.
For example, a very simple history processor would be one that strips away old observations to reduce context when querying the model.

You can set them as follows:

```yaml
agent:
  history_processors:
    - type: last_n_observations
      n: 5
```

::: clippybot.agent.history_processors.DefaultHistoryProcessor

::: clippybot.agent.history_processors.LastNObservations

::: clippybot.agent.history_processors.TagToolCallObservations

::: clippybot.agent.history_processors.CacheControlHistoryProcessor

::: clippybot.agent.history_processors.RemoveRegex