#!/usr/bin/env python3
"""
Clippy SWE Agent - Code Structure Validation

This script validates the code structure without requiring dependencies.
"""

import ast
import sys
from pathlib import Path


def validate_python_file(file_path: Path) -> tuple[bool, str]:
    """
    Validate that a Python file has valid syntax.

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        with open(file_path) as f:
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
        with open(file_path) as f:
            code = f.read()

        tree = ast.parse(code)

        defined_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                defined_classes.append(node.name)

        all_found = all(cls in defined_classes for cls in required_classes)
        return all_found, defined_classes
    except Exception as e:
        return False, []


def check_required_functions(file_path: Path, required_functions: list[str]) -> tuple[bool, list[str]]:
    """
    Check if required functions are defined in the file.

    Returns:
        Tuple of (all_found, found_functions)
    """
    try:
        with open(file_path) as f:
            code = f.read()

        tree = ast.parse(code)

        defined_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined_functions.append(node.name)

        all_found = all(func in defined_functions for func in required_functions)
        return all_found, defined_functions
    except Exception as e:
        return False, []


def main():
    """Run validation checks."""
    print("=" * 70)
    print("CLIPPY SWE AGENT - CODE STRUCTURE VALIDATION")
    print("=" * 70)

    cwd = Path.cwd()
    all_valid = True

    # Validate clippy_swe_agent.py
    print("\n📄 Validating autogen/cli/clippy_swe_agent.py...")
    agent_file = cwd / "autogen/cli/clippy_swe_agent.py"

    valid, msg = validate_python_file(agent_file)
    if valid:
        print(f"   ✅ {msg}")

        # Check required classes
        required_classes = ["ClippySWEConfig", "TaskHistory", "ClippySWEAgent"]
        classes_found, found_classes = check_required_classes(agent_file, required_classes)

        if classes_found:
            print(f"   ✅ All required classes present: {', '.join(required_classes)}")
        else:
            print(f"   ❌ Missing classes. Found: {', '.join(found_classes)}")
            all_valid = False

        # Check key methods
        required_methods = ["execute_task", "execute_windows_task", "get_system_status"]
        methods_found, found_methods = check_required_functions(agent_file, required_methods)

        if methods_found:
            print(f"   ✅ All required methods present")
        else:
            print(f"   ❌ Missing methods")
            all_valid = False
    else:
        print(f"   ❌ {msg}")
        all_valid = False

    # Validate clippy_swe_cli.py
    print("\n📄 Validating autogen/cli/clippy_swe_cli.py...")
    cli_file = cwd / "autogen/cli/clippy_swe_cli.py"

    valid, msg = validate_python_file(cli_file)
    if valid:
        print(f"   ✅ {msg}")

        # Check required command functions
        required_commands = ["task", "windows", "status", "history", "init", "version", "main"]
        commands_found, found_funcs = check_required_functions(cli_file, required_commands)

        if commands_found:
            print(f"   ✅ All required CLI commands present: {', '.join(required_commands)}")
        else:
            print(f"   ❌ Missing commands. Found: {', '.join([f for f in found_funcs if f in required_commands])}")
            all_valid = False
    else:
        print(f"   ❌ {msg}")
        all_valid = False

    # Validate __init__.py
    print("\n📄 Validating autogen/cli/__init__.py...")
    init_file = cwd / "autogen/cli/__init__.py"

    valid, msg = validate_python_file(init_file)
    if valid:
        print(f"   ✅ {msg}")

        # Check it has main function
        funcs_found, found_funcs = check_required_functions(init_file, ["main"])
        if funcs_found:
            print(f"   ✅ Main entry point defined")
        else:
            print(f"   ❌ Missing main entry point")
            all_valid = False
    else:
        print(f"   ❌ {msg}")
        all_valid = False

    # Validate example file
    print("\n📄 Validating examples/clippy_swe_agent_example.py...")
    example_file = cwd / "examples/clippy_swe_agent_example.py"

    valid, msg = validate_python_file(example_file)
    if valid:
        print(f"   ✅ {msg}")
    else:
        print(f"   ❌ {msg}")
        all_valid = False

    # Check documentation
    print("\n📄 Validating CLIPPY_SWE_AGENT_GUIDE.md...")
    doc_file = cwd / "CLIPPY_SWE_AGENT_GUIDE.md"

    if doc_file.exists():
        content = doc_file.read_text()
        required_sections = ["Overview", "Installation", "Usage", "Examples"]

        sections_found = all(section in content for section in required_sections)
        if sections_found:
            print(f"   ✅ All required sections present")
        else:
            print(f"   ❌ Missing documentation sections")
            all_valid = False
    else:
        print(f"   ❌ Documentation file not found")
        all_valid = False

    # Check pyproject.toml entry point
    print("\n📄 Checking pyproject.toml entry point...")
    pyproject = cwd / "pyproject.toml"

    if pyproject.exists():
        content = pyproject.read_text()
        if 'clippy-swe = "autogen.cli:main"' in content:
            print(f"   ✅ CLI entry point configured in pyproject.toml")
        else:
            print(f"   ❌ CLI entry point not configured")
            all_valid = False
    else:
        print(f"   ❌ pyproject.toml not found")
        all_valid = False

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    if all_valid:
        print("\n✅ All validation checks passed!")
        print("\n📝 Notes:")
        print("   - Code structure is valid")
        print("   - All required classes and methods are present")
        print("   - CLI commands are properly defined")
        print("   - Documentation is complete")
        print("   - Entry point is configured")
        print("\n⚠️  To test functionality, install dependencies:")
        print("   pip install -e '.[openai,mcp-proxy-gen]'")
        return 0
    else:
        print("\n❌ Some validation checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
