#!/usr/bin/env python3
"""
Clippy Kernel Agent Development Team - Basic Example

This example demonstrates how to use the Agent Development Team to collaboratively
implement a new feature using agile methodologies.
"""

import logging
from pathlib import Path
from autogen import LLMConfig
from autogen.agentchat import AgentDevTeam, create_agent_dev_team

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run a basic Agent Development Team example."""
    
    # Load LLM configuration
    # Make sure you have an OAI_CONFIG_LIST file with your API keys
    try:
        llm_config = LLMConfig.from_json(path="OAI_CONFIG_LIST")
    except FileNotFoundError:
        print("❌ Please create an OAI_CONFIG_LIST file with your API keys")
        return
    
    # Create the Agent Development Team
    print("🤖 Creating Agent Development Team...")
    dev_team = create_agent_dev_team(
        llm_config=llm_config,
        project_path=Path("./sample_project"),
        sprint_duration_days=7,  # 1-week sprint
        capacity_points=30,
        focus_areas=["functionality", "quality", "performance", "user_experience"]
    )
    
    print(f"✅ Team created with {len(dev_team.agents)} agents")
    
    # Feature request for the team to implement
    feature_request = """
    Implement a real-time chat system with the following requirements:
    
    1. **Core Features:**
       - Real-time messaging between users
       - Message history persistence
       - User authentication and authorization
       - Online/offline status indicators
       
    2. **Technical Requirements:**
       - WebSocket-based communication
       - RESTful API for message management
       - Database for message persistence
       - Scalable architecture for multiple concurrent users
       
    3. **Quality Requirements:**
       - Comprehensive test coverage (>90%)
       - Security best practices
       - Performance optimization for high load
       - Mobile-responsive UI
       
    4. **Deployment Requirements:**
       - Docker containerization
       - CI/CD pipeline
       - Monitoring and logging
       - Documentation for setup and usage
    """
    
    print("\n🚀 Starting development sprint...")
    print("=" * 60)
    
    # Run the development sprint
    try:
        sprint_results = dev_team.run_development_sprint(
            feature_request=feature_request,
            max_iterations=20  # Allow up to 20 rounds of collaboration
        )
        
        print("\n" + "=" * 60)
        print("📊 SPRINT RESULTS")
        print("=" * 60)
        print(f"Status: {sprint_results['status']}")
        print(f"Iterations Used: {sprint_results['iterations_used']}")
        print(f"Timestamp: {sprint_results['timestamp']}")
        
        if sprint_results['status'] == 'completed':
            print("\n✅ Sprint completed successfully!")
            print("\n📋 Sprint Summary:")
            print(sprint_results['sprint_execution'])
        else:
            print(f"\n❌ Sprint failed: {sprint_results.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Sprint execution failed: {str(e)}")
        return
    
    # Run a code review session
    print("\n" + "=" * 60)
    print("🔍 CONDUCTING CODE REVIEW")
    print("=" * 60)
    
    try:
        review_results = dev_team.run_code_review(
            code_path=Path("./sample_project/src"),
            review_criteria=[
                "Code quality and maintainability",
                "Security best practices",
                "Performance optimization",
                "Test coverage and quality",
                "Documentation completeness",
                "Architecture alignment"
            ]
        )
        
        print("✅ Code review completed!")
        print("\n📝 Review Summary:")
        print(review_results['review_results'])
        
    except Exception as e:
        logger.error(f"Code review failed: {str(e)}")
    
    # Run sprint retrospective
    print("\n" + "=" * 60)
    print("🔄 SPRINT RETROSPECTIVE")
    print("=" * 60)
    
    try:
        retrospective_results = dev_team.run_retrospective()
        
        print("✅ Retrospective completed!")
        print("\n🎯 Retrospective Summary:")
        print(retrospective_results['retrospective_discussion'])
        
    except Exception as e:
        logger.error(f"Retrospective failed: {str(e)}")
    
    # Export sprint history
    print("\n" + "=" * 60)
    print("📁 EXPORTING SPRINT HISTORY")
    print("=" * 60)
    
    try:
        export_path = dev_team.export_sprint_history()
        print(f"✅ Sprint history exported to: {export_path}")
        
        # Display team status
        team_status = dev_team.get_team_status()
        print("\n👥 Team Status:")
        for role, agent_name in team_status['team_composition'].items():
            print(f"  - {role.replace('_', ' ').title()}: {agent_name}")
            
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")


if __name__ == "__main__":
    main()