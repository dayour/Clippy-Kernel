# Copyright (c) 2023 - 2025, clippy kernel development team
#
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for clippy kernel enhanced MCP Tools.

This module tests the comprehensive MCP toolkit functionality including:
- Development workflow tools
- Web scraping and API integration
- Database operations
- Cloud service integrations
- System monitoring and performance tools
"""

import tempfile
import subprocess
import sys
import warnings
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from autogen.mcp.clippy_kernel_tools import (
    ClippyKernelToolkit,
    CloudConfig,
    DatabaseConfig,
    M365CopilotConfig,
    WebScrapingConfig,
    WorkIQConfig,
    create_clippy_kernel_toolkit,
)


class TestWebScrapingConfig:
    """Test the WebScrapingConfig dataclass."""

    def test_default_config(self):
        """Test default web scraping configuration."""
        config = WebScrapingConfig()

        assert config.headless is True
        assert config.timeout == 30
        assert config.user_agent == "clippy-kernel-bot/1.0"
        assert config.max_retries == 3
        assert config.delay_between_requests == 1.0

    def test_custom_config(self):
        """Test custom web scraping configuration."""
        config = WebScrapingConfig(
            headless=False, timeout=60, user_agent="Custom-Agent/2.0", max_retries=5, delay_between_requests=2.0
        )

        assert config.headless is False
        assert config.timeout == 60
        assert config.user_agent == "Custom-Agent/2.0"
        assert config.max_retries == 5
        assert config.delay_between_requests == 2.0


class TestDatabaseConfig:
    """Test the DatabaseConfig dataclass."""

    def test_database_config(self):
        """Test database configuration."""
        config = DatabaseConfig(connection_string="sqlite:///test.db", pool_size=10, timeout=45, auto_commit=False)

        assert config.connection_string == "sqlite:///test.db"
        assert config.pool_size == 10
        assert config.timeout == 45
        assert config.auto_commit is False


class TestCloudConfig:
    """Test the CloudConfig dataclass."""

    def test_cloud_config(self):
        """Test cloud service configuration."""
        config = CloudConfig(
            provider="aws",
            region="us-west-2",
            credentials_path=Path("/path/to/creds"),
            project_id="test-project",
            subscription_id="test-subscription",
        )

        assert config.provider == "aws"
        assert config.region == "us-west-2"
        assert config.credentials_path == Path("/path/to/creds")
        assert config.project_id == "test-project"
        assert config.subscription_id == "test-subscription"


class TestWorkIQConfig:
    """Test the WorkIQConfig dataclass."""

    def test_default_workiq_config(self):
        config = WorkIQConfig()

        assert config.command == "npx"
        assert config.package_spec == "@microsoft/workiq@latest"
        assert config.tenant_id is None
        assert config.timeout == 120


class TestM365CopilotConfig:
    """Test the M365CopilotConfig dataclass."""

    def test_default_m365copilot_config(self):
        config = M365CopilotConfig()

        assert config.repo_path is None
        assert config.tenant_id is None
        assert config.client_id is None
        assert config.credential_mode == "default"
        assert config.scopes == ["https://graph.microsoft.com/.default"]
        assert config.default_user_id is None


class TestClippyKernelToolkit:
    """Test the ClippyKernelToolkit class."""

    def test_toolkit_initialization_minimal(self):
        """Test toolkit initialization with minimal configuration."""
        toolkit = ClippyKernelToolkit(enable_web_scraping=False, enable_database=False, enable_cloud=False)

        assert isinstance(toolkit, ClippyKernelToolkit)
        assert toolkit.enable_web_scraping is False
        assert toolkit.enable_database is False
        assert toolkit.enable_cloud is False
        assert toolkit.enable_development_tools is True

        # Should have at least development tools
        assert len(toolkit.tools) >= 3

    def test_toolkit_initialization_full(self):
        """Test toolkit initialization with all features enabled."""
        web_config = WebScrapingConfig()
        db_config = DatabaseConfig(connection_string="sqlite:///test.db")
        cloud_config = CloudConfig(provider="azure")

        toolkit = ClippyKernelToolkit(
            web_config=web_config,
            db_config=db_config,
            cloud_config=cloud_config,
            enable_web_scraping=True,
            enable_database=True,
            enable_cloud=True,
        )

        assert toolkit.web_config == web_config
        assert toolkit.db_config == db_config
        assert toolkit.cloud_config == cloud_config
        assert toolkit.enable_web_scraping is True
        assert toolkit.enable_database is True
        assert toolkit.enable_cloud is True

        # Should have all categories of tools
        assert len(toolkit.tools) >= 8

    def test_development_tools_registration(self):
        """Test that development tools are properly registered."""
        toolkit = ClippyKernelToolkit()

        tool_names = [tool.name for tool in toolkit.tools]

        # Check for key development tools
        assert "analyze_codebase" in tool_names
        assert "run_code_quality_check" in tool_names
        assert "generate_project_documentation" in tool_names
        assert "get_system_metrics" in tool_names

    def test_workiq_tool_registration(self):
        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_workiq=True,
        )

        tool_names = [tool.name for tool in toolkit.tools]

        assert "ask_work_iq" in tool_names

    def test_m365_copilot_tool_registration(self):
        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_m365_copilot=True,
        )

        tool_names = [tool.name for tool in toolkit.tools]

        assert "m365_copilot_retrieve" in tool_names
        assert "m365_copilot_list_users" in tool_names
        assert "m365_copilot_get_user" in tool_names
        assert "m365_copilot_list_interactions" in tool_names
        assert "m365_copilot_list_user_online_meetings" in tool_names
        assert "m365_copilot_get_admin_settings" in tool_names
        assert "m365_copilot_get_usage_report" in tool_names


class TestDevelopmentTools:
    """Test development workflow tools functionality."""

    @pytest.fixture
    def toolkit(self):
        """Create a toolkit with development tools only."""
        return ClippyKernelToolkit(enable_web_scraping=False, enable_database=False, enable_cloud=False)

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with sample files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create sample Python files
            (project_path / "main.py").write_text("""
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""")

            (project_path / "utils.py").write_text("""
class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
""")

            # Create a subdirectory
            (project_path / "tests").mkdir()
            (project_path / "tests" / "test_main.py").write_text("""
import unittest
from main import hello_world

class TestMain(unittest.TestCase):
    def test_hello_world(self):
        # This would test hello_world function
        pass
""")

            yield project_path

    def test_analyze_codebase(self, toolkit, temp_project):
        """Test codebase analysis functionality."""
        analyze_tool = None
        for tool in toolkit.tools:
            if tool.name == "analyze_codebase":
                analyze_tool = tool
                break

        assert analyze_tool is not None

        # Test the analysis
        result = analyze_tool.func(
            project_path=str(temp_project), include_tests=True, include_docs=True, file_extensions=[".py"]
        )

        assert isinstance(result, dict)
        assert "project_path" in result
        assert "analysis_timestamp" in result
        assert "file_counts" in result
        assert "line_counts" in result
        assert "totals" in result
        assert result["schema"]["name"] == "clippy-kernel.toolkit.codebase-analysis"
        assert "semantic_tags" in result
        assert result["routing_hints"]["workflow"] == "codebase-analysis"

        # Check file counts
        assert result["file_counts"][".py"] == 3
        assert result["totals"]["total_files"] == 3
        assert result["totals"]["total_lines"] > 0

    def test_analyze_codebase_nonexistent_path(self, toolkit):
        """Test codebase analysis with nonexistent path."""
        analyze_tool = None
        for tool in toolkit.tools:
            if tool.name == "analyze_codebase":
                analyze_tool = tool
                break

        result = analyze_tool.func(project_path="/nonexistent/path")

        assert isinstance(result, dict)
        assert "error" in result
        assert "does not exist" in result["error"]
        assert result["schema"]["name"] == "clippy-kernel.toolkit.codebase-analysis"

    @patch("subprocess.run")
    def test_run_code_quality_check(self, mock_subprocess, toolkit, temp_project):
        """Test code quality check functionality."""
        # Mock successful subprocess calls
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "All checks passed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        quality_tool = None
        for tool in toolkit.tools:
            if tool.name == "run_code_quality_check":
                quality_tool = tool
                break

        assert quality_tool is not None

        result = quality_tool.func(project_path=str(temp_project), tools=["ruff", "black"], fix_issues=False)

        assert isinstance(result, dict)
        assert "project_path" in result
        assert "tool_results" in result
        assert "summary" in result
        assert result["schema"]["name"] == "clippy-kernel.toolkit.code-quality-check"
        assert "quality-gate" in result["semantic_tags"]

        # Check that both tools were attempted
        assert "ruff" in result["tool_results"]
        assert "black" in result["tool_results"]

        # Should be successful
        assert result["summary"]["overall_success"] is True

    def test_generate_project_documentation(self, toolkit, temp_project):
        """Test project documentation generation."""
        doc_tool = None
        for tool in toolkit.tools:
            if tool.name == "generate_project_documentation":
                doc_tool = tool
                break

        assert doc_tool is not None

        result = doc_tool.func(
            project_path=str(temp_project), output_format="markdown", include_api_docs=True, include_examples=True
        )

        assert isinstance(result, dict)
        assert "project_path" in result
        assert "docs_directory" in result
        assert "generated_files" in result
        assert "summary" in result

        # Check that files were generated
        assert len(result["generated_files"]) >= 3  # README, API, Examples
        assert result["summary"]["documentation_complete"] is True

        # Verify files actually exist
        docs_dir = Path(result["docs_directory"])
        assert docs_dir.exists()
        assert (docs_dir / "README.markdown").exists()


class TestWorkIQTools:
    """Test WorkIQ tool integration."""

    @patch("subprocess.run")
    def test_ask_work_iq_uses_npx_by_default(self, mock_subprocess):
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "You have three meetings tomorrow."
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_workiq=True,
            workiq_config=WorkIQConfig(tenant_id="tenant-123"),
        )
        workiq_tool = next(tool for tool in toolkit.tools if tool.name == "ask_work_iq")

        result = workiq_tool.func(question="What meetings do I have tomorrow?")

        mock_subprocess.assert_called_once()
        assert mock_subprocess.call_args.args[0] == [
            "npx",
            "-y",
            "@microsoft/workiq@latest",
            "ask",
            "-t",
            "tenant-123",
            "-q",
            "What meetings do I have tomorrow?",
        ]
        assert result["response"] == "You have three meetings tomorrow."
        assert result["schema"]["name"] == "clippy-kernel.toolkit.workiq-query"

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_ask_work_iq_reports_missing_cli(self, mock_subprocess):
        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_workiq=True,
        )
        workiq_tool = next(tool for tool in toolkit.tools if tool.name == "ask_work_iq")

        result = workiq_tool.func(question="Show my recent documents")

        mock_subprocess.assert_called_once()
        assert "error" in result
        assert "WorkIQ CLI command not found" in result["error"]
        assert result["schema"]["name"] == "clippy-kernel.toolkit.workiq-query"

    @pytest.mark.parametrize("command", ["workiq.cmd", r"C:\Program Files\nodejs\workiq.ps1"])
    @patch("subprocess.run")
    def test_ask_work_iq_treats_windows_shims_as_direct_commands(self, mock_subprocess, command):
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Ready."
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_workiq=True,
            workiq_config=WorkIQConfig(command=command, tenant_id="tenant-123"),
        )
        workiq_tool = next(tool for tool in toolkit.tools if tool.name == "ask_work_iq")

        result = workiq_tool.func(question="Show my focus time")

        assert mock_subprocess.call_args.args[0] == [
            command,
            "ask",
            "-t",
            "tenant-123",
            "-q",
            "Show my focus time",
        ]
        assert result["response"] == "Ready."

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["npx"], timeout=120))
    def test_ask_work_iq_reports_timeout(self, mock_subprocess):
        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_workiq=True,
            workiq_config=WorkIQConfig(timeout=120),
        )
        workiq_tool = next(tool for tool in toolkit.tools if tool.name == "ask_work_iq")

        result = workiq_tool.func(question="Summarize my unread email")

        mock_subprocess.assert_called_once()
        assert "error" in result
        assert "timed out after 120 seconds" in result["error"]
        assert result["schema"]["name"] == "clippy-kernel.toolkit.workiq-query"


class TestM365CopilotTools:
    """Test Microsoft 365 Copilot SDK tool integration."""

    @pytest.mark.parametrize(
        "repo_path_factory",
        [
            lambda repo_root: repo_root,
            lambda repo_root: repo_root / "python" / "packages",
        ],
        ids=["repo-root", "python-packages"],
    )
    def test_import_m365_copilot_module_supports_local_repo_layouts(self, tmp_path, monkeypatch, repo_path_factory):
        repo_root = tmp_path / "Agents-M365Copilot"
        packages_root = repo_root / "python" / "packages"
        for package_name in [
            "microsoft_agents_m365copilot",
            "microsoft_agents_m365copilot_core",
            "m365_loader_probe",
        ]:
            package_dir = packages_root / package_name
            package_dir.mkdir(parents=True, exist_ok=True)
            (package_dir / "__init__.py").write_text(f"PACKAGE_NAME = {package_name!r}\n", encoding="utf-8")

        module_name = "m365_loader_probe"
        monkeypatch.delitem(sys.modules, module_name, raising=False)
        monkeypatch.setattr(sys, "path", [entry for entry in sys.path if str(repo_root) not in entry])

        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_m365_copilot=True,
            m365_copilot_config=M365CopilotConfig(repo_path=repo_path_factory(repo_root)),
        )

        module = toolkit._import_m365_copilot_module(module_name)

        assert module.PACKAGE_NAME == module_name
        assert str(packages_root) in sys.path
        assert str(packages_root / "microsoft_agents_m365copilot") not in sys.path

    def test_m365_copilot_retrieve_reports_warnings_and_hit_count(self, monkeypatch):
        class DummyRetrievalPostRequestBody:
            def __init__(self):
                self.query_string = None
                self.data_source = None
                self.maximum_number_of_results = None
                self.filter_expression = None
                self.resource_metadata = None

        class DummyRetrievalEnum:
            SharePoint = "sharePoint"

        def fake_import(self, module_name):
            if module_name.endswith("retrieval_post_request_body"):
                return type("BodyModule", (), {"RetrievalPostRequestBody": DummyRetrievalPostRequestBody})
            if module_name.endswith("retrieval_data_source"):
                return type("EnumModule", (), {"RetrievalDataSource": DummyRetrievalEnum})
            raise AssertionError(module_name)

        class DummyResponse:
            def __init__(self):
                self.retrieval_hits = [{"id": "hit-1"}, {"id": "hit-2"}]

        class DummyRetrieval:
            def __init__(self):
                self.body = None

            async def post(self, body):
                self.body = body
                warnings.warn("retrieval preview", DeprecationWarning)
                return DummyResponse()

        class DummyCopilot:
            def __init__(self):
                self.retrieval = DummyRetrieval()

        class DummyClient:
            def __init__(self):
                self.copilot = DummyCopilot()

        client = DummyClient()
        monkeypatch.setattr(ClippyKernelToolkit, "_import_m365_copilot_module", fake_import)
        monkeypatch.setattr(ClippyKernelToolkit, "_create_m365_copilot_client", lambda self: client)

        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_m365_copilot=True,
        )
        retrieval_tool = next(tool for tool in toolkit.tools if tool.name == "m365_copilot_retrieve")

        result = retrieval_tool.func(query="What changed this week?", max_results=2)

        assert result["hit_count"] == 2
        assert result["warnings"] == ["retrieval preview"]
        assert client.copilot.retrieval.body.query_string == "What changed this week?"
        assert client.copilot.retrieval.body.maximum_number_of_results == 2
        assert client.copilot.retrieval.body.data_source == "sharePoint"

    def test_m365_copilot_retrieve_reports_body_configuration_failures(self, monkeypatch):
        class DummyRetrievalPostRequestBody:
            def __init__(self):
                self.query_string = None
                self.data_source = None
                self.filter_expression = None
                self.resource_metadata = None
                self._maximum_number_of_results = None

            @property
            def maximum_number_of_results(self):
                return self._maximum_number_of_results

            @maximum_number_of_results.setter
            def maximum_number_of_results(self, value):
                raise RuntimeError(f"invalid max result count: {value}")

        class DummyRetrievalEnum:
            SharePoint = "sharePoint"

        def fake_import(self, module_name):
            if module_name.endswith("retrieval_post_request_body"):
                return type("BodyModule", (), {"RetrievalPostRequestBody": DummyRetrievalPostRequestBody})
            if module_name.endswith("retrieval_data_source"):
                return type("EnumModule", (), {"RetrievalDataSource": DummyRetrievalEnum})
            raise AssertionError(module_name)

        monkeypatch.setattr(ClippyKernelToolkit, "_import_m365_copilot_module", fake_import)

        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_m365_copilot=True,
        )
        retrieval_tool = next(tool for tool in toolkit.tools if tool.name == "m365_copilot_retrieve")

        result = retrieval_tool.func(query="What changed this week?", max_results=2)

        assert result["operation"] == "retrieval"
        assert "invalid max result count" in result["error"]
        assert result["schema"]["name"] == "clippy-kernel.toolkit.m365-copilot-retrieval"

    def test_m365_copilot_list_users_builds_query_configuration(self, monkeypatch):
        class DummyUsersBuilder:
            class UsersRequestBuilderGetQueryParameters:
                def __init__(self, **kwargs):
                    self.__dict__.update(kwargs)

            class UsersRequestBuilderGetRequestConfiguration:
                def __init__(self, query_parameters=None):
                    self.query_parameters = query_parameters

            def __init__(self):
                self.last_configuration = None

            async def get(self, request_configuration=None):
                self.last_configuration = request_configuration
                return type("UserCollection", (), {"value": [{"id": "u1"}, {"id": "u2"}]})()

        class DummyCopilot:
            def __init__(self):
                self.users = DummyUsersBuilder()

        class DummyClient:
            def __init__(self):
                self.copilot = DummyCopilot()

        client = DummyClient()
        monkeypatch.setattr(ClippyKernelToolkit, "_create_m365_copilot_client", lambda self: client)

        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_m365_copilot=True,
        )
        users_tool = next(tool for tool in toolkit.tools if tool.name == "m365_copilot_list_users")

        result = users_tool.func(top=3, search="finance", include_count=True)

        assert result["count"] == 2
        assert client.copilot.users.last_configuration.query_parameters.top == 3
        assert client.copilot.users.last_configuration.query_parameters.search == "finance"
        assert client.copilot.users.last_configuration.query_parameters.count is True

    def test_m365_copilot_get_user_requires_user_id_without_default(self):
        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_m365_copilot=True,
        )
        get_user_tool = next(tool for tool in toolkit.tools if tool.name == "m365_copilot_get_user")

        result = get_user_tool.func()

        assert "error" in result
        assert "user_id" in result["error"]

    def test_m365_copilot_usage_report_decodes_bytes(self, monkeypatch):
        class DummyReportBuilder:
            async def get(self):
                return b"Report Refresh Date,Value\n2026-03-01,42\n"

        class DummyReports:
            def __init__(self):
                self.period = None

            def get_microsoft365_copilot_user_count_summary_with_period(self, period):
                self.period = period
                return DummyReportBuilder()

        class DummyCopilot:
            def __init__(self):
                self.reports = DummyReports()

        class DummyClient:
            def __init__(self):
                self.copilot = DummyCopilot()

        client = DummyClient()
        monkeypatch.setattr(ClippyKernelToolkit, "_create_m365_copilot_client", lambda self: client)

        toolkit = ClippyKernelToolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_m365_copilot=True,
        )
        report_tool = next(tool for tool in toolkit.tools if tool.name == "m365_copilot_get_usage_report")

        result = report_tool.func(report="user_count_summary", period="D30")

        assert result["report"] == "user_count_summary"
        assert result["period"] == "D30"
        assert result["report_data"]["preview_lines"][0] == "Report Refresh Date,Value"
        assert client.copilot.reports.period == "D30"


class TestWebScrapingTools:
    """Test web scraping and API tools functionality."""

    @pytest.fixture
    def web_toolkit(self):
        """Create a toolkit with web scraping enabled."""
        return ClippyKernelToolkit(enable_web_scraping=True, enable_database=False, enable_cloud=False)

    @patch("requests.request")
    def test_api_request_success(self, mock_request, web_toolkit):
        """Test successful API request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"message": "success", "data": [1, 2, 3]}
        mock_request.return_value = mock_response

        api_tool = None
        for tool in web_toolkit.tools:
            if tool.name == "api_request":
                api_tool = tool
                break

        assert api_tool is not None

        result = api_tool.func(
            url="https://api.example.com/data", method="GET", headers={"Authorization": "Bearer token"}
        )

        assert isinstance(result, dict)
        assert result["status_code"] == 200
        assert result["success"] is True
        assert "json_data" in result
        assert result["json_data"]["message"] == "success"

    @patch("requests.request")
    def test_api_request_failure(self, mock_request, web_toolkit):
        """Test failed API request."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = "Not Found"
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_request.return_value = mock_response

        api_tool = None
        for tool in web_toolkit.tools:
            if tool.name == "api_request":
                api_tool = tool
                break

        result = api_tool.func(url="https://api.example.com/nonexistent", method="GET")

        assert isinstance(result, dict)
        assert result["status_code"] == 404
        assert result["success"] is False
        assert "text_data" in result


class TestDatabaseTools:
    """Test database operation tools functionality."""

    @pytest.fixture
    def db_toolkit(self):
        """Create a toolkit with database enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_config = DatabaseConfig(connection_string=f"sqlite:///{db_path}", auto_commit=True)

            yield ClippyKernelToolkit(
                enable_web_scraping=False, enable_database=True, enable_cloud=False, db_config=db_config
            )

    def test_execute_sql_query_create_table(self, db_toolkit):
        """Test SQL query execution for table creation."""
        sql_tool = None
        for tool in db_toolkit.tools:
            if tool.name == "execute_sql_query":
                sql_tool = tool
                break

        assert sql_tool is not None

        # Create a test table
        result = sql_tool.func(query="CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)", fetch_results=False)

        assert isinstance(result, dict)
        assert "query" in result
        assert "timestamp" in result
        assert "rows_affected" in result

    def test_execute_sql_query_insert_select(self, db_toolkit):
        """Test SQL query execution for insert and select operations."""
        sql_tool = None
        for tool in db_toolkit.tools:
            if tool.name == "execute_sql_query":
                sql_tool = tool
                break

        # Create table
        sql_tool.func("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")

        # Insert data
        insert_result = sql_tool.func(
            query="INSERT INTO users (name) VALUES (?)", parameters=["John Doe"], fetch_results=False
        )

        assert insert_result["rows_affected"] == 1

        # Select data
        select_result = sql_tool.func(query="SELECT * FROM users", fetch_results=True)

        assert "columns" in select_result
        assert "rows" in select_result
        assert "row_count" in select_result
        assert select_result["row_count"] == 1
        assert select_result["columns"] == ["id", "name"]

    def test_analyze_database_schema(self, db_toolkit):
        """Test database schema analysis."""
        sql_tool = None
        schema_tool = None

        for tool in db_toolkit.tools:
            if tool.name == "execute_sql_query":
                sql_tool = tool
            elif tool.name == "analyze_database_schema":
                schema_tool = tool

        assert sql_tool is not None
        assert schema_tool is not None

        # Create test tables
        sql_tool.func("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        sql_tool.func("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL)")
        sql_tool.func("INSERT INTO users (name) VALUES ('Test User')")

        # Analyze schema
        result = schema_tool.func()

        assert isinstance(result, dict)
        assert "database_type" in result
        assert "total_tables" in result
        assert "tables" in result

        assert result["database_type"] == "sqlite"
        assert result["total_tables"] >= 2
        assert "users" in result["tables"]
        assert "orders" in result["tables"]

        # Check user table details
        users_table = result["tables"]["users"]
        assert "columns" in users_table
        assert "row_count" in users_table
        assert users_table["row_count"] == 1
        assert len(users_table["columns"]) == 2


class TestSystemMonitoringTools:
    """Test system monitoring and performance tools."""

    @pytest.fixture
    def toolkit(self):
        """Create a basic toolkit."""
        return ClippyKernelToolkit()

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    @patch("psutil.cpu_count")
    def test_get_system_metrics(self, mock_cpu_count, mock_disk_usage, mock_virtual_memory, mock_cpu_percent, toolkit):
        """Test system metrics collection."""
        # Mock psutil functions
        mock_cpu_percent.return_value = 45.2
        mock_cpu_count.return_value = 8
        mock_virtual_memory.return_value = Mock(
            _asdict=lambda: {"total": 16000000000, "available": 8000000000, "percent": 50.0}
        )
        mock_disk_usage.return_value = Mock(
            _asdict=lambda: {"total": 500000000000, "used": 250000000000, "free": 250000000000}
        )

        metrics_tool = None
        for tool in toolkit.tools:
            if tool.name == "get_system_metrics":
                metrics_tool = tool
                break

        assert metrics_tool is not None

        result = metrics_tool.func()

        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "cpu" in result
        assert "memory" in result
        assert "disk" in result

        # Check CPU metrics
        assert result["cpu"]["usage_percent"] == 45.2
        assert result["cpu"]["count"] == 8

        # Check memory metrics
        assert result["memory"]["percent"] == 50.0

        # Check disk metrics
        assert "usage" in result["disk"]


class TestFactoryFunction:
    """Test the factory function for creating toolkits."""

    def test_create_clippy_kernel_toolkit_minimal(self):
        """Test factory function with minimal configuration."""
        toolkit = create_clippy_kernel_toolkit(enable_web_scraping=False, enable_database=False, enable_cloud=False)

        assert isinstance(toolkit, ClippyKernelToolkit)
        assert toolkit.enable_web_scraping is False
        assert toolkit.enable_database is False
        assert toolkit.enable_cloud is False
        assert len(toolkit.tools) >= 3  # At least development tools

    def test_create_clippy_kernel_toolkit_full(self):
        """Test factory function with full configuration."""
        web_config = WebScrapingConfig(headless=False)
        db_config = DatabaseConfig(connection_string="sqlite:///test.db")
        cloud_config = CloudConfig(provider="aws")

        toolkit = create_clippy_kernel_toolkit(
            enable_web_scraping=True,
            enable_database=True,
            enable_cloud=True,
            web_config=web_config,
            db_config=db_config,
            cloud_config=cloud_config,
        )

        assert isinstance(toolkit, ClippyKernelToolkit)
        assert toolkit.enable_web_scraping is True
        assert toolkit.enable_database is True
        assert toolkit.enable_cloud is True
        assert toolkit.web_config == web_config
        assert toolkit.db_config == db_config
        assert toolkit.cloud_config == cloud_config

    def test_create_clippy_kernel_toolkit_with_workiq(self):
        workiq_config = WorkIQConfig(command="workiq", tenant_id="tenant-456", timeout=45)

        toolkit = create_clippy_kernel_toolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_workiq=True,
            workiq_config=workiq_config,
        )

        assert isinstance(toolkit, ClippyKernelToolkit)
        assert toolkit.enable_workiq is True
        assert toolkit.workiq_config == workiq_config
        assert "ask_work_iq" in [tool.name for tool in toolkit.tools]

    def test_create_clippy_kernel_toolkit_with_m365_copilot(self):
        m365_config = M365CopilotConfig(repo_path=Path("E:/Agents-M365Copilot"), default_user_id="user-123")

        toolkit = create_clippy_kernel_toolkit(
            enable_web_scraping=False,
            enable_database=False,
            enable_cloud=False,
            enable_m365_copilot=True,
            m365_copilot_config=m365_config,
        )

        assert isinstance(toolkit, ClippyKernelToolkit)
        assert toolkit.enable_m365_copilot is True
        assert toolkit.m365_copilot_config == m365_config
        assert "m365_copilot_retrieve" in [tool.name for tool in toolkit.tools]


# Skip tests that require actual external services
@pytest.mark.skip(reason="Requires actual external services - run manually for integration testing")
class TestIntegrationScenarios:
    """Integration tests that require external services."""

    def test_real_web_scraping(self):
        """Test web scraping with real websites."""
        # This would require actual browser and network access
        pass

    def test_real_api_requests(self):
        """Test API requests with real endpoints."""
        # This would require actual API endpoints
        pass

    def test_cloud_service_integration(self):
        """Test cloud service integration."""
        # This would require actual cloud service credentials
        pass


if __name__ == "__main__":
    pytest.main([__file__])
