import json

import autogen.cli.clippy_swe_agent as clippy_swe_agent_module
from autogen.cli.clippy_swe_agent import ClippySWEAgent, ClippySWEConfig, TaskHistory


class TestTaskHistory:
    def test_add_task_records_semantic_metadata(self, tmp_path):
        history = TaskHistory(tmp_path / "task-history.json")

        history.add_task(
            task_type="coding",
            description="Normalize branding",
            status="failed",
            metadata={"agents_used": ["software_engineer", "task_coordinator"]},
            error="boom",
        )

        task = history.get_recent_tasks(1)[0]

        assert task["error"] == "boom"
        assert task["schema"]["name"] == "clippy-kernel.swe-agent.task-history.entry"
        assert "task-history" in task["semantic_tags"]
        assert task["routing_hints"]["primary_owner"] == "task-coordinator"


class TestClippySWEAgent:
    def test_execute_task_without_llm_config_records_failure(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ClippySWEAgent, "_initialize", lambda self: None)

        agent = ClippySWEAgent(
            ClippySWEConfig(
                task_history_path=tmp_path / "task-history.json",
                workspace_path=tmp_path,
            )
        )

        result = agent.execute_task("Investigate failing task", task_type="debug")
        task = agent.list_recent_tasks(1)[0]

        assert result["status"] == "failed"
        assert result["schema"]["name"] == "clippy-kernel.swe-agent.task-result"
        assert "status-failed" in result["semantic_tags"]
        assert task["error"].startswith("Cannot execute task without LLM configuration")

    def test_register_toolkit_with_agents_registers_llm_and_execution(self, tmp_path, monkeypatch):
        class DummyToolkit:
            def __init__(self):
                self.llm_agents = []
                self.execution_agents = []

            def register_for_llm(self, agent):
                self.llm_agents.append(agent)

            def register_for_execution(self, agent):
                self.execution_agents.append(agent)

        monkeypatch.setattr(ClippySWEAgent, "_initialize", lambda self: None)

        agent = ClippySWEAgent(
            ClippySWEConfig(
                task_history_path=tmp_path / "task-history.json",
                workspace_path=tmp_path,
            )
        )

        dummy_toolkit = DummyToolkit()
        first_agent = object()
        second_agent = object()
        agent.toolkit = dummy_toolkit
        agent.agents = {"engineer": first_agent, "researcher": second_agent}

        agent._register_toolkit_with_agents()

        assert dummy_toolkit.llm_agents == [first_agent, second_agent]
        assert dummy_toolkit.execution_agents == [first_agent, second_agent]


class TestClippySWEConfig:
    def test_workiq_defaults_are_explicit_and_disabled(self):
        config = ClippySWEConfig()

        assert config.enable_workiq is False
        assert config.workiq_command == "npx"
        assert config.workiq_package == "@microsoft/workiq@latest"
        assert config.workiq_tenant_id is None
        assert config.workiq_timeout == 120

    def test_m365_copilot_defaults_are_explicit_and_disabled(self):
        config = ClippySWEConfig()

        assert config.enable_m365_copilot is False
        assert config.m365_copilot_repo_path is None
        assert config.m365_copilot_tenant_id is None
        assert config.m365_copilot_client_id is None
        assert config.m365_copilot_credential_mode == "default"
        assert config.m365_copilot_default_user_id is None
        assert config.m365_copilot_scopes == ["https://graph.microsoft.com/.default"]

    def test_shared_copilot_defaults_apply_when_workspace_files_are_absent(self, tmp_path, monkeypatch):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        shared_root = tmp_path / ".copilot"
        shared_state_dir = shared_root / "clippy-kernel"

        monkeypatch.setattr(clippy_swe_agent_module, "_current_working_dir", lambda: workspace)
        monkeypatch.setattr(clippy_swe_agent_module, "_copilot_config_dir", lambda: shared_root)
        monkeypatch.setattr(clippy_swe_agent_module, "_clippy_state_dir", lambda: shared_state_dir)

        config = ClippySWEConfig(config_dir=shared_root)

        assert config.config_dir == shared_root
        assert config.custom_agents_dir == shared_root / "agents"
        assert config.skill_directories == [shared_root / "skills"]
        assert config.mcp_config_path == shared_root / "mcp-config.json"
        assert config.task_history_path == shared_state_dir / "task-history.json"
        assert config.interactive_session_path == shared_state_dir / "interactive-session.json"
        assert config.llm_config_path == str(shared_state_dir / "OAI_CONFIG_LIST")

    def test_workspace_legacy_files_stay_preferred(self, tmp_path, monkeypatch):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        legacy_llm_config = workspace / "OAI_CONFIG_LIST"
        legacy_history = workspace / ".clippy_swe_history.json"
        legacy_session = workspace / ".clippy_session.json"

        legacy_llm_config.write_text("[]", encoding="utf-8")
        legacy_history.write_text("{}", encoding="utf-8")
        legacy_session.write_text("{}", encoding="utf-8")

        shared_root = tmp_path / ".copilot"
        shared_state_dir = shared_root / "clippy-kernel"

        monkeypatch.setattr(clippy_swe_agent_module, "_current_working_dir", lambda: workspace)
        monkeypatch.setattr(clippy_swe_agent_module, "_copilot_config_dir", lambda: shared_root)
        monkeypatch.setattr(clippy_swe_agent_module, "_clippy_state_dir", lambda: shared_state_dir)

        config = ClippySWEConfig()

        assert config.llm_config_path == str(legacy_llm_config)
        assert config.task_history_path == legacy_history
        assert config.interactive_session_path == legacy_session

    def test_build_copilot_session_config_loads_shared_mcp_servers(self, tmp_path):
        shared_root = tmp_path / ".copilot"
        skill_dir = shared_root / "skills"
        workspace = tmp_path / "workspace"
        mcp_config_path = shared_root / "mcp-config.json"

        workspace.mkdir()
        skill_dir.mkdir(parents=True)
        mcp_config_path.parent.mkdir(parents=True, exist_ok=True)
        mcp_config_path.write_text(
            json.dumps({"mcpServers": {"filesystem": {"command": "node", "args": ["server.js"]}}}),
            encoding="utf-8",
        )

        config = ClippySWEConfig(
            workspace_path=workspace,
            config_dir=shared_root,
            custom_agents_dir=shared_root / "agents",
            skill_directories=[skill_dir],
            disabled_skills=["legacy-skill"],
            mcp_config_path=mcp_config_path,
        )

        session_config = config.build_copilot_session_config()

        assert session_config["working_directory"] == str(workspace)
        assert session_config["config_dir"] == str(shared_root)
        assert session_config["skill_directories"] == [str(skill_dir)]
        assert session_config["disabled_skills"] == ["legacy-skill"]
        assert session_config["mcp_servers"] == {"filesystem": {"command": "node", "args": ["server.js"]}}
