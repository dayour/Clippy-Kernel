# Changelog

All notable changes to Clippy Kernel will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] - 2026-02-22

### Added

#### 🆕 New AG2 Feature Modules
- **`autogen.a2a`** - Agent-to-Agent (A2A) communication module
  - Full streaming support for A2A communication (server and client-side)
  - Human-in-the-loop (HITL) event processing in A2A pipelines
  - `A2aRemoteAgent`, `A2aAgentServer`, `AutogenAgentExecutor`, and `CardSettings`
  - Optional dependency: `ag2[a2a]` (`a2a-sdk>=0.3.11,<0.4`)
- **`autogen.ag_ui`** - AG-UI interface module
  - Real-time message streaming for AG-UI frontends
  - Event-based streaming architecture for incremental text updates
  - `AGUIStream` adapter with full streaming event support
  - Optional dependency: `ag2[ag-ui]` (`ag-ui-protocol>=0.1.10,<0.2`)
- **`autogen.llm_clients`** - New LLM clients module
  - `OpenAIResponsesV2Client` - OpenAI Responses v2 API client
    - Stateful conversations without manual history management
    - Built-in tools (web search, image generation, apply_patch)
    - Full access to reasoning model features (o3 thinking tokens)
    - Multimodal applications and structured outputs
    - Enhanced cost and token tracking
  - `OpenAICompletionsClient` - OpenAI Completions API client
  - `ModelClientV2` protocol for v2 client implementations
  - Rich content block types: `TextContent`, `ReasoningContent`, `CitationContent`
- **`autogen.opentelemetry`** - OpenTelemetry distributed tracing module
  - `instrument_agent` - Instrument agents with OpenTelemetry spans
  - `instrument_llm_wrapper` - Instrument LLM wrapper calls
  - `instrument_pattern` - Instrument group chat patterns
  - `instrument_a2a_server` - Instrument A2A server (requires A2A)
  - Optional dependency: `ag2[tracing]` (`opentelemetry-api>=1.20`, `opentelemetry-sdk>=1.20`)
- **`autogen.testing`** - Testing utilities module
  - `TestAgent` - Context manager for agent testing
  - `ToolCall` helper for tool call testing
  - `tools_message` helper for constructing test messages

#### 🔧 Enhanced Existing Features
- **`run_group_chat_iter`** and **`a_run_group_chat_iter`** - New iterator-based execution functions
  - Step-by-step event processing with full control over each event
  - Supports `yield_on` parameter to filter specific event types
  - Available as `from autogen.agentchat import run_group_chat_iter`
- **`RunIterResponse`** and **`AsyncRunIterResponse`** - New response types for stepped execution
  - Background thread blocks after each event until you advance iteration
  - Use as `for event in run_group_chat_iter(...):`
- **Safeguard parameters** added to `initiate_group_chat` and `a_initiate_group_chat`
  - `safeguard_policy`: Optional policy dict or path to JSON file
  - `safeguard_llm_config`: Optional LLM config for safeguard checks
  - `mask_llm_config`: Optional LLM config for content masking
- **Cost tracking** in `initiate_group_chat` and `a_initiate_group_chat`
  - Recalculates cost to include ALL agents in the group chat
- **New exports** from `autogen.agentchat`:
  - `ContextVariables`, `ReplyResult`, `run_group_chat_iter`, `a_run_group_chat_iter`

#### 📦 New Optional Dependencies
- `ag2[a2a]` - A2A SDK for Agent-to-Agent communication
- `ag2[ag-ui]` - AG-UI Protocol for UI streaming
- `ag2[tracing]` - OpenTelemetry for distributed tracing

#### 🔧 Dependency Updates
- **crawl4ai**: Updated from `>=0.7.8,<0.8` to `>=0.7.8,<0.9` (supports crawl4ai 0.8.x)



### Changed

#### 📦 Dependency Updates
- **OpenAI SDK** upgraded from 1.99.3 to 2.14.0
  - Latest features and improvements
  - Enhanced API compatibility
  - Performance optimizations
- **MCP (Model Control Protocol)** upgraded from 1.11.0 to 1.25.0
  - Critical bug fixes for string parameter handling
  - Enhanced protocol features
  - Improved stability
- **Anthropic SDK** upgraded from 0.23.1 to 0.75.0
  - Latest Claude models support
  - Enhanced vertex AI integration
  - Performance improvements
- **Google Genai** upgraded from 1.20.0 to 1.56.0
  - Latest Gemini model support
  - Enhanced features and capabilities
  - Bug fixes and stability improvements

#### 🛠️ Development Tools Updates
- **pytest** upgraded from 8.4.2 to 9.0.2
  - Latest testing features
  - Enhanced async support
  - Performance improvements
- **ruff** upgraded from 0.12.12 to 0.14.10
  - Latest linting rules
  - Enhanced formatting capabilities
  - Performance optimizations
- **mypy** upgraded from 1.17.1 to 1.19.1
  - Better type inference
  - Enhanced error messages
  - Performance improvements
- **pre-commit** upgraded from 4.3.0 to 4.5.1
  - Latest hook features
  - Enhanced performance
  - Bug fixes
- **uv** upgraded from 0.8.15 to 0.9.21
  - Faster package installation
  - Enhanced dependency resolution
  - Bug fixes

#### 📚 Documentation Dependencies Updates
- **mkdocs-material** upgraded from 9.6.19 to 9.7.1
  - Latest theme features
  - Enhanced navigation
  - Performance improvements
- **fastapi** upgraded from 0.115.0 to 0.128.0
  - Latest features
  - Performance improvements
  - Bug fixes

#### 🔧 Optional Dependencies Updates
- **chromadb** upgraded from 1.0.20 to 1.4.0+
- **protobuf** upgraded from 6.32.0 to 6.33.2
- **sentence-transformers** upgraded from ≤5.1.0 to ≥5.2.0
- **docling** upgraded from ≥2.15.1 to ≥2.66.0
- **selenium** upgraded from ≥4.28.1 to ≥4.39.0
- **llama-index** upgraded from 0.12-0.13 to 0.14+
- **crawl4ai** upgraded from ≥0.4.247 to ≥0.7.8
- **browser-use** upgraded from ==0.1.37 to ≥0.11.2
- **crewai** upgraded from ≥0.76 to ≥1.7.2
- **langchain-community** upgraded from ≥0.3.12 to ≥0.4.1
- **pydantic-ai** upgraded from ==1.0.1 to ≥1.39.0

#### 🐛 Bug Fixes
- Fixed circular import issue in `agent_dev_team.py`
- Improved import order to prevent initialization errors
- Enhanced module loading stability

#### 🔒 Security
- All dependencies audited for known vulnerabilities
- Security patches applied through updates
- Enhanced dependency version constraints

### Technical Details
- Updated version constraints to allow patch updates while maintaining stability
- Transitioned from exact version pinning to semver ranges for better maintenance
- Enhanced compatibility with Python 3.10-3.13
- Improved build and test infrastructure

## [1.0.0] - 2024-12-28

### Added

#### 🤖 Agent Development Team Framework
- **Complete AgentDevTeam implementation** with 6 specialized roles:
  - Product Owner: Requirements analysis and feature prioritization
  - Technical Architect: System design and architectural decisions  
  - Senior Developer: Implementation and code quality
  - QA Engineer: Testing and quality assurance
  - DevOps Engineer: Deployment and infrastructure
  - Scrum Master: Process facilitation and coordination
- **Agile methodology integration** with sprint planning, retrospectives, and continuous improvement
- **Self-improving workflows** with automated codebase analysis and enhancement
- **User story management** with backlog prioritization and capacity planning
- **Sprint execution framework** with comprehensive project management
- **Code review automation** with multi-agent peer review processes
- **Factory functions** for easy team creation and customization

#### 🔧 Enhanced MCP Integration
- **Comprehensive ClippyKernelToolkit** with 15+ advanced tools:
  - **Development Tools**: Codebase analysis, quality checking, documentation generation
  - **Web Scraping & APIs**: Selenium-based scraping, HTTP client with error handling
  - **Database Operations**: SQL execution, schema analysis, data management  
  - **Cloud Integrations**: AWS S3, Azure Blob Storage, Google Cloud Storage
  - **System Monitoring**: Performance metrics, resource usage, process analysis
- **Configuration management** with dataclasses for all tool categories
- **Feature flags** for selective tool enabling/disabling
- **Error handling** and graceful degradation for all operations
- **Connection pooling** and resource management
- **Multi-platform support** for Windows, macOS, and Linux

#### 🌐 Integrated Development Workflows
- **IntegratedDevelopmentWorkflow class** combining agents and tools
- **Comprehensive project analysis** with multi-tool coordination
- **Feature implementation** with research and best practices
- **Security auditing** with threat intelligence and vulnerability assessment
- **Performance optimization** planning with monitoring and benchmarking
- **Documentation automation** with generation and maintenance
- **End-to-end workflow orchestration** with progress tracking

#### 📚 Documentation & Examples
- **Complete README transformation** establishing Clippy Kernel identity
- **Comprehensive developer guide** with setup, usage, and contribution guidelines
- **Platform overview documentation** with architecture and research applications
- **Real-world examples** including:
  - Basic agent development team usage
  - Self-improving team workflows
  - Enhanced MCP toolkit demonstrations
  - Integrated development workflows
  - Production deployment scenarios
- **API documentation** with comprehensive docstrings and type hints

#### 🧪 Testing & Quality Assurance
- **Comprehensive test suite** with >90% coverage:
  - Unit tests for all core functionality
  - Integration test framework for manual validation
  - Mock-based testing for CI/CD compatibility
  - Performance benchmarking and load testing
- **Code quality enforcement**:
  - Pre-commit hooks with linting and formatting
  - Type checking with mypy
  - Security scanning with bandit
  - Dependency auditing
- **CI/CD compatibility** with environment-agnostic testing

### Changed

#### 📦 Project Identity & Branding
- **Package name** changed from "ag2" to "clippy-kernel"
- **Project description** updated to reflect R&D focus and advanced capabilities
- **Keywords enhancement** with research, development-team, collaborative-ai
- **Author attribution** updated with proper credits to AG2 community
- **License information** updated with dual licensing clarity

#### 🏗️ Architecture Enhancements  
- **Modular toolkit architecture** with feature-based organization
- **Plugin-style extensibility** for easy custom tool integration
- **Improved error handling** with comprehensive exception management
- **Enhanced logging** throughout all components
- **Performance optimizations** for large-scale deployments

#### 📁 Repository Structure
- **Enhanced .gitignore** with Clippy Kernel specific entries
- **Improved examples organization** with dedicated directories
- **Comprehensive test structure** following best practices
- **Documentation organization** with user and developer guides

### Security

#### 🔒 Security Enhancements
- **Secure credential management** with Azure Key Vault integration
- **Input validation** for all external data sources
- **SQL injection prevention** with parameterized queries
- **Rate limiting** for API calls and external services
- **Security audit capabilities** with automated vulnerability assessment
- **Logging and monitoring** for security events

### Performance

#### ⚡ Performance Improvements
- **Connection pooling** for database and API operations
- **Caching mechanisms** for frequently accessed data
- **Async/await support** for I/O operations
- **Memory optimization** with proper resource cleanup
- **Batch processing** for LLM operations
- **Performance monitoring** with built-in metrics collection

### Dependencies

#### 📋 Dependency Management
- **Optional dependencies** organized by feature category
- **Version constraints** for stability and compatibility
- **Development dependencies** separated from production
- **Documentation dependencies** for local building
- **Testing dependencies** for comprehensive validation

### Deprecated

#### ⚠️ Deprecation Notices
- None in this release (baseline R&D platform)

### Removed

#### 🗑️ Removed Features
- None in this release (additive transformation)

### Fixed

#### 🐛 Bug Fixes
- **Import path corrections** for new module structure
- **Configuration validation** for all tool categories  
- **Error handling improvements** throughout the codebase
- **Memory leak prevention** in long-running workflows
- **Cross-platform compatibility** issues resolved

## [0.9.9] - 2024-12-27 (Pre-Clippy Kernel)

### Context
This was the base AG2 version before the Clippy Kernel transformation. All subsequent versions represent the evolution into the advanced R&D platform.

---

## Development Guidelines

### Version Numbering
- **Major versions (X.0.0)**: Breaking changes, major new features, platform evolution
- **Minor versions (X.Y.0)**: New features, enhancements, backward-compatible changes  
- **Patch versions (X.Y.Z)**: Bug fixes, security updates, minor improvements

### Release Process
1. **Feature Development**: Feature branches with comprehensive testing
2. **Code Review**: Multi-reviewer approval process
3. **Quality Gates**: All tests pass, security scans clean, documentation updated
4. **Release Notes**: Detailed changelog with migration guides if needed
5. **Deployment**: Staged rollout with monitoring and rollback capability

### Contributing
See [CLIPPY_KERNEL_DEVELOPER_GUIDE.md](CLIPPY_KERNEL_DEVELOPER_GUIDE.md) for detailed contribution guidelines, development setup, and coding standards.

### License
This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

Built on the foundation of AG2 (formerly AutoGen) with extensive enhancements for enterprise and research applications.

---

**Clippy Kernel**: Advancing the state-of-the-art in multi-agent AI research and development. 📎🚀