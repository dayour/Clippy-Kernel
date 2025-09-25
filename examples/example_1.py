"""
Example 1: The First AG2 Agent

This is example #1 - the most basic AG2 agent interaction.
It demonstrates the simplest form of agent-to-agent communication.
"""

from autogen import ConversableAgent


def example_1():
    """Example 1: Basic agent-to-agent communication."""
    print("📚 Example 1: Basic Agent Communication")
    print("=" * 50)
    
    # Agent 1: The helper
    agent_1 = ConversableAgent(
        name="helper",
        system_message="You are a helpful assistant. Respond to messages politely.",
        human_input_mode="NEVER",
        llm_config=False,  # No LLM for this basic example
    )
    
    # Agent 2: The user
    agent_2 = ConversableAgent(
        name="user",
        system_message="You are asking for help.",
        human_input_mode="NEVER", 
        llm_config=False,  # No LLM for this basic example
    )
    
    print("✅ Created two agents:")
    print(f"   1. {agent_1.name} - The helper")
    print(f"   2. {agent_2.name} - The user")
    
    # Demonstrate basic properties
    print(f"\n📝 Agent 1 system message: {agent_1.system_message}")
    print(f"📝 Agent 2 system message: {agent_2.system_message}")
    
    print("\n🎉 Example 1 completed successfully!")
    print("This demonstrates the basic structure of AG2 agents.")


if __name__ == "__main__":
    example_1()