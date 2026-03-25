#!/usr/bin/env python3
"""
Clippy SWE Agent - Basic Usage Example

This example demonstrates how to use the Clippy SWE Agent for autonomous
software engineering tasks.
"""

import logging

from autogen.cli import ClippySWEAgent, ClippySWEConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_task():
    """Example: Execute a basic coding task."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Coding Task")
    print("=" * 70 + "\n")

    # Configure the agent
    config = ClippySWEConfig(
        observer_mode=True,  # Show what the agent is doing
        autonomous_mode=True,  # Run autonomously
        max_iterations=20,
    )

    # Create the agent
    agent = ClippySWEAgent(config=config)

    # Execute a coding task
    task_description = """
    Create a simple Python REST API using Flask with the following features:
    1. User registration endpoint (POST /api/register)
    2. User login endpoint (POST /api/login) 
    3. Protected endpoint (GET /api/profile) that requires authentication
    4. Use JWT for authentication
    5. Include basic input validation
    
    Provide the complete code with proper error handling.
    """

    result = agent.execute_task(task_description, task_type="coding")

    print(f"\n✅ Task Status: {result['status']}")
    print(f"📝 Result: {result.get('result', 'No result')}")


def example_research_task():
    """Example: Execute a research task."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Research Task")
    print("=" * 70 + "\n")

    config = ClippySWEConfig(observer_mode=True)
    agent = ClippySWEAgent(config=config)

    task_description = """
    Research and compare the following Python web frameworks:
    - Flask
    - FastAPI
    - Django
    
    Provide:
    1. Key features of each framework
    2. Performance characteristics
    3. Use case recommendations
    4. Learning curve assessment
    5. When to choose which framework
    
    Focus on practical, actionable insights.
    """

    result = agent.execute_task(task_description, task_type="research")

    print(f"\n✅ Task Status: {result['status']}")


def example_system_task():
    """Example: Execute a system administration task."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: System Task")
    print("=" * 70 + "\n")

    config = ClippySWEConfig(observer_mode=True, enable_windows_automation=True)
    agent = ClippySWEAgent(config=config)

    task_description = """
    Analyze the current system's resource usage and provide:
    1. CPU usage patterns
    2. Memory consumption
    3. Disk space availability
    4. Running processes consuming most resources
    5. Recommendations for optimization
    
    Present the information in a clear, actionable format.
    """

    result = agent.execute_task(task_description, task_type="system")

    print(f"\n✅ Task Status: {result['status']}")


def example_windows_task():
    """Example: Execute a Windows-specific task (only on Windows)."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Windows Task (requires Windows)")
    print("=" * 70 + "\n")

    import platform

    if platform.system() != "Windows":
        print("⚠️  Skipping Windows example (not running on Windows)")
        return

    config = ClippySWEConfig(
        observer_mode=True, enable_windows_automation=True, enable_app_interaction=True
    )
    agent = ClippySWEAgent(config=config)

    task_description = """
    Perform the following Windows tasks:
    1. Check Windows version and build number
    2. List all running services
    3. Identify services consuming most memory
    4. Check Windows Update status
    5. Provide recommendations for system optimization
    """

    result = agent.execute_windows_task(task_description)

    print(f"\n✅ Task Status: {result['status']}")


def example_view_history():
    """Example: View task execution history."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: View Task History")
    print("=" * 70 + "\n")

    config = ClippySWEConfig()
    agent = ClippySWEAgent(config=config)

    # Get recent tasks
    recent_tasks = agent.list_recent_tasks(limit=5)

    print(f"📜 Found {len(recent_tasks)} recent tasks:\n")

    for task in recent_tasks:
        status_emoji = "✅" if task["status"] == "completed" else "❌"
        print(f"{status_emoji} Task #{task['id']} [{task['type']}]: {task['description'][:60]}...")
        print(f"   Status: {task['status']}")
        print(f"   Time: {task['timestamp']}\n")


def example_system_status():
    """Example: Check agent system status."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: System Status")
    print("=" * 70 + "\n")

    config = ClippySWEConfig()
    agent = ClippySWEAgent(config=config)

    status = agent.get_system_status()

    print("🤖 Agent Status:")
    print(f"   Platform: {status['platform']['system']} {status['platform']['release']}")
    print(f"   Python: {status['python']['version']}")
    print(f"   Agent Initialized: {status['agent']['initialized']}")
    print(f"   LLM Configured: {status['agent']['llm_configured']}")
    print(f"   Agent Count: {status['agent']['agent_count']}")

    if "resources" in status:
        print("\n💻 System Resources:")
        print(f"   CPU: {status['resources'].get('cpu_percent', 0):.1f}%")
        print(f"   Memory: {status['resources'].get('memory', {}).get('percent', 0):.1f}%")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("CLIPPY SWE AGENT - USAGE EXAMPLES")
    print("=" * 70)

    print("\n⚠️  Note: These examples require an OAI_CONFIG_LIST file with API keys")
    print("Create one with your OpenAI API key before running.\n")

    try:
        # Run examples
        # example_basic_task()  # Uncomment to run
        # example_research_task()  # Uncomment to run
        # example_system_task()  # Uncomment to run
        # example_windows_task()  # Uncomment to run
        example_view_history()
        example_system_status()

        print("\n" + "=" * 70)
        print("✅ EXAMPLES COMPLETED")
        print("=" * 70)
        print("\nTo run tasks, uncomment the example functions in main()")
        print("and ensure you have OAI_CONFIG_LIST configured.\n")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease create an OAI_CONFIG_LIST file with your API keys.")
        print("See OAI_CONFIG_LIST_sample for an example.\n")
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
