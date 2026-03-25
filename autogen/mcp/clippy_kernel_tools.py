# Copyright (c) 2023 - 2025, clippy kernel development team
#
# SPDX-License-Identifier: Apache-2.0

"""
clippy kernel enhanced MCP Tools

This module provides an extensive collection of MCP (Model Control Protocol) tools
specifically designed for clippy kernel's advanced multi-agent development workflows.
These tools extend beyond basic Windows desktop operations to include:

- Web scraping and API integration
- Database operations and data management
- Cloud service interactions (AWS, Azure, GCP)
- Development workflow automation
- File system and project management
- Real-time collaboration features
- Performance monitoring and analytics
"""

import asyncio
import importlib
import inspect
import logging
import sqlite3
import subprocess
import sys
import threading
import warnings
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..import_utils import optional_import_block
from ..orchestration_metadata import build_semantic_envelope
from ..tools import Tool, Toolkit, tool

logger = logging.getLogger(__name__)

# Optional imports for enhanced functionality
with optional_import_block():
    import boto3
with optional_import_block():
    import psutil
with optional_import_block():
    import requests
with optional_import_block():
    from azure.storage.blob import BlobServiceClient
with optional_import_block():
    from google.cloud import storage as gcs
with optional_import_block():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.by import By


@dataclass
class WebScrapingConfig:
    """Configuration for web scraping operations."""

    headless: bool = True
    timeout: int = 30
    user_agent: str = "clippy-kernel-bot/1.0"
    max_retries: int = 3
    delay_between_requests: float = 1.0


@dataclass
class DatabaseConfig:
    """Configuration for database operations."""

    connection_string: str
    pool_size: int = 5
    timeout: int = 30
    auto_commit: bool = True


@dataclass
class CloudConfig:
    """Configuration for cloud service operations."""

    provider: str  # 'aws', 'azure', 'gcp'
    region: str = "us-east-1"
    credentials_path: Path | None = None
    project_id: str | None = None  # For GCP
    subscription_id: str | None = None  # For Azure


@dataclass
class WorkIQConfig:
    """Configuration for WorkIQ CLI access."""

    command: str = "npx"
    package_spec: str = "@microsoft/workiq@latest"
    tenant_id: str | None = None
    timeout: int = 120


@dataclass
class M365CopilotConfig:
    """Configuration for Microsoft 365 Copilot SDK access."""

    repo_path: Path | None = None
    tenant_id: str | None = None
    client_id: str | None = None
    credential_mode: str = "default"
    scopes: list[str] = field(default_factory=lambda: ["https://graph.microsoft.com/.default"])
    default_user_id: str | None = None


class ClippyKernelToolkit(Toolkit):
    """
    Comprehensive toolkit for clippy kernel multi-agent development workflows.

    This toolkit provides advanced tools that go beyond basic MCP operations,
    enabling sophisticated development workflows, cloud integrations, and
    collaborative features for agent teams.
    """

    def __init__(
        self,
        web_config: WebScrapingConfig | None = None,
        db_config: DatabaseConfig | None = None,
        cloud_config: CloudConfig | None = None,
        workiq_config: WorkIQConfig | None = None,
        enable_web_scraping: bool = True,
        enable_database: bool = True,
        enable_cloud: bool = True,
        enable_workiq: bool = False,
        enable_development_tools: bool = True,
        enable_m365_copilot: bool = False,
        m365_copilot_config: M365CopilotConfig | None = None,
    ):
        """
        Initialize the clippy kernel toolkit.

        Args:
            web_config: Configuration for web scraping operations
            db_config: Configuration for database operations
            cloud_config: Configuration for cloud service operations
            workiq_config: Configuration for WorkIQ CLI access
            m365_copilot_config: Configuration for Microsoft 365 Copilot SDK access
            enable_web_scraping: Enable web scraping tools
            enable_database: Enable database operation tools
            enable_cloud: Enable cloud service tools
            enable_workiq: Enable Microsoft 365 workplace query tool integration
            enable_m365_copilot: Enable Microsoft 365 Copilot SDK tools
            enable_development_tools: Enable development workflow tools
        """
        super().__init__(tools=[])

        self.web_config = web_config or WebScrapingConfig()
        self.db_config = db_config
        self.cloud_config = cloud_config
        self.workiq_config = workiq_config or WorkIQConfig()
        self.m365_copilot_config = m365_copilot_config or M365CopilotConfig()

        # Feature flags
        self.enable_web_scraping = enable_web_scraping
        self.enable_database = enable_database and db_config is not None
        self.enable_cloud = enable_cloud and cloud_config is not None
        self.enable_workiq = enable_workiq
        self.enable_m365_copilot = enable_m365_copilot
        self.enable_development_tools = enable_development_tools

        # Initialize tools
        self._register_tools()

        logger.info(f"ClippyKernelToolkit initialized with {len(self.tools)} tools")

    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the toolkit."""
        self.set_tool(tool)

    def _tool_metadata(
        self,
        *,
        schema_name: str,
        workflow: str,
        tags: list[str],
        capabilities: list[str],
        attributes: dict[str, Any] | None = None,
        kind: str = "tool-result",
    ) -> dict[str, Any]:
        """Build semantic metadata for toolkit results."""
        semantic_attributes = {
            "toolkit": "clippy-kernel",
            "development_tools_enabled": self.enable_development_tools,
            "web_scraping_enabled": self.enable_web_scraping,
            "database_enabled": self.enable_database,
            "cloud_enabled": self.enable_cloud,
            "workiq_enabled": self.enable_workiq,
            "m365_copilot_enabled": self.enable_m365_copilot,
        }
        if attributes:
            semantic_attributes.update(attributes)

        return build_semantic_envelope(
            schema_name=schema_name,
            kind=kind,
            workflow=workflow,
            primary_owner="software-engineer",
            participant_roles=["software-engineer", "qa-engineer", "task-coordinator"],
            focus_areas=["code-quality", "automation", "documentation"],
            capabilities=capabilities,
            tags=["toolkit", *tags],
            attributes=semantic_attributes,
        )

    def _tool_result(
        self,
        payload: dict[str, Any],
        *,
        schema_name: str,
        workflow: str,
        tags: list[str],
        capabilities: list[str],
        attributes: dict[str, Any] | None = None,
        kind: str = "tool-result",
    ) -> dict[str, Any]:
        """Attach semantic metadata to a toolkit payload."""
        return payload | self._tool_metadata(
            schema_name=schema_name,
            workflow=workflow,
            tags=tags,
            capabilities=capabilities,
            attributes=attributes,
            kind=kind,
        )

    def _tool_error(
        self,
        message: str,
        *,
        schema_name: str,
        workflow: str,
        tags: list[str],
        capabilities: list[str],
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a semantic error payload for toolkit operations."""
        return self._tool_result(
            {"error": message},
            schema_name=schema_name,
            workflow=workflow,
            tags=tags,
            capabilities=capabilities,
            attributes=attributes,
            kind="tool-error",
        )

    def _register_tools(self):
        """Register all available tools based on configuration."""

        # Core development tools (always enabled)
        self._register_development_tools()

        # Web scraping tools
        if self.enable_web_scraping:
            self._register_web_scraping_tools()

        # Database tools
        if self.enable_database:
            self._register_database_tools()

        # Cloud service tools
        if self.enable_cloud:
            self._register_cloud_tools()

        if self.enable_workiq:
            self._register_workiq_tools()

        if self.enable_m365_copilot:
            self._register_m365_copilot_tools()

        # System monitoring tools
        self._register_monitoring_tools()

    def _register_development_tools(self):
        """Register development workflow tools."""

        @tool()
        def analyze_codebase(
            project_path: str,
            include_tests: bool = True,
            include_docs: bool = True,
            file_extensions: list[str] | None = None,
        ) -> dict[str, Any]:
            """
            Analyze a codebase and provide comprehensive metrics and insights.

            Args:
                project_path: Path to the project directory
                include_tests: Include test files in analysis
                include_docs: Include documentation files in analysis
                file_extensions: List of file extensions to analyze (e.g., ['.py', '.js'])

            Returns:
                Dictionary containing codebase analysis results
            """
            try:
                project = Path(project_path)
                if not project.exists():
                    return self._tool_error(
                        f"Project path does not exist: {project_path}",
                        schema_name="clippy-kernel.toolkit.codebase-analysis",
                        workflow="codebase-analysis",
                        tags=["analysis", "codebase"],
                        capabilities=["code-analysis", "project-inventory"],
                        attributes={"project_path": project_path},
                    )

                extensions = file_extensions or [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h"]

                analysis = {
                    "project_path": str(project),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "file_counts": {},
                    "line_counts": {},
                    "complexity_metrics": {},
                    "structure_analysis": {},
                }

                total_files = 0
                total_lines = 0

                for ext in extensions:
                    files = list(project.rglob(f"*{ext}"))
                    if not include_tests:
                        files = [f for f in files if "test" not in str(f).lower()]
                    if not include_docs:
                        files = [f for f in files if "doc" not in str(f).lower()]

                    file_count = len(files)
                    line_count = 0

                    for file_path in files:
                        try:
                            with open(file_path, encoding="utf-8") as f:
                                lines = len(f.readlines())
                                line_count += lines
                        except (UnicodeDecodeError, PermissionError):
                            continue

                    analysis["file_counts"][ext] = file_count
                    analysis["line_counts"][ext] = line_count
                    total_files += file_count
                    total_lines += line_count

                analysis["totals"] = {
                    "total_files": total_files,
                    "total_lines": total_lines,
                    "average_lines_per_file": total_lines / max(total_files, 1),
                }

                # Analyze directory structure
                directories = [d for d in project.rglob("*") if d.is_dir()]
                analysis["structure_analysis"] = {
                    "total_directories": len(directories),
                    "max_depth": max([len(d.parts) - len(project.parts) for d in directories], default=0),
                    "common_patterns": self._identify_project_patterns(project),
                }

                return self._tool_result(
                    analysis,
                    schema_name="clippy-kernel.toolkit.codebase-analysis",
                    workflow="codebase-analysis",
                    tags=["analysis", "codebase"],
                    capabilities=["code-analysis", "project-inventory"],
                    attributes={"project_path": str(project), "file_extensions": extensions},
                )

            except Exception as e:
                logger.error(f"Codebase analysis failed: {str(e)}")
                return self._tool_error(
                    f"Analysis failed: {str(e)}",
                    schema_name="clippy-kernel.toolkit.codebase-analysis",
                    workflow="codebase-analysis",
                    tags=["analysis", "codebase"],
                    capabilities=["code-analysis", "project-inventory"],
                    attributes={"project_path": project_path},
                )

        @tool()
        def run_code_quality_check(
            project_path: str, tools: list[str] = None, fix_issues: bool = False
        ) -> dict[str, Any]:
            """
            Run code quality checks using various linting and analysis tools.

            Args:
                project_path: Path to the project directory
                tools: List of tools to run (e.g., ['ruff', 'mypy', 'black'])
                fix_issues: Attempt to automatically fix issues

            Returns:
                Dictionary containing quality check results
            """
            try:
                project = Path(project_path)
                tools = tools or ["ruff", "black", "mypy"]

                results = {
                    "project_path": str(project),
                    "timestamp": datetime.now().isoformat(),
                    "tool_results": {},
                    "summary": {},
                }

                for tool in tools:
                    try:
                        if tool == "ruff":
                            cmd = ["ruff", "check", str(project)]
                            if fix_issues:
                                cmd.append("--fix")
                        elif tool == "black":
                            cmd = ["black", str(project)]
                            if not fix_issues:
                                cmd.append("--check")
                        elif tool == "mypy":
                            cmd = ["mypy", str(project)]
                        else:
                            continue

                        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project)

                        results["tool_results"][tool] = {
                            "exit_code": result.returncode,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "success": result.returncode == 0,
                        }

                    except FileNotFoundError:
                        results["tool_results"][tool] = {"error": f"Tool '{tool}' not found in PATH"}

                # Generate summary
                successful_tools = [t for t, r in results["tool_results"].items() if r.get("success", False)]
                failed_tools = [t for t, r in results["tool_results"].items() if not r.get("success", False)]

                results["summary"] = {
                    "total_tools": len(tools),
                    "successful_tools": len(successful_tools),
                    "failed_tools": len(failed_tools),
                    "overall_success": len(failed_tools) == 0,
                }

                return self._tool_result(
                    results,
                    schema_name="clippy-kernel.toolkit.code-quality-check",
                    workflow="quality-gate",
                    tags=["quality", "linting", "validation"],
                    capabilities=["linting", "type-checking", "quality-gates"],
                    attributes={"project_path": str(project), "requested_tools": tools, "fix_issues": fix_issues},
                )

            except Exception as e:
                logger.error(f"Code quality check failed: {str(e)}")
                return self._tool_error(
                    f"Quality check failed: {str(e)}",
                    schema_name="clippy-kernel.toolkit.code-quality-check",
                    workflow="quality-gate",
                    tags=["quality", "linting", "validation"],
                    capabilities=["linting", "type-checking", "quality-gates"],
                    attributes={"project_path": project_path, "requested_tools": tools or []},
                )

        @tool()
        def generate_project_documentation(
            project_path: str,
            output_format: str = "markdown",
            include_api_docs: bool = True,
            include_examples: bool = True,
        ) -> dict[str, Any]:
            """
            Generate comprehensive documentation for a project.

            Args:
                project_path: Path to the project directory
                output_format: Format for documentation ('markdown', 'html', 'rst')
                include_api_docs: Include API documentation
                include_examples: Include code examples

            Returns:
                Dictionary containing documentation generation results
            """
            try:
                project = Path(project_path)
                docs_dir = project / "docs_generated"
                docs_dir.mkdir(exist_ok=True)

                results = {
                    "project_path": str(project),
                    "docs_directory": str(docs_dir),
                    "timestamp": datetime.now().isoformat(),
                    "generated_files": [],
                    "summary": {},
                }

                # Generate README if not exists
                readme_path = docs_dir / f"README.{output_format}"
                if not readme_path.exists():
                    readme_content = self._generate_readme_content(project, output_format)
                    with open(readme_path, "w") as f:
                        f.write(readme_content)
                    results["generated_files"].append(str(readme_path))

                # Generate API documentation
                if include_api_docs:
                    api_docs_path = docs_dir / f"API.{output_format}"
                    api_content = self._generate_api_docs(project, output_format)
                    with open(api_docs_path, "w") as f:
                        f.write(api_content)
                    results["generated_files"].append(str(api_docs_path))

                # Generate examples
                if include_examples:
                    examples_path = docs_dir / f"Examples.{output_format}"
                    examples_content = self._generate_examples_docs(project, output_format)
                    with open(examples_path, "w") as f:
                        f.write(examples_content)
                    results["generated_files"].append(str(examples_path))

                results["summary"] = {
                    "total_files_generated": len(results["generated_files"]),
                    "documentation_complete": True,
                }

                return self._tool_result(
                    results,
                    schema_name="clippy-kernel.toolkit.project-documentation",
                    workflow="documentation-generation",
                    tags=["documentation", "generated-artifact"],
                    capabilities=["documentation-generation", "project-analysis"],
                    attributes={
                        "project_path": str(project),
                        "output_format": output_format,
                        "include_api_docs": include_api_docs,
                        "include_examples": include_examples,
                    },
                    kind="artifact-result",
                )

            except Exception as e:
                logger.error(f"Documentation generation failed: {str(e)}")
                return self._tool_error(
                    f"Documentation generation failed: {str(e)}",
                    schema_name="clippy-kernel.toolkit.project-documentation",
                    workflow="documentation-generation",
                    tags=["documentation", "generated-artifact"],
                    capabilities=["documentation-generation", "project-analysis"],
                    attributes={"project_path": project_path, "output_format": output_format},
                )

        # Add tools to toolkit
        self.add_tool(analyze_codebase)
        self.add_tool(run_code_quality_check)
        self.add_tool(generate_project_documentation)

    def _register_web_scraping_tools(self):
        """Register web scraping and API integration tools."""

        @tool()
        def scrape_website(
            url: str,
            selectors: dict[str, str] | None = None,
            wait_for_element: str | None = None,
            screenshot: bool = False,
        ) -> dict[str, Any]:
            """
            Scrape content from a website using Selenium.

            Args:
                url: URL to scrape
                selectors: CSS selectors to extract specific elements
                wait_for_element: CSS selector to wait for before scraping
                screenshot: Take a screenshot of the page

            Returns:
                Dictionary containing scraped content and metadata
            """
            try:
                chrome_options = ChromeOptions()
                if self.web_config.headless:
                    chrome_options.add_argument("--headless")
                chrome_options.add_argument(f"--user-agent={self.web_config.user_agent}")

                driver = webdriver.Chrome(options=chrome_options)
                driver.set_page_load_timeout(self.web_config.timeout)

                driver.get(url)

                if wait_for_element:
                    from selenium.webdriver.support import expected_conditions as EC
                    from selenium.webdriver.support.ui import WebDriverWait

                    WebDriverWait(driver, self.web_config.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                    )

                results = {
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "title": driver.title,
                    "page_source_length": len(driver.page_source),
                    "extracted_content": {},
                }

                if selectors:
                    for name, selector in selectors.items():
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        results["extracted_content"][name] = [elem.text for elem in elements]
                else:
                    results["extracted_content"]["body"] = driver.find_element(By.TAG_NAME, "body").text

                if screenshot:
                    screenshot_path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    driver.save_screenshot(screenshot_path)
                    results["screenshot_path"] = screenshot_path

                driver.quit()
                return results

            except Exception as e:
                logger.error(f"Web scraping failed: {str(e)}")
                return {"error": f"Scraping failed: {str(e)}"}

        @tool()
        def api_request(
            url: str,
            method: str = "GET",
            headers: dict[str, str] | None = None,
            data: dict[str, Any] | None = None,
            timeout: int = 30,
        ) -> dict[str, Any]:
            """
            Make HTTP API requests with comprehensive error handling.

            Args:
                url: API endpoint URL
                method: HTTP method (GET, POST, PUT, DELETE, etc.)
                headers: Request headers
                data: Request data/payload
                timeout: Request timeout in seconds

            Returns:
                Dictionary containing response data and metadata
            """
            try:
                headers = headers or {}
                headers.setdefault("User-Agent", self.web_config.user_agent)

                response = requests.request(
                    method=method, url=url, headers=headers, json=data if data else None, timeout=timeout
                )

                results = {
                    "url": url,
                    "method": method,
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat(),
                    "headers": dict(response.headers),
                    "success": response.status_code < 400,
                }

                try:
                    results["json_data"] = response.json()
                except ValueError:
                    results["text_data"] = response.text

                return results

            except Exception as e:
                logger.error(f"API request failed: {str(e)}")
                return {"error": f"API request failed: {str(e)}"}

        self.add_tool(scrape_website)
        self.add_tool(api_request)

    def _register_database_tools(self):
        """Register database operation tools."""

        @tool()
        def execute_sql_query(
            query: str, parameters: list[Any] | None = None, fetch_results: bool = True
        ) -> dict[str, Any]:
            """
            Execute SQL queries with proper error handling and result formatting.

            Args:
                query: SQL query to execute
                parameters: Query parameters for prepared statements
                fetch_results: Whether to fetch and return results

            Returns:
                Dictionary containing query results and metadata
            """
            try:
                if not self.db_config:
                    return {"error": "Database configuration not provided"}

                # For SQLite (simple example)
                if self.db_config.connection_string.startswith("sqlite"):
                    db_path = self.db_config.connection_string.replace("sqlite:///", "")
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    if parameters:
                        cursor.execute(query, parameters)
                    else:
                        cursor.execute(query)

                    results = {
                        "query": query,
                        "timestamp": datetime.now().isoformat(),
                        "rows_affected": cursor.rowcount,
                    }

                    if fetch_results and query.strip().upper().startswith("SELECT"):
                        rows = cursor.fetchall()
                        columns = [description[0] for description in cursor.description]
                        results["columns"] = columns
                        results["rows"] = rows
                        results["row_count"] = len(rows)

                    if self.db_config.auto_commit:
                        conn.commit()

                    conn.close()
                    return results

                else:
                    return {"error": "Unsupported database type"}

            except Exception as e:
                logger.error(f"SQL query execution failed: {str(e)}")
                return {"error": f"Query execution failed: {str(e)}"}

        @tool()
        def analyze_database_schema(table_names: list[str] | None = None) -> dict[str, Any]:
            """
            Analyze database schema and provide insights.

            Args:
                table_names: Specific tables to analyze (None for all tables)

            Returns:
                Dictionary containing schema analysis results
            """
            try:
                if not self.db_config:
                    return {"error": "Database configuration not provided"}

                # SQLite schema analysis
                if self.db_config.connection_string.startswith("sqlite"):
                    db_path = self.db_config.connection_string.replace("sqlite:///", "")
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    # Get all tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    all_tables = [row[0] for row in cursor.fetchall()]

                    tables_to_analyze = table_names or all_tables

                    schema_info = {
                        "database_type": "sqlite",
                        "total_tables": len(all_tables),
                        "analyzed_tables": len(tables_to_analyze),
                        "tables": {},
                    }

                    for table in tables_to_analyze:
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = cursor.fetchall()

                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        row_count = cursor.fetchone()[0]

                        schema_info["tables"][table] = {
                            "columns": [
                                {"name": col[1], "type": col[2], "nullable": not col[3], "primary_key": bool(col[5])}
                                for col in columns
                            ],
                            "row_count": row_count,
                            "column_count": len(columns),
                        }

                    conn.close()
                    return schema_info

                else:
                    return {"error": "Unsupported database type"}

            except Exception as e:
                logger.error(f"Schema analysis failed: {str(e)}")
                return {"error": f"Schema analysis failed: {str(e)}"}

        self.add_tool(execute_sql_query)
        self.add_tool(analyze_database_schema)

    def _register_cloud_tools(self):
        """Register cloud service integration tools."""

        @tool()
        def upload_file_to_cloud(file_path: str, container_name: str, blob_name: str | None = None) -> dict[str, Any]:
            """
            Upload file to cloud storage (Azure, AWS, or GCP).

            Args:
                file_path: Local file path to upload
                container_name: Container/bucket name
                blob_name: Remote file name (defaults to local filename)

            Returns:
                Dictionary containing upload results and metadata
            """
            try:
                file_path = Path(file_path)
                if not file_path.exists():
                    return {"error": f"File does not exist: {file_path}"}

                blob_name = blob_name or file_path.name

                if self.cloud_config.provider == "azure":
                    # Azure Blob Storage
                    blob_service = BlobServiceClient.from_connection_string(
                        self.cloud_config.credentials_path.read_text()
                    )
                    blob_client = blob_service.get_blob_client(container=container_name, blob=blob_name)

                    with open(file_path, "rb") as data:
                        blob_client.upload_blob(data, overwrite=True)

                    return {
                        "provider": "azure",
                        "container": container_name,
                        "blob_name": blob_name,
                        "file_size": file_path.stat().st_size,
                        "upload_successful": True,
                        "timestamp": datetime.now().isoformat(),
                    }

                elif self.cloud_config.provider == "aws":
                    # AWS S3
                    s3_client = boto3.client("s3")
                    s3_client.upload_file(str(file_path), container_name, blob_name)

                    return {
                        "provider": "aws",
                        "bucket": container_name,
                        "key": blob_name,
                        "file_size": file_path.stat().st_size,
                        "upload_successful": True,
                        "timestamp": datetime.now().isoformat(),
                    }

                elif self.cloud_config.provider == "gcp":
                    # Google Cloud Storage
                    client = gcs.Client(project=self.cloud_config.project_id)
                    bucket = client.bucket(container_name)
                    blob = bucket.blob(blob_name)

                    blob.upload_from_filename(str(file_path))

                    return {
                        "provider": "gcp",
                        "bucket": container_name,
                        "blob_name": blob_name,
                        "file_size": file_path.stat().st_size,
                        "upload_successful": True,
                        "timestamp": datetime.now().isoformat(),
                    }

                else:
                    return {"error": f"Unsupported cloud provider: {self.cloud_config.provider}"}

            except Exception as e:
                logger.error(f"Cloud upload failed: {str(e)}")
                return {"error": f"Upload failed: {str(e)}"}

        self.add_tool(upload_file_to_cloud)

    def _register_monitoring_tools(self):
        """Register system monitoring and performance tools."""

        @tool()
        def get_system_metrics() -> dict[str, Any]:
            """
            Get comprehensive system performance metrics.

            Returns:
                Dictionary containing system metrics and performance data
            """
            try:
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu": {
                        "usage_percent": psutil.cpu_percent(interval=1),
                        "count": psutil.cpu_count(),
                        "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                    },
                    "memory": psutil.virtual_memory()._asdict(),
                    "disk": {
                        "usage": psutil.disk_usage("/")._asdict(),
                        "io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None,
                    },
                    "network": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None,
                    "processes": {
                        "total": len(psutil.pids()),
                        "top_cpu": [
                            {"pid": p.pid, "name": p.name(), "cpu_percent": p.cpu_percent()}
                            for p in sorted(
                                psutil.process_iter(["pid", "name", "cpu_percent"]),
                                key=lambda x: x.info["cpu_percent"],
                                reverse=True,
                            )[:5]
                        ],
                    },
                }

                return self._tool_result(
                    metrics,
                    schema_name="clippy-kernel.toolkit.system-metrics",
                    workflow="system-monitoring",
                    tags=["monitoring", "diagnostics", "system-metrics"],
                    capabilities=["monitoring", "diagnostics", "performance-analysis"],
                )

            except Exception as e:
                logger.error(f"System metrics collection failed: {str(e)}")
                return self._tool_error(
                    f"Metrics collection failed: {str(e)}",
                    schema_name="clippy-kernel.toolkit.system-metrics",
                    workflow="system-monitoring",
                    tags=["monitoring", "diagnostics", "system-metrics"],
                    capabilities=["monitoring", "diagnostics", "performance-analysis"],
                )

        self.add_tool(get_system_metrics)

    def _resolve_m365_copilot_package_roots(self) -> list[Path]:
        """Resolve local package roots for a checked-out Agents-M365Copilot repo."""
        repo_path = self.m365_copilot_config.repo_path
        if repo_path is None:
            return []

        root = Path(repo_path)
        if not root.exists():
            raise FileNotFoundError(f"Configured Agents-M365Copilot path does not exist: {root}")

        packages_root = root / "python" / "packages"
        if packages_root.exists():
            candidate_parent = packages_root
        elif (root / "microsoft_agents_m365copilot").exists() or (root / "microsoft_agents_m365copilot_core").exists():
            candidate_parent = root
        else:
            raise FileNotFoundError(
                "Could not locate `python\\packages` under the configured Agents-M365Copilot path. "
                "Point `m365_copilot_repo_path` at the repo root or the `python\\packages` directory."
            )

        package_roots = [
            candidate_parent / "microsoft_agents_m365copilot_core",
            candidate_parent / "microsoft_agents_m365copilot",
        ]
        missing_roots = [path for path in package_roots if not path.exists()]
        if missing_roots:
            missing_list = ", ".join(str(path) for path in missing_roots)
            raise FileNotFoundError(f"Missing required Agents-M365Copilot Python package roots: {missing_list}")

        return package_roots

    def _import_m365_copilot_module(self, module_name: str) -> Any:
        """Import an Agents-M365Copilot module from installed packages or a local repo checkout."""
        try:
            return importlib.import_module(module_name)
        except ImportError:
            package_roots = self._resolve_m365_copilot_package_roots()
            package_parents: list[Path] = []
            for package_root in package_roots:
                package_parent = package_root.parent
                if package_parent not in package_parents:
                    package_parents.append(package_parent)

            for package_parent in reversed(package_parents):
                package_parent_str = str(package_parent)
                if package_parent_str not in sys.path:
                    sys.path.insert(0, package_parent_str)
            importlib.invalidate_caches()
            return importlib.import_module(module_name)

    def _create_m365_copilot_credential(self) -> Any:
        """Create an Azure credential for the Microsoft 365 Copilot SDK."""
        try:
            azure_identity = importlib.import_module("azure.identity")
        except ImportError as exc:
            raise ImportError(
                "The `azure-identity` package is required for Microsoft 365 Copilot SDK tools."
            ) from exc

        credential_mode = self.m365_copilot_config.credential_mode.lower()
        tenant_id = self.m365_copilot_config.tenant_id

        if credential_mode == "default":
            return azure_identity.DefaultAzureCredential()

        if credential_mode == "device_code":
            client_id = self.m365_copilot_config.client_id
            if not client_id:
                raise ValueError(
                    "A client ID is required when `m365_copilot_credential_mode` is set to `device_code`."
                )

            def _prompt_callback(verification_uri: str, user_code: str, expires_on: datetime) -> None:
                logger.info(
                    "M365 Copilot device code sign-in required. Open %s, enter code %s, expires at %s.",
                    verification_uri,
                    user_code,
                    expires_on,
                )

            credential_kwargs: dict[str, Any] = {"client_id": client_id, "prompt_callback": _prompt_callback}
            if tenant_id:
                credential_kwargs["tenant_id"] = tenant_id
            return azure_identity.DeviceCodeCredential(**credential_kwargs)

        raise ValueError(
            "Unsupported `m365_copilot_credential_mode`. Use `default` or `device_code`."
        )

    def _create_m365_copilot_client(self) -> Any:
        """Create the stable Microsoft 365 Copilot service client."""
        sdk_module = self._import_m365_copilot_module("microsoft_agents_m365copilot")
        client_class = getattr(sdk_module, "AgentsM365CopilotServiceClient")
        scopes = list(self.m365_copilot_config.scopes or ["https://graph.microsoft.com/.default"])
        return client_class(credentials=self._create_m365_copilot_credential(), scopes=scopes)

    def _run_async_tool(self, operation: Any) -> Any:
        """Run an async toolkit operation even if the current thread already has an event loop."""
        if not inspect.isawaitable(operation):
            return operation

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(operation)

        result_holder: dict[str, Any] = {}
        error_holder: dict[str, BaseException] = {}

        def _runner() -> None:
            try:
                result_holder["value"] = asyncio.run(operation)
            except BaseException as exc:  # pragma: no cover - surfaced to caller
                error_holder["error"] = exc

        worker = threading.Thread(target=_runner, daemon=True)
        worker.start()
        worker.join()

        if "error" in error_holder:
            raise error_holder["error"]

        return result_holder.get("value")

    def _serialize_m365_copilot_value(self, value: Any) -> Any:
        """Convert SDK models into plain JSON-like structures."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, bytes):
            decoded = value.decode("utf-8", errors="replace")
            lines = decoded.splitlines()
            return {
                "text": decoded,
                "preview_lines": lines[:10],
                "line_count": len(lines),
                "byte_length": len(value),
            }

        if isinstance(value, Path):
            return str(value)

        if isinstance(value, Enum):
            enum_value = value.value
            if isinstance(enum_value, tuple) and len(enum_value) == 1:
                return enum_value[0]
            return enum_value

        if isinstance(value, dict):
            return {str(key): self._serialize_m365_copilot_value(item) for key, item in value.items()}

        if isinstance(value, (list, tuple, set)):
            return [self._serialize_m365_copilot_value(item) for item in value]

        if is_dataclass(value):
            return {field_info.name: self._serialize_m365_copilot_value(getattr(value, field_info.name)) for field_info in fields(value)}

        if hasattr(value, "__dict__"):
            return {
                key: self._serialize_m365_copilot_value(item)
                for key, item in vars(value).items()
                if not key.startswith("_")
            }

        return str(value)

    def _build_m365_request_configuration(self, query_cls: type[Any], config_cls: type[Any], **kwargs: Any) -> Any | None:
        """Build a request configuration only when query parameters are supplied."""
        query_values = {key: value for key, value in kwargs.items() if value is not None}
        if not query_values:
            return None
        return config_cls(query_parameters=query_cls(**query_values))

    def _resolve_m365_user_id(self, user_id: str | None) -> str:
        """Resolve a user identifier from the call or the default configuration."""
        resolved_user_id = user_id or self.m365_copilot_config.default_user_id
        if not resolved_user_id:
            raise ValueError(
                "A `user_id` is required unless `m365_copilot_default_user_id` is configured."
            )
        return resolved_user_id

    def _resolve_m365_retrieval_data_source(self, data_source: str) -> Any:
        """Resolve a friendly retrieval data source string to the SDK enum."""
        data_source_module = self._import_m365_copilot_module(
            "microsoft_agents_m365copilot.generated.models.retrieval_data_source"
        )
        data_source_enum = getattr(data_source_module, "RetrievalDataSource")
        normalized = data_source.replace("-", "").replace("_", "").replace(" ", "").lower()
        mapping = {
            "sharepoint": "SharePoint",
            "onedrivebusiness": "OneDriveBusiness",
            "externalitem": "ExternalItem",
            "unknownfuturevalue": "UnknownFutureValue",
        }
        member_name = mapping.get(normalized)
        if not member_name or not hasattr(data_source_enum, member_name):
            allowed = ", ".join(sorted(mapping))
            raise ValueError(f"Unsupported retrieval data source `{data_source}`. Use one of: {allowed}.")
        return getattr(data_source_enum, member_name)

    def _m365_error_guidance(self, error: Exception) -> list[str]:
        """Generate actionable guidance for common Microsoft 365 Copilot SDK failures."""
        error_text = str(error).lower()
        guidance: list[str] = []

        if "microsoft_agents_m365copilot" in error_text or "no module named" in error_text:
            guidance.append(
                "Install `microsoft-agents-m365copilot` and `microsoft-agents-m365copilot-core`, "
                "or set `m365_copilot_repo_path` to a local Agents-M365Copilot checkout."
            )

        if "azure-identity" in error_text or "defaultazurecredential" in error_text or "devicecodecredential" in error_text:
            guidance.append(
                "Install `azure-identity` or the `windows-clippy-mcp` extras before enabling M365 Copilot SDK tools."
            )

        if "credential" in error_text or "token" in error_text or "authentication" in error_text or "login" in error_text:
            guidance.append(
                "Authenticate with Azure CLI or configure a valid Azure credential source before using M365 Copilot SDK tools."
            )

        if "client id" in error_text or "device_code" in error_text:
            guidance.append(
                "Set `m365_copilot_client_id` when `m365_copilot_credential_mode` is `device_code`."
            )

        if "forbidden" in error_text or "license" in error_text or "consent" in error_text or "403" in error_text:
            guidance.append(
                "Ensure the tenant, app registration, API permissions, and Microsoft 365 Copilot licensing are all in place."
            )

        if isinstance(error, FileNotFoundError):
            guidance.append(
                "Point `m365_copilot_repo_path` at the local Agents-M365Copilot repo root if the SDK is not installed in the environment."
            )

        return guidance

    def _execute_m365_copilot_operation(
        self,
        *,
        operation_name: str,
        schema_name: str,
        workflow: str,
        tags: list[str],
        capabilities: list[str],
        action: Any,
        response_builder: Any,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a Microsoft 365 Copilot SDK operation and normalize the result."""
        operation_attributes = {
            "credential_mode": self.m365_copilot_config.credential_mode,
            "repo_path": str(self.m365_copilot_config.repo_path) if self.m365_copilot_config.repo_path else None,
        }
        if attributes:
            operation_attributes.update(attributes)

        try:
            client = self._create_m365_copilot_client()
            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter("always")
                response = self._run_async_tool(action(client))

            payload = response_builder(response)
            payload["operation"] = operation_name
            warning_messages = [str(item.message) for item in caught_warnings]
            if warning_messages:
                payload["warnings"] = warning_messages
        except Exception as exc:
            return self._tool_result(
                {
                    "error": str(exc),
                    "operation": operation_name,
                    "guidance": self._m365_error_guidance(exc),
                },
                schema_name=schema_name,
                workflow=workflow,
                tags=tags,
                capabilities=capabilities,
                attributes=operation_attributes,
                kind="tool-error",
            )

        return self._tool_result(
            payload,
            schema_name=schema_name,
            workflow=workflow,
            tags=tags,
            capabilities=capabilities,
            attributes=operation_attributes,
        )

    def _register_m365_copilot_tools(self):
        """Register Microsoft 365 Copilot SDK tools backed by the stable v1 Python client."""

        @tool(description="Run a Microsoft 365 Copilot retrieval query through the stable Python SDK.")
        def m365_copilot_retrieve(
            query: str,
            data_source: str = "sharePoint",
            max_results: int = 5,
            filter_expression: str | None = None,
            resource_metadata: list[str] | None = None,
        ) -> dict[str, Any]:
            if not query.strip():
                return self._tool_error(
                    "Query cannot be empty.",
                    schema_name="clippy-kernel.toolkit.m365-copilot-retrieval",
                    workflow="m365-copilot-sdk",
                    tags=["m365-copilot", "retrieval"],
                    capabilities=["m365-copilot-sdk", "enterprise-retrieval"],
                )

            if max_results <= 0:
                return self._tool_error(
                    "max_results must be greater than zero.",
                    schema_name="clippy-kernel.toolkit.m365-copilot-retrieval",
                    workflow="m365-copilot-sdk",
                    tags=["m365-copilot", "retrieval"],
                    capabilities=["m365-copilot-sdk", "enterprise-retrieval"],
                )

            try:
                retrieval_body_module = self._import_m365_copilot_module(
                    "microsoft_agents_m365copilot.generated.copilot.retrieval.retrieval_post_request_body"
                )
                retrieval_body = retrieval_body_module.RetrievalPostRequestBody()
                retrieval_body.query_string = query
                retrieval_body.data_source = self._resolve_m365_retrieval_data_source(data_source)
                retrieval_body.maximum_number_of_results = max_results
                retrieval_body.filter_expression = filter_expression
                retrieval_body.resource_metadata = resource_metadata
            except Exception as exc:
                return self._tool_result(
                    {
                        "error": str(exc),
                        "operation": "retrieval",
                        "guidance": self._m365_error_guidance(exc),
                    },
                    schema_name="clippy-kernel.toolkit.m365-copilot-retrieval",
                    workflow="m365-copilot-sdk",
                    tags=["m365-copilot", "retrieval"],
                    capabilities=["m365-copilot-sdk", "enterprise-retrieval"],
                    attributes={"query": query, "data_source": data_source, "max_results": max_results},
                    kind="tool-error",
                )

            return self._execute_m365_copilot_operation(
                operation_name="retrieval",
                schema_name="clippy-kernel.toolkit.m365-copilot-retrieval",
                workflow="m365-copilot-sdk",
                tags=["m365-copilot", "retrieval"],
                capabilities=["m365-copilot-sdk", "enterprise-retrieval"],
                attributes={"data_source": data_source, "max_results": max_results},
                action=lambda client: client.copilot.retrieval.post(retrieval_body),
                response_builder=lambda response: {
                    "query": query,
                    "data_source": data_source,
                    "max_results": max_results,
                    "hit_count": len(getattr(response, "retrieval_hits", []) or []),
                    "retrieval": self._serialize_m365_copilot_value(response),
                },
            )

        @tool(description="List Microsoft 365 Copilot AI users through the stable Python SDK.")
        def m365_copilot_list_users(
            top: int = 10,
            search: str | None = None,
            filter_expression: str | None = None,
            select: list[str] | None = None,
            orderby: list[str] | None = None,
            skip: int | None = None,
            include_count: bool | None = None,
        ) -> dict[str, Any]:
            async def _action(client: Any) -> Any:
                request_builder = client.copilot.users
                request_configuration = self._build_m365_request_configuration(
                    type(request_builder).UsersRequestBuilderGetQueryParameters,
                    type(request_builder).UsersRequestBuilderGetRequestConfiguration,
                    top=top,
                    search=search,
                    filter=filter_expression,
                    select=select,
                    orderby=orderby,
                    skip=skip,
                    count=include_count,
                )
                return await request_builder.get(request_configuration)

            return self._execute_m365_copilot_operation(
                operation_name="list-users",
                schema_name="clippy-kernel.toolkit.m365-copilot-users",
                workflow="m365-copilot-sdk",
                tags=["m365-copilot", "users"],
                capabilities=["m365-copilot-sdk", "directory-query"],
                attributes={"top": top},
                action=_action,
                response_builder=lambda response: {
                    "top": top,
                    "count": len(getattr(response, "value", []) or []),
                    "users": self._serialize_m365_copilot_value(response),
                },
            )

        @tool(description="Get a specific Microsoft 365 Copilot AI user through the stable Python SDK.")
        def m365_copilot_get_user(user_id: str | None = None, select: list[str] | None = None) -> dict[str, Any]:
            try:
                resolved_user_id = self._resolve_m365_user_id(user_id)
            except ValueError as exc:
                return self._tool_error(
                    str(exc),
                    schema_name="clippy-kernel.toolkit.m365-copilot-user",
                    workflow="m365-copilot-sdk",
                    tags=["m365-copilot", "users"],
                    capabilities=["m365-copilot-sdk", "directory-query"],
                )

            async def _action(client: Any) -> Any:
                request_builder = client.copilot.users.by_ai_user_id(resolved_user_id)
                request_configuration = self._build_m365_request_configuration(
                    type(request_builder).AiUserItemRequestBuilderGetQueryParameters,
                    type(request_builder).AiUserItemRequestBuilderGetRequestConfiguration,
                    select=select,
                )
                return await request_builder.get(request_configuration)

            return self._execute_m365_copilot_operation(
                operation_name="get-user",
                schema_name="clippy-kernel.toolkit.m365-copilot-user",
                workflow="m365-copilot-sdk",
                tags=["m365-copilot", "users"],
                capabilities=["m365-copilot-sdk", "directory-query"],
                attributes={"user_id": resolved_user_id},
                action=_action,
                response_builder=lambda response: {
                    "user_id": resolved_user_id,
                    "user": self._serialize_m365_copilot_value(response),
                },
            )

        @tool(description="List Microsoft 365 Copilot enterprise or user-scoped interactions through the stable Python SDK.")
        def m365_copilot_list_interactions(
            user_id: str | None = None,
            top: int = 10,
            search: str | None = None,
            filter_expression: str | None = None,
            select: list[str] | None = None,
            orderby: list[str] | None = None,
            skip: int | None = None,
            include_count: bool | None = None,
        ) -> dict[str, Any]:
            resolved_user_id = user_id or self.m365_copilot_config.default_user_id

            async def _action(client: Any) -> Any:
                if resolved_user_id:
                    request_builder = (
                        client.copilot.users.by_ai_user_id(resolved_user_id).interaction_history.get_all_enterprise_interactions
                    )
                else:
                    request_builder = client.copilot.interaction_history.get_all_enterprise_interactions

                request_configuration = self._build_m365_request_configuration(
                    type(request_builder).GetAllEnterpriseInteractionsRequestBuilderGetQueryParameters,
                    type(request_builder).GetAllEnterpriseInteractionsRequestBuilderGetRequestConfiguration,
                    top=top,
                    search=search,
                    filter=filter_expression,
                    select=select,
                    orderby=orderby,
                    skip=skip,
                    count=include_count,
                )
                return await request_builder.get(request_configuration)

            return self._execute_m365_copilot_operation(
                operation_name="list-interactions",
                schema_name="clippy-kernel.toolkit.m365-copilot-interactions",
                workflow="m365-copilot-sdk",
                tags=["m365-copilot", "interactions"],
                capabilities=["m365-copilot-sdk", "interaction-history"],
                attributes={"user_id": resolved_user_id, "top": top},
                action=_action,
                response_builder=lambda response: {
                    "user_id": resolved_user_id,
                    "count": len(getattr(response, "value", []) or []),
                    "interactions": self._serialize_m365_copilot_value(response),
                },
            )

        @tool(description="List Microsoft 365 Copilot user online meetings through the stable Python SDK.")
        def m365_copilot_list_user_online_meetings(
            user_id: str | None = None,
            top: int = 10,
            search: str | None = None,
            filter_expression: str | None = None,
            select: list[str] | None = None,
            orderby: list[str] | None = None,
            skip: int | None = None,
            include_count: bool | None = None,
        ) -> dict[str, Any]:
            try:
                resolved_user_id = self._resolve_m365_user_id(user_id)
            except ValueError as exc:
                return self._tool_error(
                    str(exc),
                    schema_name="clippy-kernel.toolkit.m365-copilot-online-meetings",
                    workflow="m365-copilot-sdk",
                    tags=["m365-copilot", "online-meetings"],
                    capabilities=["m365-copilot-sdk", "meeting-query"],
                )

            async def _action(client: Any) -> Any:
                request_builder = client.copilot.users.by_ai_user_id(resolved_user_id).online_meetings
                request_configuration = self._build_m365_request_configuration(
                    type(request_builder).OnlineMeetingsRequestBuilderGetQueryParameters,
                    type(request_builder).OnlineMeetingsRequestBuilderGetRequestConfiguration,
                    top=top,
                    search=search,
                    filter=filter_expression,
                    select=select,
                    orderby=orderby,
                    skip=skip,
                    count=include_count,
                )
                return await request_builder.get(request_configuration)

            return self._execute_m365_copilot_operation(
                operation_name="list-user-online-meetings",
                schema_name="clippy-kernel.toolkit.m365-copilot-online-meetings",
                workflow="m365-copilot-sdk",
                tags=["m365-copilot", "online-meetings"],
                capabilities=["m365-copilot-sdk", "meeting-query"],
                attributes={"user_id": resolved_user_id, "top": top},
                action=_action,
                response_builder=lambda response: {
                    "user_id": resolved_user_id,
                    "count": len(getattr(response, "value", []) or []),
                    "online_meetings": self._serialize_m365_copilot_value(response),
                },
            )

        @tool(description="Get Microsoft 365 Copilot admin settings through the stable Python SDK.")
        def m365_copilot_get_admin_settings(select: list[str] | None = None, expand: list[str] | None = None) -> dict[str, Any]:
            async def _action(client: Any) -> Any:
                request_builder = client.copilot.admin.settings
                request_configuration = self._build_m365_request_configuration(
                    type(request_builder).SettingsRequestBuilderGetQueryParameters,
                    type(request_builder).SettingsRequestBuilderGetRequestConfiguration,
                    select=select,
                    expand=expand,
                )
                return await request_builder.get(request_configuration)

            return self._execute_m365_copilot_operation(
                operation_name="get-admin-settings",
                schema_name="clippy-kernel.toolkit.m365-copilot-admin-settings",
                workflow="m365-copilot-sdk",
                tags=["m365-copilot", "admin"],
                capabilities=["m365-copilot-sdk", "admin-query"],
                action=_action,
                response_builder=lambda response: {"settings": self._serialize_m365_copilot_value(response)},
            )

        @tool(description="Get a Microsoft 365 Copilot usage report through the stable Python SDK.")
        def m365_copilot_get_usage_report(report: str, period: str) -> dict[str, Any]:
            normalized_report = report.strip().lower()
            if not normalized_report:
                return self._tool_error(
                    "Report cannot be empty.",
                    schema_name="clippy-kernel.toolkit.m365-copilot-usage-report",
                    workflow="m365-copilot-sdk",
                    tags=["m365-copilot", "reports"],
                    capabilities=["m365-copilot-sdk", "usage-reporting"],
                )

            report_mapping = {
                "user_detail": "get_microsoft365_copilot_usage_user_detail_with_period",
                "user_count_summary": "get_microsoft365_copilot_user_count_summary_with_period",
                "user_count_trend": "get_microsoft365_copilot_user_count_trend_with_period",
            }
            builder_method = report_mapping.get(normalized_report)
            if not builder_method:
                return self._tool_error(
                    "Unsupported report. Use `user_detail`, `user_count_summary`, or `user_count_trend`.",
                    schema_name="clippy-kernel.toolkit.m365-copilot-usage-report",
                    workflow="m365-copilot-sdk",
                    tags=["m365-copilot", "reports"],
                    capabilities=["m365-copilot-sdk", "usage-reporting"],
                )

            async def _action(client: Any) -> Any:
                request_builder = getattr(client.copilot.reports, builder_method)(period)
                return await request_builder.get()

            return self._execute_m365_copilot_operation(
                operation_name="get-usage-report",
                schema_name="clippy-kernel.toolkit.m365-copilot-usage-report",
                workflow="m365-copilot-sdk",
                tags=["m365-copilot", "reports"],
                capabilities=["m365-copilot-sdk", "usage-reporting"],
                attributes={"report": normalized_report, "period": period},
                action=_action,
                response_builder=lambda response: {
                    "report": normalized_report,
                    "period": period,
                    "report_data": self._serialize_m365_copilot_value(response),
                },
            )

        for sdk_tool in [
            m365_copilot_retrieve,
            m365_copilot_list_users,
            m365_copilot_get_user,
            m365_copilot_list_interactions,
            m365_copilot_list_user_online_meetings,
            m365_copilot_get_admin_settings,
            m365_copilot_get_usage_report,
        ]:
            self.add_tool(sdk_tool)

    def _build_workiq_command(self, question: str, tenant_id: str | None = None) -> tuple[list[str], str]:
        """Build the WorkIQ CLI invocation for a query."""
        resolved_tenant_id = tenant_id or self.workiq_config.tenant_id or "common"
        command_name = Path(self.workiq_config.command).name.lower()

        if command_name in {"workiq", "workiq.exe", "workiq.cmd", "workiq.ps1", "workiq.bat"}:
            cmd = [self.workiq_config.command, "ask"]
        else:
            cmd = [self.workiq_config.command, "-y", self.workiq_config.package_spec, "ask"]

        if resolved_tenant_id != "common":
            cmd.extend(["-t", resolved_tenant_id])

        cmd.extend(["-q", question])
        return cmd, resolved_tenant_id

    def _register_workiq_tools(self):
        """Register WorkIQ-backed workplace query tools."""

        @tool(description="Query Microsoft 365 workplace data through the WorkIQ CLI.")
        def ask_work_iq(question: str, tenant_id: str | None = None) -> dict[str, Any]:
            """
            Ask WorkIQ a Microsoft 365 workplace question.

            Prerequisites:
            - Node.js 18+ and the WorkIQ CLI available through npx or a global install
            - accepted WorkIQ EULA
            - tenant consent for the required Microsoft 365 permissions

            Args:
                question: Natural-language workplace question to send to WorkIQ
                tenant_id: Optional Entra tenant override for this query

            Returns:
                Dictionary containing WorkIQ output and execution metadata
            """
            if not question.strip():
                return self._tool_error(
                    "Question cannot be empty.",
                    schema_name="clippy-kernel.toolkit.workiq-query",
                    workflow="workiq-query",
                    tags=["workiq", "m365", "query"],
                    capabilities=["workplace-intelligence", "m365-query"],
                )

            cmd, resolved_tenant_id = self._build_workiq_command(question, tenant_id)

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=self.workiq_config.timeout,
                    check=False,
                )
            except FileNotFoundError:
                return self._tool_error(
                    (
                        "WorkIQ CLI command not found. Install Node.js 18+ and run WorkIQ via "
                        "`npx -y @microsoft/workiq@latest ...`, or point `workiq_command` at a "
                        "global `workiq` executable."
                    ),
                    schema_name="clippy-kernel.toolkit.workiq-query",
                    workflow="workiq-query",
                    tags=["workiq", "m365", "query"],
                    capabilities=["workplace-intelligence", "m365-query"],
                    attributes={"command": self.workiq_config.command},
                )
            except subprocess.TimeoutExpired:
                return self._tool_error(
                    f"WorkIQ query timed out after {self.workiq_config.timeout} seconds.",
                    schema_name="clippy-kernel.toolkit.workiq-query",
                    workflow="workiq-query",
                    tags=["workiq", "m365", "query"],
                    capabilities=["workplace-intelligence", "m365-query"],
                    attributes={"command": cmd, "tenant_id": resolved_tenant_id},
                )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode != 0:
                guidance = []
                failure_text = f"{stdout}\n{stderr}".lower()
                if "eula" in failure_text:
                    guidance.append("Run `workiq accept-eula` once before using this tool.")
                if "consent" in failure_text or "administrator" in failure_text or "admin" in failure_text:
                    guidance.append("Ensure the tenant administrator has granted the required WorkIQ consent.")

                return self._tool_result(
                    {
                        "error": stderr or stdout or f"WorkIQ command failed with exit code {result.returncode}.",
                        "command": cmd,
                        "question": question,
                        "tenant_id": resolved_tenant_id,
                        "stdout": stdout,
                        "stderr": stderr,
                        "guidance": guidance,
                    },
                    schema_name="clippy-kernel.toolkit.workiq-query",
                    workflow="workiq-query",
                    tags=["workiq", "m365", "query"],
                    capabilities=["workplace-intelligence", "m365-query"],
                    attributes={"exit_code": result.returncode, "tenant_id": resolved_tenant_id},
                    kind="tool-error",
                )

            return self._tool_result(
                {
                    "question": question,
                    "tenant_id": resolved_tenant_id,
                    "response": stdout,
                    "stderr": stderr or None,
                    "command": cmd,
                },
                schema_name="clippy-kernel.toolkit.workiq-query",
                workflow="workiq-query",
                tags=["workiq", "m365", "query"],
                capabilities=["workplace-intelligence", "m365-query"],
                attributes={"tenant_id": resolved_tenant_id},
            )

        self.add_tool(ask_work_iq)

    def _identify_project_patterns(self, project_path: Path) -> list[str]:
        """Identify common project patterns and frameworks."""
        patterns = []

        # Check for common files and directories
        if (project_path / "package.json").exists():
            patterns.append("Node.js/JavaScript project")
        if (project_path / "requirements.txt").exists() or (project_path / "pyproject.toml").exists():
            patterns.append("Python project")
        if (project_path / "pom.xml").exists():
            patterns.append("Maven/Java project")
        if (project_path / "Cargo.toml").exists():
            patterns.append("Rust project")
        if (project_path / ".git").exists():
            patterns.append("Git repository")
        if (project_path / "Dockerfile").exists():
            patterns.append("Docker containerized")
        if (project_path / ".github").exists():
            patterns.append("GitHub Actions")

        return patterns

    def _generate_readme_content(self, project_path: Path, format_type: str) -> str:
        """Generate README content for the project."""
        if format_type == "markdown":
            return f"""# {project_path.name}

## Overview

This project was analyzed by the clippy kernel agent development team.

## Getting Started

### Installation

```bash
# Add installation instructions here
```

### Usage

```bash
# Add usage examples here
```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the [License Name] - see the LICENSE file for details.

Generated by clippy kernel on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        return f"README for {project_path.name}"

    def _generate_api_docs(self, project_path: Path, format_type: str) -> str:
        """Generate API documentation for the project."""
        if format_type == "markdown":
            return f"""# API Documentation

## Overview

This document provides API documentation for {project_path.name}.

## Endpoints

### Example Endpoint

- **URL**: `/api/example`
- **Method**: `GET`
- **Description**: Example endpoint description

## Authentication

Describe authentication requirements here.

## Error Handling

Describe error handling and response codes here.

Generated by clippy kernel on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        return f"API Documentation for {project_path.name}"

    def _generate_examples_docs(self, project_path: Path, format_type: str) -> str:
        """Generate examples documentation for the project."""
        if format_type == "markdown":
            return f"""# Examples

## Overview

This document provides usage examples for {project_path.name}.

## Basic Usage

```python
# Add basic usage example here
```

## Advanced Usage

```python
# Add advanced usage example here
```

## Integration Examples

```python
# Add integration examples here
```

Generated by clippy kernel on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        return f"Examples for {project_path.name}"


def create_clippy_kernel_toolkit(
    enable_web_scraping: bool = True,
    enable_database: bool = False,
    enable_cloud: bool = False,
    enable_workiq: bool = False,
    web_config: WebScrapingConfig | None = None,
    db_config: DatabaseConfig | None = None,
    cloud_config: CloudConfig | None = None,
    workiq_config: WorkIQConfig | None = None,
    enable_m365_copilot: bool = False,
    m365_copilot_config: M365CopilotConfig | None = None,
) -> ClippyKernelToolkit:
    """
    Factory function to create a clippy kernel toolkit with specified features.

    Args:
        enable_web_scraping: Enable web scraping tools
        enable_database: Enable database tools
        enable_cloud: Enable cloud service tools
        enable_workiq: Enable WorkIQ workplace query tool
        enable_m365_copilot: Enable Microsoft 365 Copilot SDK tools
        web_config: Web scraping configuration
        db_config: Database configuration
        cloud_config: Cloud service configuration
        workiq_config: WorkIQ CLI configuration
        m365_copilot_config: Microsoft 365 Copilot SDK configuration

    Returns:
        Configured ClippyKernelToolkit instance
    """
    return ClippyKernelToolkit(
        web_config=web_config,
        db_config=db_config,
        cloud_config=cloud_config,
        workiq_config=workiq_config,
        m365_copilot_config=m365_copilot_config,
        enable_web_scraping=enable_web_scraping,
        enable_database=enable_database,
        enable_cloud=enable_cloud,
        enable_workiq=enable_workiq,
        enable_m365_copilot=enable_m365_copilot,
        enable_development_tools=True,  # Always enable dev tools
    )
