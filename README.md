<a name="readme-top"></a>

<p align="center">
  <!-- Clippy Kernel - Advanced R&D Fork of AG2 -->
  <h1 align="center">📎 Clippy Kernel</h1>
  
  <p align="center"><i>Advanced R&D Fork of AG2 with Extensible Agent Development Platform</i></p>

  <br>

  <a href="https://github.com/dayour/Clippy-Kernel/actions">
    <img src="https://github.com/dayour/Clippy-Kernel/workflows/CI/badge.svg" alt="CI Status">
  </a>
  
  <img src="https://img.shields.io/pypi/pyversions/ag2.svg?label=Python">
  
  <a href="https://github.com/dayour/Clippy-Kernel">
    <img src="https://img.shields.io/github/stars/dayour/Clippy-Kernel?style=social" alt="GitHub Stars">
  </a>

  <br>
  <br>

  <a href="#getting-started">🚀 Quick Start</a> |
  <a href="#agent-dev-team">🤖 Agent Dev Team</a> |
  <a href="#clippy-mcp-integration">🔧 Clippy MCP</a> |
  <a href="#examples">💡 Examples</a> |
  <a href="#contributing">🤝 Contributing</a>
</p>

<p align="center">
  <strong>Clippy Kernel</strong> is an advanced R&D fork of AG2 (formerly AutoGen) designed for cutting-edge multi-agent AI research and development. 
  <br>Built with extensible architecture, enterprise-grade MCP integration, and self-improving agent development teams.
</p>

---

# 📎 Clippy Kernel: Next-Generation Agent Development Platform

**Clippy Kernel** is an advanced research and development fork of AG2 (formerly AutoGen), specifically designed for cutting-edge multi-agent AI experimentation and enterprise-grade deployment. Our platform extends the core AG2 framework with:

- 🤖 **Self-Improving Agent Dev Teams**: Collaborative AI agents that iteratively improve codebases using agile methodologies
- 🔧 **Extensible Clippy MCP Integration**: Enterprise-grade Model Control Protocol with Windows desktop, Azure, and VSCode integration
- 🏗️ **Advanced Orchestration Patterns**: Sophisticated multi-agent workflows with real-time coordination and memory persistence
- 🌐 **Comprehensive Tool Ecosystem**: Extensive integrations for web scraping, database operations, cloud services, and development workflows
- 🧠 **Context-Aware Memory Engine**: Persistent agent memory with cross-session knowledge retention and Azure backend support

This R&D platform enables researchers, developers, and enterprises to push the boundaries of what's possible with collaborative AI systems. Built on the solid foundation of AG2, Clippy Kernel adds production-ready features for real-world deployment scenarios.

## Table of contents

- [📎 Clippy Kernel: Next-Generation Agent Development Platform](#-clippy-kernel-next-generation-agent-development-platform)
  - [Table of contents](#table-of-contents)
  - [🚀 Getting started](#-getting-started)
    - [Quick Installation](#quick-installation)
    - [Setup your API keys](#setup-your-api-keys)
    - [Run your first agent](#run-your-first-agent)
  - [🤖 Agent Development Team](#-agent-development-team)
  - [🔧 Clippy MCP Integration](#-clippy-mcp-integration)
  - [💡 Advanced Examples](#-advanced-examples)
  - [🏗️ Architecture & Concepts](#️-architecture--concepts)
    - [Conversable agent](#conversable-agent)
    - [Human in the loop](#human-in-the-loop)
    - [Orchestrating multiple agents](#orchestrating-multiple-agents)
    - [Tools & Extensions](#tools--extensions)
    - [Advanced agentic design patterns](#advanced-agentic-design-patterns)
  - [📦 Deployment & Production](#-deployment--production)
  - [🧪 Testing & Development](#-testing--development)
  - [📚 Documentation](#-documentation)
  - [🎯 Roadmap & Research Areas](#-roadmap--research-areas)
  - [🤝 Contributing](#-contributing)
  - [📄 License](#-license)

## 🚀 Getting started

For a comprehensive walk-through of Clippy Kernel concepts and advanced features, see our [Documentation](website/docs/) and [Examples](examples/) directories.

### Quick Installation

Clippy Kernel requires **Python version >= 3.10, < 3.14**. Install with enhanced features:

**Standard Installation:**
```bash
pip install -e ".[openai,windows-clippy-mcp]"
```

**Full R&D Installation (Recommended):**
```bash
# Using UV (faster)
uv pip install -e ".[openai,windows-clippy-mcp,dev,mcp,browser-use,retrievechat]"

# Using pip
pip install -e ".[openai,windows-clippy-mcp,dev,mcp,browser-use,retrievechat]"
```

**Quick Deployment (One Command):**
```bash
python scripts/deploy_windows_clippy_mcp.py --full-setup
```

### Setup your API keys

To keep your LLM dependencies neat and avoid accidentally checking in code with your API key, we recommend storing your keys in a configuration file.

In our examples, we use a file named **`OAI_CONFIG_LIST`** to store API keys. You can choose any filename, but make sure to add it to `.gitignore` so it will not be committed to source control.

You can use the following content as a template:

```json
[
  {
    "model": "gpt-5",
    "api_key": "<your OpenAI API key here>"
  }
]
```

### Run your first agent

Create a script or a Jupyter Notebook and run your first agent.

```python
from autogen import AssistantAgent, UserProxyAgent, LLMConfig

llm_config = LLMConfig.from_json(path="OAI_CONFIG_LIST")

assistant = AssistantAgent("assistant", llm_config=llm_config)

user_proxy = UserProxyAgent("user_proxy", code_execution_config={"work_dir": "coding", "use_docker": False})

user_proxy.run(assistant, message="Analyze this codebase and suggest improvements using Clippy Kernel's agent dev team approach.").process()
```

## 🤖 Agent Development Team

Clippy Kernel's revolutionary **Agent Development Team** feature creates collaborative AI teams that follow agile methodologies to iteratively improve codebases, implement features, and conduct code reviews.

### Core Agent Roles

```python
from autogen import ConversableAgent, LLMConfig
from autogen.agentchat import run_group_chat
from autogen.agentchat.group.patterns import AutoPattern

llm_config = LLMConfig.from_json(path="OAI_CONFIG_LIST")

# Product Owner - Defines requirements and priorities
product_owner = ConversableAgent(
    name="product_owner",
    system_message="""You are an experienced Product Owner who:
    - Defines clear user stories and acceptance criteria
    - Prioritizes features based on business value
    - Communicates requirements to the development team
    - Ensures deliverables meet stakeholder needs""",
    llm_config=llm_config,
)

# Technical Architect - Designs system architecture
tech_architect = ConversableAgent(
    name="tech_architect", 
    system_message="""You are a Senior Technical Architect who:
    - Designs scalable, maintainable system architectures
    - Makes technology stack decisions
    - Defines coding standards and patterns
    - Reviews architectural decisions for long-term viability""",
    llm_config=llm_config,
)

# Senior Developer - Implements complex features
senior_dev = ConversableAgent(
    name="senior_developer",
    system_message="""You are a Senior Software Developer who:
    - Implements complex features and algorithms
    - Mentors junior developers
    - Ensures code quality and best practices
    - Optimizes performance and scalability""",
    llm_config=llm_config,
)

# QA Engineer - Tests and validates quality
qa_engineer = ConversableAgent(
    name="qa_engineer",
    system_message="""You are a Quality Assurance Engineer who:
    - Creates comprehensive test plans and test cases
    - Performs manual and automated testing
    - Identifies bugs and edge cases
    - Ensures quality standards are met""",
    llm_config=llm_config,
)

# DevOps Engineer - Handles deployment and infrastructure
devops_engineer = ConversableAgent(
    name="devops_engineer",
    system_message="""You are a DevOps Engineer who:
    - Manages CI/CD pipelines and automation
    - Handles infrastructure and deployment
    - Monitors system performance and reliability
    - Implements security and compliance measures""",
    llm_config=llm_config,
)

# Scrum Master - Facilitates agile processes
scrum_master = ConversableAgent(
    name="scrum_master",
    system_message="""You are a Scrum Master who:
    - Facilitates sprint planning and retrospectives
    - Removes blockers and impediments
    - Ensures team follows agile principles
    - Coordinates team communication and collaboration
    When the sprint is complete, output: SPRINT_COMPLETE!""",
    is_termination_msg=lambda x: "SPRINT_COMPLETE!" in (x.get("content", "") or "").upper(),
    llm_config=llm_config,
)

# Create the Agent Dev Team
agent_dev_team = AutoPattern(
    agents=[product_owner, tech_architect, senior_dev, qa_engineer, devops_engineer, scrum_master],
    initial_agent=scrum_master,
    group_manager_args={"name": "team_lead", "llm_config": llm_config},
)

# Run a sprint planning session
response = run_group_chat(
    pattern=agent_dev_team,
    messages="""Let's plan a sprint to implement a new feature: 
    'Add real-time collaboration capabilities to Clippy Kernel agents with WebSocket support and shared memory persistence.'
    
    Please conduct sprint planning, define user stories, create tasks, and establish a development plan.""",
    max_rounds=25,
)

response.process()
```

### Agile Methodology Integration

The Agent Development Team follows established agile practices:

- **Sprint Planning**: Automated backlog grooming and task estimation
- **Daily Standups**: Progress tracking and blocker identification
- **Code Reviews**: Multi-agent peer review process
- **Retrospectives**: Continuous improvement recommendations
- **Testing Integration**: Automated test generation and validation

## 🔧 Clippy MCP Integration

Clippy Kernel includes a comprehensive Model Control Protocol (MCP) integration that extends far beyond basic Windows desktop operations:

### Enterprise Features
- **Azure Integration**: Key Vault, Entra ID, and Managed Identity support
- **VSCode Extension**: Auto-generated TypeScript extension with real-time communication
- **Memory Engine**: Persistent context with agent-aware storage
- **Multi-Platform Support**: Windows, macOS, and Linux compatibility

### Quick Setup
```bash
# Deploy complete MCP integration
python scripts/deploy_windows_clippy_mcp.py

# Manual configuration
pip install -e ".[windows-clippy-mcp]"
```

### Usage Example
```python
from autogen.mcp.clippy_mcp import WindowsClippyMCPClient, ClippyMCPConfig

# Configure Clippy MCP
config = ClippyMCPConfig(
    clippy_executable_path="/path/to/clippy.exe",
    vscode_extension_enabled=True,
    memory_engine_enabled=True,
    azure_key_vault_url="https://your-vault.vault.azure.net/"
)

# Create MCP client
clippy_client = WindowsClippyMCPClient(config)

# Use with agents
from autogen import ConversableAgent
from autogen.tools import Toolkit

agent = ConversableAgent("clippy_agent", llm_config=llm_config)
toolkit = Toolkit.from_mcp_client(clippy_client)
toolkit.register_for_llm(agent)
toolkit.register_for_execution(agent)
```

## 💡 Advanced Examples

Explore our comprehensive collection of advanced examples and use cases:

- **[Agent Development Team Examples](examples/agent_dev_team/)** - Complete agile development workflows
- **[Clippy MCP Integration](examples/clippy_mcp/)** - Enterprise desktop and cloud integrations  
- **[Multi-Agent Research Projects](examples/research/)** - Cutting-edge R&D scenarios
- **[Production Deployment](examples/deployment/)** - Enterprise-grade deployment patterns
- **[Interactive Notebooks](notebook/)** - Hands-on tutorials and experiments

### Featured Examples

**1. Self-Improving Codebase Agent Team**
```python
# Create a team that continuously improves its own codebase
from examples.agent_dev_team import create_self_improving_team

team = create_self_improving_team(
    project_path="./",  
    focus_areas=["performance", "maintainability", "test_coverage"]
)

improvements = team.run_improvement_sprint(
    message="Analyze the current codebase and implement 3 high-impact improvements",
    max_iterations=5
)
```

**2. Enterprise Knowledge Management System**
```python
# Deploy a multi-agent knowledge management system
from examples.enterprise import KnowledgeManagementSystem

km_system = KnowledgeManagementSystem(
    data_sources=["confluence", "sharepoint", "github"],
    embedding_model="text-embedding-ada-002",
    vector_store="azure-search"
)

response = km_system.query(
    "What are our best practices for microservices architecture?"
)
```

**3. Real-time Collaborative Development**
```python
# Enable real-time collaboration between human and AI agents
from examples.collaboration import RealTimeDevEnvironment

dev_env = RealTimeDevEnvironment(
    websocket_port=8765,
    shared_memory_backend="redis",
    ide_integration=True
)

# Agents can collaborate in real-time with developers
session = dev_env.start_collaboration_session(
    participants=["human_developer", "code_review_agent", "test_generator_agent"]
)
```

## 🏗️ Architecture & Concepts

Clippy Kernel extends AG2's core concepts with advanced R&D features. Here are the fundamental building blocks:

- **Conversable Agent**: Enhanced agents with persistent memory and context awareness
- **Human in the loop**: Advanced human-AI collaboration patterns with real-time feedback
- **Multi-agent orchestration**: Sophisticated patterns including swarms, hierarchies, and self-organizing teams
- **Tools & Extensions**: Comprehensive tool ecosystem with MCP integration and cloud services
- **Advanced Concepts**: Memory persistence, context switching, agent specialization, and performance optimization

### Conversable agent

The [ConversableAgent](https://docs.ag2.ai/latest/docs/api-reference/autogen/ConversableAgent) is the fundamental building block of AG2, designed to enable seamless communication between AI entities. This core agent type handles message exchange and response generation, serving as the base class for all agents in the framework.

Let's begin with a simple example where two agents collaborate:
- A **coder agent** that writes Python code.
- A **reviewer agent** that critiques the code without rewriting it.

```python
import logging
from autogen import ConversableAgent, LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load LLM configuration
llm_config = LLMConfig.from_json(path="OAI_CONFIG_LIST")

# Define agents
coder = ConversableAgent(
    name="coder",
    system_message="You are a Python developer. Write short Python scripts.",
    llm_config=llm_config,
)

reviewer = ConversableAgent(
    name="reviewer",
    system_message="You are a code reviewer. Analyze provided code and suggest improvements. "
                   "Do not generate code, only suggest improvements.",
    llm_config=llm_config,
)

# Start a conversation
response = reviewer.run(
            recipient=coder,
            message="Write a Python function that computes Fibonacci numbers.",
            max_turns=10
        )

response.process()

logger.info("Final output:\n%s", response.summary)
```

---
### Orchestrating Multiple Agents

AG2 enables sophisticated multi-agent collaboration through flexible orchestration patterns, allowing you to create dynamic systems where specialized agents work together to solve complex problems.

Here’s how to build a team of **teacher**, **lesson planner**, and **reviewer** agents working together to design a lesson plan:

```python
import logging
from autogen import ConversableAgent, LLMConfig
from autogen.agentchat import run_group_chat
from autogen.agentchat.group.patterns import AutoPattern

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm_config = LLMConfig.from_json(path="OAI_CONFIG_LIST")

# Define lesson planner and reviewer
planner_message = "You are a classroom lesson planner. Given a topic, write a lesson plan for a fourth grade class."
reviewer_message = "You are a classroom lesson reviewer. Compare the plan to the curriculum and suggest up to 3 improvements."

lesson_planner = ConversableAgent(
    name="planner_agent",
    system_message=planner_message,
    description="Creates or revises lesson plans.",
    llm_config=llm_config,
)

lesson_reviewer = ConversableAgent(
    name="reviewer_agent",
    system_message=reviewer_message,
    description="Provides one round of feedback to lesson plans.",
    llm_config=llm_config,
)

teacher_message = "You are a classroom teacher. You decide topics and collaborate with planner and reviewer to finalize lesson plans. When satisfied, output DONE!"

teacher = ConversableAgent(
    name="teacher_agent",
    system_message=teacher_message,
    is_termination_msg=lambda x: "DONE!" in (x.get("content", "") or "").upper(),
    llm_config=llm_config,
)

auto_selection = AutoPattern(
    agents=[teacher, lesson_planner, lesson_reviewer],
    initial_agent=lesson_planner,
    group_manager_args={"name": "group_manager", "llm_config": llm_config},
)

response = run_group_chat(
    pattern=auto_selection,
    messages="Let's introduce our kids to the solar system.",
    max_rounds=20,
)

response.process()

logger.info("Final output:\n%s", response.summary)
```

---

### Human in the Loop

Human oversight is often essential for validating or guiding AI outputs.
AG2 provides the `UserProxyAgent` for seamless integration of human feedback.

Here we extend the **teacher–planner–reviewer** example by introducing a **human agent** who validates the final lesson:

```python
import logging
from autogen import ConversableAgent, LLMConfig, UserProxyAgent
from autogen.agentchat import run_group_chat
from autogen.agentchat.group.patterns import AutoPattern

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm_config = LLMConfig.from_json(path="OAI_CONFIG_LIST")

# Same agents as before, but now the human validator will pass to the planner who will check for "APPROVED" and terminate
planner_message = "You are a classroom lesson planner. Given a topic, write a lesson plan for a fourth grade class."
reviewer_message = "You are a classroom lesson reviewer. Compare the plan to the curriculum and suggest up to 3 improvements."
teacher_message = "You are an experienced classroom teacher. You don't prepare plans, you provide simple guidance to the planner to prepare a lesson plan on the key topic."

lesson_planner = ConversableAgent(
    name="planner_agent",
    system_message=planner_message,
    description="Creates or revises lesson plans before having them reviewed.",
    is_termination_msg=lambda x: "APPROVED" in (x.get("content", "") or "").upper(),
    human_input_mode="NEVER",
    llm_config=llm_config,
)

lesson_reviewer = ConversableAgent(
    name="reviewer_agent",
    system_message=reviewer_message,
    description="Provides one round of feedback to lesson plans back to the lesson planner before requiring the human validator.",
    llm_config=llm_config,
)

teacher = ConversableAgent(
    name="teacher_agent",
    system_message=teacher_message,
    description="Provides guidance on the topic and content, if required.",
    llm_config=llm_config,
)

human_validator = UserProxyAgent(
    name="human_validator",
    system_message="You are a human educator who provides final approval for lesson plans.",
    description="Evaluates the proposed lesson plan and either approves it or requests revisions, before returning to the planner.",
)

auto_selection = AutoPattern(
    agents=[teacher, lesson_planner, lesson_reviewer],
    initial_agent=teacher,
    user_agent=human_validator,
    group_manager_args={"name": "group_manager", "llm_config": llm_config},
)

response = run_group_chat(
    pattern=auto_selection,
    messages="Let's introduce our kids to the solar system.",
    max_rounds=20,
)

response.process()

logger.info("Final output:\n%s", response.summary)
```

---

### Tools

Agents gain significant utility through **tools**, which extend their capabilities with external data, APIs, or functions.

```python
import logging
from datetime import datetime
from typing import Annotated
from autogen import ConversableAgent, register_function, LLMConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm_config = LLMConfig.from_json(path="OAI_CONFIG_LIST")

# Tool: returns weekday for a given date
def get_weekday(date_string: Annotated[str, "Format: YYYY-MM-DD"]) -> str:
    date = datetime.strptime(date_string, "%Y-%m-%d")
    return date.strftime("%A")

date_agent = ConversableAgent(
    name="date_agent",
    system_message="You find the day of the week for a given date.",
    llm_config=llm_config,
)

executor_agent = ConversableAgent(
    name="executor_agent",
    human_input_mode="NEVER",
    llm_config=llm_config,
)

# Register tool
register_function(
    get_weekday,
    caller=date_agent,
    executor=executor_agent,
    description="Get the day of the week for a given date",
)

# Use tool in chat
chat_result = executor_agent.initiate_chat(
    recipient=date_agent,
    message="I was born on 1995-03-25, what day was it?",
    max_turns=2,
)

logger.info("Final output:\n%s", chat_result.chat_history[-1]["content"])
```

### Advanced agentic design patterns

Clippy Kernel supports advanced concepts to help you build sophisticated AI agent workflows:

- [Persistent Memory & Context](website/docs/advanced/memory-engine.md) - Agent memory that persists across sessions
- [Self-Improving Agents](website/docs/advanced/self-improvement.md) - Agents that learn and adapt over time
- [Enterprise Security](website/docs/advanced/security.md) - Azure integration and secure deployment
- [Real-time Collaboration](website/docs/advanced/realtime.md) - WebSocket-based agent communication
- [Performance Optimization](website/docs/advanced/performance.md) - Scaling multi-agent systems
- [Research Methodologies](website/docs/research/) - Cutting-edge AI research patterns

## 📦 Deployment & Production

### Docker Deployment
```bash
# Build production image
docker build -t clippy-kernel:latest .

# Run with all features
docker run -p 8080:8080 -e OPENAI_API_KEY=$OPENAI_API_KEY clippy-kernel:latest
```

### Kubernetes Deployment
```yaml
# Deploy to Kubernetes cluster
kubectl apply -f deployment/k8s/
```

### Cloud Deployment
```bash
# Azure Container Instances
az container create --resource-group myResourceGroup \
  --name clippy-kernel --image clippy-kernel:latest

# AWS ECS
aws ecs create-service --cluster production \
  --service-name clippy-kernel --task-definition clippy-kernel:1
```

## 🧪 Testing & Development

### Run Core Tests
```bash
# Run tests without LLM dependencies
bash scripts/test-core-skip-llm.sh

# Run full test suite
bash scripts/test-skip-llm.sh

# Run specific test categories
pytest test/mcp/ -v
pytest test/agentchat/ -v
```

### Development Environment
```bash
# Set up development environment
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev,windows-clippy-mcp]"

# Install pre-commit hooks
pre-commit install

# Run linting and formatting
bash scripts/lint.sh
```

### Performance Testing
```bash
# Run performance benchmarks
python scripts/benchmark_agents.py

# Load testing for production
python scripts/load_test.py --concurrent=10 --duration=300
```

## 📚 Documentation

Comprehensive documentation is available in the `website/docs/` directory:

- **[Getting Started Guide](website/docs/getting-started/)** - Quick setup and first steps
- **[Agent Development](website/docs/agent-development/)** - Building sophisticated agents
- **[MCP Integration](website/docs/mcp-integration/)** - Model Control Protocol usage
- **[Enterprise Features](website/docs/enterprise/)** - Security, scalability, deployment
- **[API Reference](website/docs/api/)** - Complete API documentation
- **[Research Papers](website/docs/research/)** - Academic research and findings

### Build Documentation
```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build and serve locally
./scripts/docs_build_mkdocs.sh
./scripts/docs_serve_mkdocs.sh
```

## 🎯 Roadmap & Research Areas

### Current Research Focus
- **Multi-Agent Reasoning**: Advanced reasoning patterns across agent teams
- **Self-Supervised Learning**: Agents that improve without human intervention  
- **Emergent Behavior**: Studying complex behaviors in large agent systems
- **Ethical AI**: Ensuring responsible AI behavior in autonomous systems
- **Performance Optimization**: Scaling to thousands of concurrent agents

### Upcoming Features
- **Q1 2025**: Advanced memory architectures and knowledge graphs
- **Q2 2025**: Multi-modal agent capabilities (vision, audio, video)
- **Q3 2025**: Blockchain integration for decentralized agent networks
- **Q4 2025**: Quantum computing readiness and hybrid classical-quantum agents

### Research Collaboration
We actively collaborate with academic institutions and research organizations. 
Interested in research partnerships? Contact us at research@clippy-kernel.ai

We welcome contributions from researchers, developers, and organizations interested in advancing multi-agent AI systems!

### Contributing Guidelines

1. **Fork and Clone**: Fork the repository and clone your fork locally
2. **Development Setup**: Follow the development environment setup above
3. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
4. **Make Changes**: Implement your feature with comprehensive tests
5. **Run Tests**: Ensure all tests pass with `bash scripts/test-core-skip-llm.sh`
6. **Submit PR**: Create a pull request with detailed description

### Areas for Contribution

- **🤖 Agent Architectures**: New agent types and interaction patterns
- **🔧 Tool Integration**: Additional MCP tools and service integrations  
- **📊 Research**: Novel multi-agent coordination algorithms
- **🎯 Applications**: Real-world use cases and domain-specific agents
- **📚 Documentation**: Examples, tutorials, and API documentation
- **🧪 Testing**: Test coverage, performance benchmarks, edge cases

### Code Quality Standards

```bash
# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Run quality checks
bash scripts/lint.sh
bash scripts/test-core-skip-llm.sh
```

### Research Contributions

We especially welcome research contributions in:
- Multi-agent learning and adaptation
- Emergent behavior in agent systems  
- Ethical AI and agent alignment
- Performance optimization at scale
- Novel application domains

## 📄 License

Clippy Kernel is licensed under the [Apache License, Version 2.0 (Apache-2.0)](./LICENSE).

This project is an advanced R&D fork of [AG2](https://github.com/ag2ai/ag2) (formerly AutoGen) and contains code under two licenses:

- **Original AG2/AutoGen code**: Licensed under the Apache License, Version 2.0. See the [LICENSE](./LICENSE) file for details.
- **Clippy Kernel enhancements**: All new features, modifications, and additions are licensed under the Apache License, Version 2.0.

### Acknowledgments

- **AG2 Community**: For the excellent foundation and ongoing development
- **Microsoft Research**: For the original AutoGen framework
- **Contributors**: All researchers and developers contributing to multi-agent AI

### Citation

If you use Clippy Kernel in your research, please cite:

```bibtex
@software{ClippyKernel_2024,
  author = {Clippy Kernel Development Team},
  title = {Clippy Kernel: Advanced R\&D Fork of AG2 for Multi-Agent AI Research},
  year = {2024},
  url = {https://github.com/dayour/Clippy-Kernel},
  note = {Advanced multi-agent AI platform with enterprise MCP integration}
}

@software{AG2_2024,
  author = {Chi Wang and Qingyun Wu and the AG2 Community},
  title = {AG2: Open-Source AgentOS for AI Agents},
  year = {2024},
  url = {https://github.com/ag2ai/ag2},
  note = {Available at https://docs.ag2.ai/}
}
```

---

<p align="center">
  <strong>📎 Clippy Kernel</strong> - Pushing the boundaries of multi-agent AI research and development
  <br>
  <br>
  <a href="https://github.com/dayour/Clippy-Kernel/issues">Report Bug</a> •
  <a href="https://github.com/dayour/Clippy-Kernel/discussions">Discussions</a> •
  <a href="mailto:research@clippy-kernel.ai">Research Collaboration</a>
</p>
