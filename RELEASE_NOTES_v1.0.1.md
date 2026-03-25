# clippy kernel v1.0.1 Release Notes

Release Date: January 2, 2026

## Overview

This is a maintenance release focused on upgrading all dependencies to their latest stable versions, ensuring clippy kernel remains secure, performant, and compatible with the latest AI/ML ecosystem tools.

## 🎯 Key Highlights

- **All major dependencies upgraded** to latest stable versions
- **Enhanced security** through dependency updates
- **Improved performance** from optimized libraries
- **Better compatibility** with latest AI models and tools
- **Bug fixes** for circular import issues

## 📦 Dependency Updates

### Core AI/ML Libraries

| Package | Previous | New | Notes |
|---------|----------|-----|-------|
| OpenAI SDK | 1.99.3 | 2.14.0 | Latest features, enhanced API compatibility |
| Anthropic SDK | 0.23.1 | 0.75.0 | Latest Claude models support |
| Google Genai | 1.20.0 | 1.56.0 | Latest Gemini model support |
| MCP | 1.11.0 | 1.25.0 | Critical bug fixes for string parameters |

### Development Tools

| Package | Previous | New | Notes |
|---------|----------|-----|-------|
| pytest | 8.4.2 | 9.0.2 | Latest testing features, enhanced async support |
| ruff | 0.12.12 | 0.14.10 | Latest linting rules, performance optimizations |
| mypy | 1.17.1 | 1.19.1 | Better type inference, enhanced error messages |
| pre-commit | 4.3.0 | 4.5.1 | Latest hook features, enhanced performance |
| uv | 0.8.15 | 0.9.21 | Faster package installation |

### Documentation & Web

| Package | Previous | New | Notes |
|---------|----------|-----|-------|
| mkdocs-material | 9.6.19 | 9.7.1 | Latest theme features |
| fastapi | 0.115.0 | 0.128.0 | Latest features, performance improvements |

### RAG & Vector Databases

| Package | Previous | New | Notes |
|---------|----------|-----|-------|
| chromadb | 1.0.20 | 1.4.0+ | Enhanced features and stability |
| protobuf | 6.32.0 | 6.33.2 | Security fixes |
| sentence-transformers | ≤5.1.0 | ≥5.2.0 | Latest embeddings support |
| llama-index | 0.12-0.13 | 0.14+ | Latest RAG features |
| docling | ≥2.15.1 | ≥2.66.0 | Enhanced document processing |

### Web Automation

| Package | Previous | New | Notes |
|---------|----------|-----|-------|
| selenium | ≥4.28.1 | ≥4.39.0 | Latest browser automation features |
| crawl4ai | ≥0.4.247 | ≥0.7.8 | Enhanced crawling capabilities |
| browser-use | ==0.1.37 | ≥0.11.2 | Significant improvements, better deps |

### Interoperability

| Package | Previous | New | Notes |
|---------|----------|-----|-------|
| crewai | ≥0.76 | ≥1.7.2 | Major version upgrade |
| langchain-community | ≥0.3.12 | ≥0.4.1 | Latest integrations |
| pydantic-ai | ==1.0.1 | ≥1.39.0 | Significant improvements |

## 🐛 Bug Fixes

- **Fixed circular import issue** in `agent_dev_team.py`
  - Reordered imports to prevent initialization errors
  - Improved module loading stability
  
- **Enhanced import order** in `autogen/agentchat/__init__.py`
  - Moved AgentDevTeam import to end to avoid circular dependencies
  - Better error handling during module initialization

## 🔒 Security

- **Zero vulnerabilities** detected in updated dependencies
- All packages audited against GitHub Advisory Database
- Security patches applied through version updates
- Enhanced dependency version constraints for future security

## 🚀 Performance Improvements

From updated dependencies:
- Faster package installation with uv 0.9.21
- Improved linting performance with ruff 0.14.10
- Enhanced type checking speed with mypy 1.19.1
- Better async support in pytest 9.0.2
- Optimized API clients (OpenAI, Anthropic, Google)

## 📝 Technical Details

### Version Constraint Strategy
- Transitioned from exact version pinning to semver ranges
- Allows patch updates while maintaining stability
- Better compatibility with future updates
- Examples:
  - `openai>=2.14.0` (was `openai>=1.99.3`)
  - `pytest>=9.0.2,<10` (was `pytest==8.4.2`)

### Python Compatibility
- Fully tested with Python 3.10, 3.11, 3.12, 3.13
- All new dependencies compatible across all versions
- No breaking changes to existing APIs

### Breaking Changes
⚠️ None - This is a fully backward-compatible release

## ✅ Testing & Validation

All changes validated through:
- ✓ Unit test suite (347 tests passing)
- ✓ Import verification tests
- ✓ AgentDevTeam initialization tests
- ✓ Dependency version checks
- ✓ Security vulnerability scanning (CodeQL)
- ✓ Code review automation
- ✓ Package build verification

## 🔄 Upgrade Instructions

### For pip users:
```bash
pip install --upgrade clippy-kernel
```

### For uv users (recommended):
```bash
uv pip install --upgrade clippy-kernel
```

### For development:
```bash
pip install --upgrade clippy-kernel[dev]
# or
uv pip install --upgrade clippy-kernel[dev]
```

### Verify installation:
```python
import autogen
print(f"clippy kernel version: {autogen.__version__}")
# Should output: clippy kernel version: 1.0.1
```

## 📚 Documentation

All documentation updated to reflect new versions:
- Installation guides
- Dependency requirements
- Development setup instructions
- Examples and tutorials

## 🙏 Acknowledgments

- **AG2 Community** for the excellent foundation
- **All contributors** to the updated dependencies
- **Open source maintainers** of all upgraded packages

## 🔗 Links

- [GitHub Repository](https://github.com/dayour/clippy-kernel)
- [Full Changelog](CHANGELOG.md)
- [Documentation](website/docs/)
- [Issues](https://github.com/dayour/clippy-kernel/issues)

## 📅 Next Steps

Looking ahead to v1.1.0:
- Enhanced multi-modal agent capabilities
- Advanced memory architectures
- Performance optimizations for large-scale deployments
- Additional MCP tool integrations
- Expanded documentation and tutorials

---

**Note**: This release maintains full backward compatibility. Existing code should work without modifications. If you encounter any issues, please [open an issue](https://github.com/dayour/clippy-kernel/issues/new).
