#!/usr/bin/env python3
"""
Clippy Kernel Self-Improving Agent Team Example

This example demonstrates how to create a team that continuously analyzes and improves
its own codebase using automated workflows and agile methodologies.
"""

import logging
from pathlib import Path
from autogen import LLMConfig
from autogen.agentchat import create_self_improving_team

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run a self-improving team example that analyzes and improves the current codebase."""
    
    # Load LLM configuration
    try:
        llm_config = LLMConfig.from_json(path="OAI_CONFIG_LIST")
    except FileNotFoundError:
        print("❌ Please create an OAI_CONFIG_LIST file with your API keys")
        return
    
    # Create a self-improving team focused on the current project
    print("🔄 Creating Self-Improving Agent Team...")
    improvement_team = create_self_improving_team(
        llm_config=llm_config,
        project_path=Path("."),  # Current project directory
        improvement_areas=[
            "code_quality",
            "performance", 
            "security",
            "maintainability",
            "test_coverage",
            "documentation",
            "architecture"
        ]
    )
    
    print(f"✅ Self-improving team created with {len(improvement_team.agents)} specialized agents")
    
    # Define the improvement sprint goal
    improvement_request = """
    Analyze the current Clippy Kernel codebase and implement high-impact improvements:
    
    **Analysis Areas:**
    1. **Code Quality**: Identify code smells, improve readability, refactor complex functions
    2. **Performance**: Find bottlenecks, optimize algorithms, improve memory usage
    3. **Security**: Review for vulnerabilities, implement security best practices
    4. **Architecture**: Evaluate system design, improve modularity and scalability
    5. **Testing**: Increase test coverage, improve test quality, add missing tests
    6. **Documentation**: Enhance code comments, update README files, create usage examples
    
    **Improvement Goals:**
    - Increase overall code quality score by 15%
    - Improve test coverage to >85%
    - Reduce technical debt by addressing critical issues
    - Enhance developer experience and onboarding
    - Optimize performance for production deployment
    
    **Success Criteria:**
    - All improvements are backward compatible
    - Changes include comprehensive tests
    - Documentation is updated for all changes
    - Performance improvements are measurable
    - Code review approval from all team members
    
    Focus on changes that provide the highest impact with manageable risk.
    """
    
    print("\n🔍 Starting Codebase Analysis and Improvement Sprint...")
    print("=" * 70)
    
    # Run the improvement sprint
    try:
        improvement_results = improvement_team.run_development_sprint(
            feature_request=improvement_request,
            max_iterations=25  # Allow extensive analysis and improvement
        )
        
        print("\n" + "=" * 70)
        print("📊 IMPROVEMENT SPRINT RESULTS")
        print("=" * 70)
        print(f"Status: {improvement_results['status']}")
        print(f"Iterations Used: {improvement_results['iterations_used']}")
        print(f"Timestamp: {improvement_results['timestamp']}")
        
        if improvement_results['status'] == 'completed':
            print("\n✅ Improvement sprint completed successfully!")
            print("\n📋 Improvement Summary:")
            print(improvement_results['sprint_execution'])
        else:
            print(f"\n❌ Improvement sprint failed: {improvement_results.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Improvement sprint failed: {str(e)}")
        return
    
    # Conduct a comprehensive architectural review
    print("\n" + "=" * 70)
    print("🏗️ ARCHITECTURAL REVIEW")
    print("=" * 70)
    
    try:
        architecture_review = improvement_team.run_code_review(
            code_path=Path("./autogen"),
            review_criteria=[
                "System architecture and design patterns",
                "Module cohesion and coupling",
                "Scalability and performance considerations", 
                "Code organization and structure",
                "API design and consistency",
                "Error handling and resilience",
                "Configuration management",
                "Extensibility and maintainability"
            ]
        )
        
        print("✅ Architectural review completed!")
        print("\n🏗️ Architecture Analysis:")
        print(architecture_review['review_results'])
        
    except Exception as e:
        logger.error(f"Architectural review failed: {str(e)}")
    
    # Run improvement retrospective
    print("\n" + "=" * 70)
    print("🎯 IMPROVEMENT RETROSPECTIVE")
    print("=" * 70)
    
    try:
        retrospective = improvement_team.run_retrospective()
        
        print("✅ Improvement retrospective completed!")
        print("\n🔄 Retrospective Insights:")
        print(retrospective['retrospective_discussion'])
        
    except Exception as e:
        logger.error(f"Retrospective failed: {str(e)}")
    
    # Create improvement roadmap
    print("\n" + "=" * 70)
    print("🗺️ IMPROVEMENT ROADMAP PLANNING")
    print("=" * 70)
    
    roadmap_request = """
    Based on our analysis and improvements, create a comprehensive roadmap for future enhancements:
    
    **Roadmap Components:**
    1. **Short-term (1-3 months)**: Critical fixes and high-impact improvements
    2. **Medium-term (3-6 months)**: Architectural enhancements and feature additions
    3. **Long-term (6-12 months)**: Strategic improvements and research initiatives
    
    **Include:**
    - Prioritized list of improvements with effort estimates
    - Technical debt reduction plan
    - Performance optimization roadmap
    - Security enhancement timeline
    - Documentation and testing improvements
    - Team capacity and resource requirements
    
    Focus on creating a realistic, actionable plan that balances innovation with stability.
    """
    
    try:
        roadmap_results = improvement_team.run_sprint_planning(
            sprint_goal="Create Comprehensive Improvement Roadmap",
            requirements=roadmap_request
        )
        
        print("✅ Improvement roadmap created!")
        print("\n🗺️ Roadmap Summary:")
        print(roadmap_results['planning_session'])
        
    except Exception as e:
        logger.error(f"Roadmap planning failed: {str(e)}")
    
    # Export all results
    print("\n" + "=" * 70)
    print("📁 EXPORTING IMPROVEMENT RESULTS")
    print("=" * 70)
    
    try:
        export_path = improvement_team.export_sprint_history(
            output_path=Path("./improvement_history.json")
        )
        print(f"✅ Improvement history exported to: {export_path}")
        
        # Display final team status
        team_status = improvement_team.get_team_status()
        print("\n👥 Self-Improving Team Final Status:")
        print(f"  - Sprints Completed: {team_status['sprint_history_count']}")
        print(f"  - Project Path: {team_status['project_path']}")
        print(f"  - Focus Areas: {', '.join(team_status['sprint_config']['focus_areas'])}")
        
        print("\n🎉 Self-improvement cycle completed successfully!")
        print("The team has analyzed the codebase and provided comprehensive improvement recommendations.")
        
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")


if __name__ == "__main__":
    main()