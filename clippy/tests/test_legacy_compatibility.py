from __future__ import annotations

from importlib import import_module

import pytest


def test_legacy_clippybot_run_main_resolves_and_is_callable() -> None:
    legacy_run_module = import_module("clippybot.run.run")
    modern_run_module = import_module("clippyagent.run.run")

    assert legacy_run_module.main is modern_run_module.main
    assert callable(legacy_run_module.main)


@pytest.mark.parametrize(
    ("legacy_module_name", "attribute_name", "modern_module_name"),
    [
        ("clippybot.environment.clippybot_env", "EnvironmentConfig", "clippyagent.environment.swe_env"),
        ("clippybot.environment.clippybot_env", "clippybotenv", "clippyagent.environment.swe_env"),
        ("clippybot.agent.agents", "DefaultAgentConfig", "clippyagent.agent.agents"),
        ("clippybot.tools.bundle", "Bundle", "clippyagent.tools.bundle"),
        ("clippybot.tools.commands", "Command", "clippyagent.tools.commands"),
        ("clippybot.utils.log", "get_logger", "clippyagent.utils.log"),
        ("clippybot.exceptions", "FormatError", "clippyagent.exceptions"),
        ("clippybot.types", "History", "clippyagent.types"),
    ],
)
def test_legacy_import_surfaces_resolve_to_clippyagent_objects(
    legacy_module_name: str,
    attribute_name: str,
    modern_module_name: str,
) -> None:
    legacy_module = import_module(legacy_module_name)
    modern_module = import_module(modern_module_name)

    assert getattr(legacy_module, attribute_name) is getattr(modern_module, attribute_name)


def test_clippybot_dataverse_api_module_imports() -> None:
    dataverse_api_module = import_module("clippybot.tools.dataverse_api")

    assert dataverse_api_module is not None
    assert hasattr(dataverse_api_module, "DataverseApi")
