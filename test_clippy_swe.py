#!/usr/bin/env python3
"""
Test script for Clippy SWE Agent

This script tests the basic functionality of the Clippy SWE Agent without
requiring a full environment setup.
"""

import sys
from pathlib import Path

# Add the repo to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from autogen.cli import ClippySWEAgent, ClippySWEConfig

        print("✅ Core imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("\n⚠️  Note: This requires dependencies to be installed:")
        print("   pip install -e '.[openai,mcp-proxy-gen]'")
        return False


def test_config_creation():
    """Test configuration creation."""
    print("\nTesting configuration creation...")

    try:
        from autogen.cli import ClippySWEConfig

        config = ClippySWEConfig(
            autonomous_mode=True,
            observer_mode=False,
            max_iterations=20,
        )

        print(f"✅ Config created successfully")
        print(f"   - Autonomous mode: {config.autonomous_mode}")
        print(f"   - Observer mode: {config.observer_mode}")
        print(f"   - Max iterations: {config.max_iterations}")
        return True
    except Exception as e:
        print(f"❌ Config creation failed: {e}")
        return False


def test_agent_creation_without_llm():
    """Test agent creation without LLM (should work in limited mode)."""
    print("\nTesting agent creation (without LLM)...")

    try:
        from autogen.cli import ClippySWEAgent, ClippySWEConfig

        config = ClippySWEConfig(
            llm_config_path="nonexistent_config.json",  # Intentionally missing
            autonomous_mode=False,
        )

        agent = ClippySWEAgent(config=config)

        print("✅ Agent created successfully (limited mode)")
        print(f"   - Agents initialized: {len(agent.agents)}")
        print(f"   - Toolkit enabled: {agent.toolkit is not None}")
        return True
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False


def test_cli_module():
    """Test CLI module structure."""
    print("\nTesting CLI module structure...")

    try:
        import autogen.cli as cli

        expected_attrs = ["ClippySWEAgent", "ClippySWEConfig", "main"]

        for attr in expected_attrs:
            if hasattr(cli, attr):
                print(f"   ✅ {attr} found")
            else:
                print(f"   ❌ {attr} missing")
                return False

        print("✅ CLI module structure valid")
        return True
    except Exception as e:
        print(f"❌ CLI module check failed: {e}")
        return False


def test_file_structure():
    """Test that all required files exist."""
    print("\nTesting file structure...")

    # Get current working directory as repo root
    import os

    cwd = Path(os.getcwd())

    required_files = [
        "autogen/cli/__init__.py",
        "autogen/cli/clippy_swe_agent.py",
        "autogen/cli/clippy_swe_cli.py",
        "examples/clippy_swe_agent_example.py",
        "CLIPPY_SWE_AGENT_GUIDE.md",
    ]

    all_exist = True
    for file_path in required_files:
        full_path = cwd / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} missing (checked: {full_path})")
            all_exist = False

    if all_exist:
        print("✅ All required files present")
    return all_exist


def main():
    """Run all tests."""
    print("=" * 70)
    print("CLIPPY SWE AGENT - TEST SUITE")
    print("=" * 70)

    tests = [
        ("File Structure", test_file_structure),
        ("Module Imports", test_imports),
        ("CLI Module", test_cli_module),
        ("Config Creation", test_config_creation),
        ("Agent Creation", test_agent_creation_without_llm),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results[test_name] = False

    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    passed_count = sum(results.values())
    total_count = len(results)

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
