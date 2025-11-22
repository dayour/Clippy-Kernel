# Copyright (c) 2023 - 2025, Clippy Kernel Development Team
#
# SPDX-License-Identifier: Apache-2.0

"""
Clippy Kernel Enhanced MCP Tools

This module provides an extensive collection of MCP (Model Control Protocol) tools
specifically designed for Clippy Kernel's advanced multi-agent development workflows.
These tools extend beyond basic Windows desktop operations to include:

- Web scraping and API integration
- Database operations and data management
- Cloud service interactions (AWS, Azure, GCP)
- Development workflow automation
- File system and project management
- Real-time collaboration features
- Performance monitoring and analytics
"""

import json
import logging
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from ..import_utils import optional_import_block
from ..tools import Tool, Toolkit

logger = logging.getLogger(__name__)

# Optional imports for enhanced functionality
with optional_import_block():
    import requests
    import psutil
    import pandas as pd
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    import boto3
    from azure.storage.blob import BlobServiceClient
    from google.cloud import storage as gcs


@dataclass
class WebScrapingConfig:
    """Configuration for web scraping operations."""
    headless: bool = True
    timeout: int = 30
    user_agent: str = "Clippy-Kernel-Bot/1.0"
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
    credentials_path: Optional[Path] = None
    project_id: Optional[str] = None  # For GCP
    subscription_id: Optional[str] = None  # For Azure


class ClippyKernelToolkit(Toolkit):
    """
    Comprehensive toolkit for Clippy Kernel multi-agent development workflows.
    
    This toolkit provides advanced tools that go beyond basic MCP operations,
    enabling sophisticated development workflows, cloud integrations, and
    collaborative features for agent teams.
    """
    
    def __init__(
        self,
        web_config: Optional[WebScrapingConfig] = None,
        db_config: Optional[DatabaseConfig] = None,
        cloud_config: Optional[CloudConfig] = None,
        enable_web_scraping: bool = True,
        enable_database: bool = True,
        enable_cloud: bool = True,
        enable_development_tools: bool = True
    ):
        """
        Initialize the Clippy Kernel Toolkit.
        
        Args:
            web_config: Configuration for web scraping operations
            db_config: Configuration for database operations
            cloud_config: Configuration for cloud service operations
            enable_web_scraping: Enable web scraping tools
            enable_database: Enable database operation tools
            enable_cloud: Enable cloud service tools
            enable_development_tools: Enable development workflow tools
        """
        super().__init__()
        
        self.web_config = web_config or WebScrapingConfig()
        self.db_config = db_config
        self.cloud_config = cloud_config
        
        # Feature flags
        self.enable_web_scraping = enable_web_scraping
        self.enable_database = enable_database and db_config is not None
        self.enable_cloud = enable_cloud and cloud_config is not None
        self.enable_development_tools = enable_development_tools
        
        # Initialize tools
        self._register_tools()
        
        logger.info(f"ClippyKernelToolkit initialized with {len(self.tools)} tools")
    
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
        
        # System monitoring tools
        self._register_monitoring_tools()
    
    def _register_development_tools(self):
        """Register development workflow tools."""
        
        @Tool
        def analyze_codebase(
            project_path: str,
            include_tests: bool = True,
            include_docs: bool = True,
            file_extensions: Optional[List[str]] = None
        ) -> Dict[str, Any]:
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
                    return {"error": f"Project path does not exist: {project_path}"}
                
                extensions = file_extensions or ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h']
                
                analysis = {
                    "project_path": str(project),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "file_counts": {},
                    "line_counts": {},
                    "complexity_metrics": {},
                    "structure_analysis": {}
                }
                
                total_files = 0
                total_lines = 0
                
                for ext in extensions:
                    files = list(project.rglob(f"*{ext}"))
                    if not include_tests:
                        files = [f for f in files if 'test' not in str(f).lower()]
                    if not include_docs:
                        files = [f for f in files if 'doc' not in str(f).lower()]
                    
                    file_count = len(files)
                    line_count = 0
                    
                    for file_path in files:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
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
                    "average_lines_per_file": total_lines / max(total_files, 1)
                }
                
                # Analyze directory structure
                directories = [d for d in project.rglob("*") if d.is_dir()]
                analysis["structure_analysis"] = {
                    "total_directories": len(directories),
                    "max_depth": max([len(d.parts) - len(project.parts) for d in directories], default=0),
                    "common_patterns": self._identify_project_patterns(project)
                }
                
                return analysis
                
            except Exception as e:
                logger.error(f"Codebase analysis failed: {str(e)}")
                return {"error": f"Analysis failed: {str(e)}"}
        
        @Tool
        def run_code_quality_check(
            project_path: str,
            tools: List[str] = None,
            fix_issues: bool = False
        ) -> Dict[str, Any]:
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
                tools = tools or ['ruff', 'black', 'mypy']
                
                results = {
                    "project_path": str(project),
                    "timestamp": datetime.now().isoformat(),
                    "tool_results": {},
                    "summary": {}
                }
                
                for tool in tools:
                    try:
                        if tool == 'ruff':
                            cmd = ['ruff', 'check', str(project)]
                            if fix_issues:
                                cmd.append('--fix')
                        elif tool == 'black':
                            cmd = ['black', str(project)]
                            if not fix_issues:
                                cmd.append('--check')
                        elif tool == 'mypy':
                            cmd = ['mypy', str(project)]
                        else:
                            continue
                        
                        result = subprocess.run(
                            cmd, 
                            capture_output=True, 
                            text=True, 
                            cwd=project
                        )
                        
                        results["tool_results"][tool] = {
                            "exit_code": result.returncode,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "success": result.returncode == 0
                        }
                        
                    except FileNotFoundError:
                        results["tool_results"][tool] = {
                            "error": f"Tool '{tool}' not found in PATH"
                        }
                
                # Generate summary
                successful_tools = [t for t, r in results["tool_results"].items() 
                                  if r.get("success", False)]
                failed_tools = [t for t, r in results["tool_results"].items() 
                              if not r.get("success", False)]
                
                results["summary"] = {
                    "total_tools": len(tools),
                    "successful_tools": len(successful_tools),
                    "failed_tools": len(failed_tools),
                    "overall_success": len(failed_tools) == 0
                }
                
                return results
                
            except Exception as e:
                logger.error(f"Code quality check failed: {str(e)}")
                return {"error": f"Quality check failed: {str(e)}"}
        
        @Tool
        def generate_project_documentation(
            project_path: str,
            output_format: str = "markdown",
            include_api_docs: bool = True,
            include_examples: bool = True
        ) -> Dict[str, Any]:
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
                    "summary": {}
                }
                
                # Generate README if not exists
                readme_path = docs_dir / f"README.{output_format}"
                if not readme_path.exists():
                    readme_content = self._generate_readme_content(project, output_format)
                    with open(readme_path, 'w') as f:
                        f.write(readme_content)
                    results["generated_files"].append(str(readme_path))
                
                # Generate API documentation
                if include_api_docs:
                    api_docs_path = docs_dir / f"API.{output_format}"
                    api_content = self._generate_api_docs(project, output_format)
                    with open(api_docs_path, 'w') as f:
                        f.write(api_content)
                    results["generated_files"].append(str(api_docs_path))
                
                # Generate examples
                if include_examples:
                    examples_path = docs_dir / f"Examples.{output_format}"
                    examples_content = self._generate_examples_docs(project, output_format)
                    with open(examples_path, 'w') as f:
                        f.write(examples_content)
                    results["generated_files"].append(str(examples_path))
                
                results["summary"] = {
                    "total_files_generated": len(results["generated_files"]),
                    "documentation_complete": True
                }
                
                return results
                
            except Exception as e:
                logger.error(f"Documentation generation failed: {str(e)}")
                return {"error": f"Documentation generation failed: {str(e)}"}
        
        # Add tools to toolkit
        self.add_tool(analyze_codebase)
        self.add_tool(run_code_quality_check)
        self.add_tool(generate_project_documentation)
    
    def _register_web_scraping_tools(self):
        """Register web scraping and API integration tools."""
        
        @Tool
        def scrape_website(
            url: str,
            selectors: Optional[Dict[str, str]] = None,
            wait_for_element: Optional[str] = None,
            screenshot: bool = False
        ) -> Dict[str, Any]:
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
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    WebDriverWait(driver, self.web_config.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                    )
                
                results = {
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "title": driver.title,
                    "page_source_length": len(driver.page_source),
                    "extracted_content": {}
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
        
        @Tool
        def api_request(
            url: str,
            method: str = "GET",
            headers: Optional[Dict[str, str]] = None,
            data: Optional[Dict[str, Any]] = None,
            timeout: int = 30
        ) -> Dict[str, Any]:
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
                headers.setdefault('User-Agent', self.web_config.user_agent)
                
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if data else None,
                    timeout=timeout
                )
                
                results = {
                    "url": url,
                    "method": method,
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat(),
                    "headers": dict(response.headers),
                    "success": response.status_code < 400
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
        
        @Tool
        def execute_sql_query(
            query: str,
            parameters: Optional[List[Any]] = None,
            fetch_results: bool = True
        ) -> Dict[str, Any]:
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
                if self.db_config.connection_string.startswith('sqlite'):
                    db_path = self.db_config.connection_string.replace('sqlite:///', '')
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    if parameters:
                        cursor.execute(query, parameters)
                    else:
                        cursor.execute(query)
                    
                    results = {
                        "query": query,
                        "timestamp": datetime.now().isoformat(),
                        "rows_affected": cursor.rowcount
                    }
                    
                    if fetch_results and query.strip().upper().startswith('SELECT'):
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
        
        @Tool
        def analyze_database_schema(
            table_names: Optional[List[str]] = None
        ) -> Dict[str, Any]:
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
                if self.db_config.connection_string.startswith('sqlite'):
                    db_path = self.db_config.connection_string.replace('sqlite:///', '')
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
                        "tables": {}
                    }
                    
                    for table in tables_to_analyze:
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = cursor.fetchall()
                        
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        row_count = cursor.fetchone()[0]
                        
                        schema_info["tables"][table] = {
                            "columns": [
                                {
                                    "name": col[1],
                                    "type": col[2], 
                                    "nullable": not col[3],
                                    "primary_key": bool(col[5])
                                } for col in columns
                            ],
                            "row_count": row_count,
                            "column_count": len(columns)
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
        
        @Tool
        def upload_file_to_cloud(
            file_path: str,
            container_name: str,
            blob_name: Optional[str] = None
        ) -> Dict[str, Any]:
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
                
                if self.cloud_config.provider == 'azure':
                    # Azure Blob Storage
                    blob_service = BlobServiceClient.from_connection_string(
                        self.cloud_config.credentials_path.read_text()
                    )
                    blob_client = blob_service.get_blob_client(
                        container=container_name, 
                        blob=blob_name
                    )
                    
                    with open(file_path, 'rb') as data:
                        blob_client.upload_blob(data, overwrite=True)
                    
                    return {
                        "provider": "azure",
                        "container": container_name,
                        "blob_name": blob_name,
                        "file_size": file_path.stat().st_size,
                        "upload_successful": True,
                        "timestamp": datetime.now().isoformat()
                    }
                
                elif self.cloud_config.provider == 'aws':
                    # AWS S3
                    s3_client = boto3.client('s3')
                    s3_client.upload_file(
                        str(file_path), 
                        container_name, 
                        blob_name
                    )
                    
                    return {
                        "provider": "aws",
                        "bucket": container_name,
                        "key": blob_name,
                        "file_size": file_path.stat().st_size,
                        "upload_successful": True,
                        "timestamp": datetime.now().isoformat()
                    }
                
                elif self.cloud_config.provider == 'gcp':
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
                        "timestamp": datetime.now().isoformat()
                    }
                
                else:
                    return {"error": f"Unsupported cloud provider: {self.cloud_config.provider}"}
                
            except Exception as e:
                logger.error(f"Cloud upload failed: {str(e)}")
                return {"error": f"Upload failed: {str(e)}"}
        
        self.add_tool(upload_file_to_cloud)
    
    def _register_monitoring_tools(self):
        """Register system monitoring and performance tools."""
        
        @Tool
        def get_system_metrics() -> Dict[str, Any]:
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
                        "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                    },
                    "memory": psutil.virtual_memory()._asdict(),
                    "disk": {
                        "usage": psutil.disk_usage('/')._asdict(),
                        "io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None
                    },
                    "network": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None,
                    "processes": {
                        "total": len(psutil.pids()),
                        "top_cpu": [
                            {
                                "pid": p.pid,
                                "name": p.name(),
                                "cpu_percent": p.cpu_percent()
                            }
                            for p in sorted(
                                psutil.process_iter(['pid', 'name', 'cpu_percent']),
                                key=lambda x: x.info['cpu_percent'],
                                reverse=True
                            )[:5]
                        ]
                    }
                }
                
                return metrics
                
            except Exception as e:
                logger.error(f"System metrics collection failed: {str(e)}")
                return {"error": f"Metrics collection failed: {str(e)}"}
        
        self.add_tool(get_system_metrics)
    
    def _identify_project_patterns(self, project_path: Path) -> List[str]:
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

This project was analyzed by Clippy Kernel Agent Development Team.

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

Generated by Clippy Kernel on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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

Generated by Clippy Kernel on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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

Generated by Clippy Kernel on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return f"Examples for {project_path.name}"


def create_clippy_kernel_toolkit(
    enable_web_scraping: bool = True,
    enable_database: bool = False,
    enable_cloud: bool = False,
    web_config: Optional[WebScrapingConfig] = None,
    db_config: Optional[DatabaseConfig] = None,
    cloud_config: Optional[CloudConfig] = None
) -> ClippyKernelToolkit:
    """
    Factory function to create a Clippy Kernel Toolkit with specified features.
    
    Args:
        enable_web_scraping: Enable web scraping tools
        enable_database: Enable database tools
        enable_cloud: Enable cloud service tools
        web_config: Web scraping configuration
        db_config: Database configuration
        cloud_config: Cloud service configuration
        
    Returns:
        Configured ClippyKernelToolkit instance
    """
    return ClippyKernelToolkit(
        web_config=web_config,
        db_config=db_config,
        cloud_config=cloud_config,
        enable_web_scraping=enable_web_scraping,
        enable_database=enable_database,
        enable_cloud=enable_cloud,
        enable_development_tools=True  # Always enable dev tools
    )