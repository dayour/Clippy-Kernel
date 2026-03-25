#!/usr/bin/env python3
"""
Clippy SWE Agent - Code Structure Validation

This script validates the code structure without requiring dependencies.
"""

import ast
import sys
from pathlib import Path


def _normalize_heading(value: str) -> str:
    """Normalize a markdown heading for case-insensitive comparison."""
    return value.strip().strip("`").lower()


def collect_markdown_headings(file_path: Path) -> list[str]:
    """Collect markdown headings from a file."""
    headings: list[str] = []
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip()
                if heading:
                    headings.append(heading)
    return headings


def check_required_markdown_sections(file_path: Path, required_sections: list[str]) -> tuple[bool, list[str]]:
    """Check whether a markdown file contains the required headings."""
    headings = collect_markdown_headings(file_path)
    normalized_headings = {_normalize_heading(heading) for heading in headings}
    missing = [section for section in required_sections if _normalize_heading(section) not in normalized_headings]
    return not missing, missing


def check_required_text(file_path: Path, required_snippets: list[str]) -> tuple[bool, list[str]]:
    """Check whether a file contains required text snippets."""
    content = file_path.read_text(encoding="utf-8")
    missing = [snippet for snippet in required_snippets if snippet not in content]
    return not missing, missing


def check_forbidden_text(file_path: Path, forbidden_snippets: list[str]) -> tuple[bool, list[str]]:
    """Check whether a file avoids forbidden text snippets."""
    content = file_path.read_text(encoding="utf-8")
    present = [snippet for snippet in forbidden_snippets if snippet in content]
    return not present, present


def validate_python_file(file_path: Path) -> tuple[bool, str]:
    """
    Validate that a Python file has valid syntax.

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            code = f.read()

        ast.parse(code)
        return True, "Valid Python syntax"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def check_required_classes(file_path: Path, required_classes: list[str]) -> tuple[bool, list[str]]:
    """
    Check if required classes are defined in the file.

    Returns:
        Tuple of (all_found, found_classes)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            code = f.read()

        tree = ast.parse(code)

        defined_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                defined_classes.append(node.name)

        all_found = all(cls in defined_classes for cls in required_classes)
        return all_found, defined_classes
    except Exception:
        return False, []


def check_required_functions(file_path: Path, required_functions: list[str]) -> tuple[bool, list[str]]:
    """
    Check if required functions are defined in the file.

    Returns:
        Tuple of (all_found, found_functions)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            code = f.read()

        tree = ast.parse(code)

        defined_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined_functions.append(node.name)

        all_found = all(func in defined_functions for func in required_functions)
        return all_found, defined_functions
    except Exception:
        return False, []


def main():
    """Run validation checks."""
    print("=" * 70)
    print("CLIPPY SWE AGENT - CODE STRUCTURE VALIDATION")
    print("=" * 70)

    cwd = Path.cwd()
    all_valid = True

    # Validate clippy_swe_agent.py
    print("\nValidating autogen/cli/clippy_swe_agent.py...")
    agent_file = cwd / "autogen/cli/clippy_swe_agent.py"

    valid, msg = validate_python_file(agent_file)
    if valid:
        print(f"   OK: {msg}")

        # Check required classes
        required_classes = ["ClippySWEConfig", "TaskHistory", "ClippySWEAgent"]
        classes_found, found_classes = check_required_classes(agent_file, required_classes)

        if classes_found:
            print(f"   OK: All required classes present: {', '.join(required_classes)}")
        else:
            print(f"   ERROR: Missing classes. Found: {', '.join(found_classes)}")
            all_valid = False

        # Check key methods
        required_methods = ["execute_task", "execute_windows_task", "get_system_status"]
        methods_found, found_methods = check_required_functions(agent_file, required_methods)

        if methods_found:
            print("   OK: All required methods present")
        else:
            print("   ERROR: Missing methods")
            all_valid = False
    else:
        print(f"   ERROR: {msg}")
        all_valid = False

    # Validate clippy_swe_cli.py
    print("\nValidating autogen/cli/clippy_swe_cli.py...")
    cli_file = cwd / "autogen/cli/clippy_swe_cli.py"

    valid, msg = validate_python_file(cli_file)
    if valid:
        print(f"   OK: {msg}")

        # Check required command functions
        required_commands = ["task", "windows", "status", "history", "init", "version", "main"]
        commands_found, found_funcs = check_required_functions(cli_file, required_commands)

        if commands_found:
            print(f"   OK: All required CLI commands present: {', '.join(required_commands)}")
        else:
            print(f"   ERROR: Missing commands. Found: {', '.join([f for f in found_funcs if f in required_commands])}")
            all_valid = False
    else:
        print(f"   ERROR: {msg}")
        all_valid = False

    # Validate __init__.py
    print("\nValidating autogen/cli/__init__.py...")
    init_file = cwd / "autogen/cli/__init__.py"

    valid, msg = validate_python_file(init_file)
    if valid:
        print(f"   OK: {msg}")

        # Check it has main function
        funcs_found, found_funcs = check_required_functions(init_file, ["main"])
        if funcs_found:
            print("   OK: Main entry point defined")
        else:
            print("   ERROR: Missing main entry point")
            all_valid = False
    else:
        print(f"   ERROR: {msg}")
        all_valid = False

    # Validate example file
    print("\nValidating examples/clippy_swe_agent_example.py...")
    example_file = cwd / "examples/clippy_swe_agent_example.py"

    valid, msg = validate_python_file(example_file)
    if valid:
        print(f"   OK: {msg}")
    else:
        print(f"   ERROR: {msg}")
        all_valid = False

    # Check documentation
    docs_to_validate = {
        "CLIPPY_SWE_AGENT_GUIDE.md": [
            "What Clippy SWE is",
            "Installation",
            "Configuration",
            "Core commands",
            "Known limitations",
            "Troubleshooting",
            "Related files",
        ],
        "CLIPPY_KERNEL_DEVELOPER_GUIDE.md": [
            "Purpose",
            "Canonical documentation set",
            "Repository orientation",
            "Testing and verification guidance",
            "Maintaining this guide",
        ],
        "CLIPPY_SWE_EVALS.md": [
            "Purpose and scope",
            "Validation layers",
            "Fast local smoke workflow",
            "Evidence checklist",
            "Known gaps and future work",
        ],
    }

    doc_text_rules = {
        "README.md": {
            "required": [
                'pip install -e ".[openai,mcp-proxy-gen]"',
                "Most commands do not read .clippy_swe_config.json automatically today.",
            ],
            "forbidden": [
                "Inspect status and resolved paths",
            ],
        },
        "CLIPPY_SWE_AGENT_GUIDE.md": {
            "required": [
                "most commands still construct `ClippySWEConfig()` directly and do not automatically consume `./.clippy_swe_config.json`",
                "- `task` and `interactive` only use it when you pass `--config`",
            ],
            "forbidden": [],
        },
        "CLIPPY_SWE_EVALS.md": {
            "required": [
                'python -m pip install -e ".[openai,mcp-proxy-gen,copilot-sdk,windows-clippy-mcp]"',
                "Do not rely on `clippy-swe status` as proof here.",
                "As with WorkIQ, do not use `clippy-swe status` as the main evidence that the workspace config was applied.",
            ],
            "forbidden": [
                "UnicodeDecodeError",
                "$env:PYTHONUTF8",
                "- whether `status` reported WorkIQ as enabled",
                "- whether `status` reported Microsoft 365 Copilot support as enabled",
            ],
        },
        "README_WINDOWS_CLIPPY_MCP.md": {
            "required": [
                "It is an operational setup note, not a claim that the repository provides a turnkey Windows automation product.",
                'pip install -e ".[mcp-proxy-gen,windows-clippy-mcp,mcp,dev]"',
                "## Operational notes",
            ],
            "forbidden": [
                "enterprise-grade",
                "experience the future of AI-assisted development",
            ],
        },
    }

    for doc_name, required_sections in docs_to_validate.items():
        print(f"\nValidating {doc_name}...")
        doc_file = cwd / doc_name

        if not doc_file.exists():
            print("   ERROR: Documentation file not found")
            all_valid = False
            continue

        sections_found, missing_sections = check_required_markdown_sections(doc_file, required_sections)
        if sections_found:
            print("   OK: Required documentation sections present")
        else:
            print(f"   ERROR: Missing documentation sections: {', '.join(missing_sections)}")
            all_valid = False

    for doc_name, rules in doc_text_rules.items():
        print(f"\nChecking wording invariants in {doc_name}...")
        doc_file = cwd / doc_name

        if not doc_file.exists():
            print("   ERROR: Documentation file not found")
            all_valid = False
            continue

        text_found, missing_snippets = check_required_text(doc_file, rules["required"])
        if text_found:
            print("   OK: Required wording present")
        else:
            print(f"   ERROR: Missing required wording: {', '.join(missing_snippets)}")
            all_valid = False

        text_clean, forbidden_snippets = check_forbidden_text(doc_file, rules["forbidden"])
        if text_clean:
            print("   OK: Forbidden stale wording absent")
        else:
            print(f"   ERROR: Found forbidden wording: {', '.join(forbidden_snippets)}")
            all_valid = False

    # Check pyproject.toml entry point
    print("\nChecking pyproject.toml entry point...")
    pyproject = cwd / "pyproject.toml"

    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        if 'clippy-swe = "autogen.cli:main"' in content:
            print("   OK: CLI entry point configured in pyproject.toml")
        else:
            print("   ERROR: CLI entry point not configured")
            all_valid = False
    else:
        print("   ERROR: pyproject.toml not found")
        all_valid = False

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    if all_valid:
        print("\nAll validation checks passed.")
        print("\nNotes:")
        print("   - Code structure is valid")
        print("   - All required classes and methods are present")
        print("   - CLI commands are properly defined")
        print("   - Canonical documentation set is structurally complete")
        print("   - Entry point is configured")
        print("\nWARNING: To test functionality, install dependencies:")
        print("   pip install -e '.[openai,mcp-proxy-gen]'")
        return 0
    else:
        print("\nSome validation checks failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
