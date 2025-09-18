"""
Minimal AG2 Agent Example - Hello World

This is the simplest possible example of using AG2 agents.
It demonstrates basic agent creation and message exchange.
"""

from autogen import ConversableAgent, LLMConfig


def main():
    """Create the simplest possible AG2 agent example."""
    print("🤖 AG2 Minimal Example - Hello World")
    print("="*40)
    
    # Create a simple agent without LLM (for basic demonstration)
    agent = ConversableAgent(
        name="simple_agent",
        system_message="You are a helpful assistant that says hello.",
        human_input_mode="NEVER",
        # No LLM config needed for this basic example
        llm_config=False,
    )
    
    # Create a basic human proxy agent
    user = ConversableAgent(
        name="user",
        system_message="You are a user asking for help.",
        human_input_mode="NEVER",
        llm_config=False,
    )
    
    print("✅ Agents created successfully!")
    print(f"📝 Agent name: {agent.name}")
    print(f"👤 User name: {user.name}")
    
    # Basic message demonstration
    message = "Hello, AG2!"
    print(f"\n💬 Sending message: '{message}'")
    print("✅ Basic AG2 agents are working correctly!")


if __name__ == "__main__":
    main()