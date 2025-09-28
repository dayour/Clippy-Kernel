# Copyright (c) 2023 - 2025, Clippy Kernel Development Team
#
# SPDX-License-Identifier: Apache-2.0

"""
Agent Development Team Module

This module provides an advanced Agent Development Team implementation for Clippy Kernel,
enabling collaborative AI agents that follow agile methodologies to iteratively improve
codebases, implement features, and conduct comprehensive code reviews.

Key Features:
- Agile sprint planning and execution
- Multi-role agent specialization (Product Owner, Architect, Developer, QA, DevOps, Scrum Master)
- Self-improving development workflows
- Automated code review and testing
- Real-time collaboration capabilities
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..conversable_agent import ConversableAgent
from ..group.patterns import AutoPattern
from ..group import run_group_chat
from ...llm_config import LLMConfig
from ...import_utils import optional_import_block

logger = logging.getLogger(__name__)


class SprintPhase(Enum):
    """Sprint phases for agile development workflow."""
    PLANNING = "planning"
    DEVELOPMENT = "development"
    REVIEW = "review"
    TESTING = "testing"
    RETROSPECTIVE = "retrospective"
    COMPLETE = "complete"


class AgentRole(Enum):
    """Agent roles in the development team."""
    PRODUCT_OWNER = "product_owner"
    TECH_ARCHITECT = "tech_architect"
    SENIOR_DEVELOPER = "senior_developer"
    QA_ENGINEER = "qa_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    SCRUM_MASTER = "scrum_master"


@dataclass
class UserStory:
    """Represents a user story in the development backlog."""
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    story_points: int
    priority: int
    status: str = "backlog"
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SprintConfig:
    """Configuration for sprint execution."""
    duration_days: int = 14
    capacity_points: int = 40
    focus_areas: List[str] = field(default_factory=lambda: ["functionality", "quality", "performance"])
    max_iterations: int = 10
    auto_testing: bool = True
    code_review_required: bool = True


class AgentDevTeam:
    """
    Advanced Agent Development Team for collaborative software development.
    
    This class creates a self-organizing team of AI agents that follow agile methodologies
    to plan, develop, test, and deploy software features collaboratively.
    """
    
    def __init__(
        self, 
        llm_config: LLMConfig,
        project_path: Optional[Path] = None,
        sprint_config: Optional[SprintConfig] = None,
        custom_agents: Optional[Dict[AgentRole, ConversableAgent]] = None
    ):
        """
        Initialize the Agent Development Team.
        
        Args:
            llm_config: Configuration for language models
            project_path: Path to the project directory
            sprint_config: Configuration for sprint execution
            custom_agents: Custom agent implementations for specific roles
        """
        self.llm_config = llm_config
        self.project_path = project_path or Path.cwd()
        self.sprint_config = sprint_config or SprintConfig()
        self.current_sprint: Optional[Dict] = None
        self.backlog: List[UserStory] = []
        self.sprint_history: List[Dict] = []
        
        # Initialize agents
        self.agents = self._create_agents(custom_agents)
        self._setup_team_pattern()
        
        logger.info(f"Agent Development Team initialized with {len(self.agents)} agents")
    
    def _create_agents(self, custom_agents: Optional[Dict[AgentRole, ConversableAgent]] = None) -> Dict[AgentRole, ConversableAgent]:
        """Create the development team agents with specialized roles."""
        agents = {}
        
        # Use custom agents if provided, otherwise create default ones
        if custom_agents:
            agents.update(custom_agents)
        
        # Product Owner
        if AgentRole.PRODUCT_OWNER not in agents:
            agents[AgentRole.PRODUCT_OWNER] = ConversableAgent(
                name="product_owner",
                system_message="""You are an experienced Product Owner who:
                - Defines clear, actionable user stories with acceptance criteria
                - Prioritizes features based on business value and user impact
                - Communicates requirements clearly to the development team
                - Ensures deliverables meet stakeholder needs and quality standards
                - Makes data-driven decisions about feature priorities
                - Balances technical debt with new feature development""",
                llm_config=self.llm_config,
                description="Defines requirements, prioritizes features, and ensures business value delivery",
            )
        
        # Technical Architect
        if AgentRole.TECH_ARCHITECT not in agents:
            agents[AgentRole.TECH_ARCHITECT] = ConversableAgent(
                name="tech_architect",
                system_message="""You are a Senior Technical Architect who:
                - Designs scalable, maintainable, and robust system architectures
                - Makes informed technology stack decisions based on requirements
                - Defines coding standards, design patterns, and best practices
                - Reviews architectural decisions for long-term viability and scalability
                - Ensures security, performance, and maintainability considerations
                - Provides technical guidance and mentorship to the team""",
                llm_config=self.llm_config,
                description="Designs system architecture and provides technical leadership",
            )
        
        # Senior Developer
        if AgentRole.SENIOR_DEVELOPER not in agents:
            agents[AgentRole.SENIOR_DEVELOPER] = ConversableAgent(
                name="senior_developer",
                system_message="""You are a Senior Software Developer who:
                - Implements complex features and algorithms efficiently
                - Writes clean, maintainable, and well-documented code
                - Follows established coding standards and best practices
                - Optimizes code for performance, security, and scalability
                - Mentors other developers and shares knowledge
                - Reviews code thoroughly and provides constructive feedback""",
                llm_config=self.llm_config,
                description="Implements features and provides technical expertise",
            )
        
        # QA Engineer
        if AgentRole.QA_ENGINEER not in agents:
            agents[AgentRole.QA_ENGINEER] = ConversableAgent(
                name="qa_engineer",
                system_message="""You are a Quality Assurance Engineer who:
                - Creates comprehensive test plans and detailed test cases
                - Performs thorough manual and automated testing
                - Identifies bugs, edge cases, and potential issues
                - Ensures quality standards and acceptance criteria are met
                - Validates performance, security, and usability requirements
                - Provides clear bug reports and recommendations for improvement""",
                llm_config=self.llm_config,
                description="Ensures quality through comprehensive testing and validation",
            )
        
        # DevOps Engineer
        if AgentRole.DEVOPS_ENGINEER not in agents:
            agents[AgentRole.DEVOPS_ENGINEER] = ConversableAgent(
                name="devops_engineer",
                system_message="""You are a DevOps Engineer who:
                - Manages CI/CD pipelines and deployment automation
                - Handles infrastructure provisioning and configuration
                - Monitors system performance, reliability, and security
                - Implements security best practices and compliance measures
                - Optimizes deployment processes and system performance
                - Ensures scalability and disaster recovery capabilities""",
                llm_config=self.llm_config,
                description="Manages deployment, infrastructure, and system reliability",
            )
        
        # Scrum Master
        if AgentRole.SCRUM_MASTER not in agents:
            agents[AgentRole.SCRUM_MASTER] = ConversableAgent(
                name="scrum_master",
                system_message="""You are an experienced Scrum Master who:
                - Facilitates sprint planning, daily standups, and retrospectives
                - Removes blockers and impediments to team productivity
                - Ensures the team follows agile principles and best practices
                - Coordinates team communication and collaboration
                - Tracks progress and helps maintain sprint commitments
                - Promotes continuous improvement and team efficiency
                
                When a sprint is successfully completed, output: SPRINT_COMPLETE!""",
                llm_config=self.llm_config,
                description="Facilitates agile processes and removes team impediments",
                is_termination_msg=lambda x: "SPRINT_COMPLETE!" in (x.get("content", "") or "").upper(),
            )
        
        return agents
    
    def _setup_team_pattern(self):
        """Set up the team orchestration pattern."""
        agent_list = list(self.agents.values())
        
        self.team_pattern = AutoPattern(
            agents=agent_list,
            initial_agent=self.agents[AgentRole.SCRUM_MASTER],
            group_manager_args={
                "name": "team_lead", 
                "llm_config": self.llm_config,
                "system_message": "You coordinate the development team and ensure effective collaboration."
            },
        )
    
    def create_user_story(
        self, 
        title: str, 
        description: str, 
        acceptance_criteria: List[str],
        story_points: int = 5,
        priority: int = 3
    ) -> UserStory:
        """Create a new user story and add it to the backlog."""
        story = UserStory(
            id=f"US-{len(self.backlog) + 1:03d}",
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            story_points=story_points,
            priority=priority
        )
        self.backlog.append(story)
        logger.info(f"Created user story: {story.id} - {title}")
        return story
    
    def plan_sprint(
        self, 
        sprint_goal: str,
        selected_stories: Optional[List[str]] = None
    ) -> Dict:
        """Plan a new sprint with the development team."""
        
        # Auto-select stories if none provided
        if selected_stories is None:
            available_points = self.sprint_config.capacity_points
            selected_stories = []
            
            # Sort by priority and select stories that fit capacity
            sorted_backlog = sorted(self.backlog, key=lambda s: s.priority)
            for story in sorted_backlog:
                if story.story_points <= available_points and story.status == "backlog":
                    selected_stories.append(story.id)
                    available_points -= story.story_points
        
        sprint_data = {
            "id": f"Sprint-{len(self.sprint_history) + 1}",
            "goal": sprint_goal,
            "stories": selected_stories,
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=self.sprint_config.duration_days),
            "phase": SprintPhase.PLANNING,
            "capacity": self.sprint_config.capacity_points
        }
        
        self.current_sprint = sprint_data
        
        # Update story statuses
        for story_id in selected_stories:
            for story in self.backlog:
                if story.id == story_id:
                    story.status = "sprint_backlog"
        
        logger.info(f"Sprint planned: {sprint_data['id']} with {len(selected_stories)} stories")
        return sprint_data
    
    def run_sprint_planning(self, sprint_goal: str, requirements: str) -> Dict:
        """Execute sprint planning session with the team."""
        
        planning_message = f"""
        🎯 SPRINT PLANNING SESSION
        
        Sprint Goal: {sprint_goal}
        
        Requirements: {requirements}
        
        Team, let's conduct our sprint planning session. We need to:
        
        1. **Product Owner**: Break down the requirements into detailed user stories with acceptance criteria
        2. **Technical Architect**: Review technical approach and identify architectural considerations  
        3. **Senior Developer**: Estimate effort and identify technical dependencies
        4. **QA Engineer**: Define testing strategy and quality criteria
        5. **DevOps Engineer**: Identify deployment and infrastructure requirements
        6. **Scrum Master**: Facilitate the discussion and ensure we have a solid plan
        
        Please collaborate to create a comprehensive sprint plan. Focus on:
        - Clear user stories with acceptance criteria
        - Technical implementation approach
        - Testing and quality assurance strategy
        - Deployment and infrastructure needs
        - Risk identification and mitigation
        
        Sprint Capacity: {self.sprint_config.capacity_points} story points
        Duration: {self.sprint_config.duration_days} days
        """
        
        response = run_group_chat(
            pattern=self.team_pattern,
            messages=planning_message,
            max_rounds=15,
        )
        
        # Extract and store planning results
        planning_results = {
            "sprint_goal": sprint_goal,
            "planning_session": response.summary,
            "timestamp": datetime.now(),
            "phase": SprintPhase.PLANNING
        }
        
        return planning_results
    
    def run_development_sprint(
        self, 
        feature_request: str, 
        max_iterations: Optional[int] = None
    ) -> Dict:
        """
        Execute a complete development sprint for the given feature request.
        
        Args:
            feature_request: Description of the feature to implement
            max_iterations: Maximum number of development iterations
            
        Returns:
            Dictionary containing sprint results and artifacts
        """
        max_iterations = max_iterations or self.sprint_config.max_iterations
        
        sprint_message = f"""
        🚀 DEVELOPMENT SPRINT EXECUTION
        
        Feature Request: {feature_request}
        
        Team, we're starting a development sprint to implement this feature. Let's work collaboratively:
        
        **Sprint Process:**
        1. **Sprint Planning** (Scrum Master leads)
           - Define user stories and acceptance criteria
           - Estimate effort and identify dependencies
           - Create sprint backlog
        
        2. **Architecture & Design** (Tech Architect leads)
           - Design system architecture
           - Define interfaces and data models
           - Identify technical risks and mitigation strategies
        
        3. **Implementation** (Senior Developer leads)
           - Implement core functionality
           - Follow coding standards and best practices
           - Create comprehensive documentation
        
        4. **Quality Assurance** (QA Engineer leads)
           - Create and execute test plans
           - Perform functional and integration testing
           - Validate acceptance criteria
        
        5. **Deployment Preparation** (DevOps Engineer leads)
           - Prepare deployment scripts and configuration
           - Set up monitoring and logging
           - Ensure security and compliance
        
        6. **Sprint Review & Retrospective** (Scrum Master leads)
           - Review completed work
           - Identify lessons learned
           - Plan improvements for next sprint
        
        **Sprint Goals:**
        - Deliver working, tested software
        - Meet all acceptance criteria
        - Maintain high quality standards
        - Document decisions and learnings
        
        Project Path: {self.project_path}
        Max Iterations: {max_iterations}
        
        Let's begin! Scrum Master, please kick off our sprint planning.
        """
        
        try:
            # Execute the sprint
            response = run_group_chat(
                pattern=self.team_pattern,
                messages=sprint_message,
                max_rounds=max_iterations,
            )
            
            # Compile sprint results
            sprint_results = {
                "feature_request": feature_request,
                "sprint_execution": response.summary,
                "chat_history": response.chat_history if hasattr(response, 'chat_history') else [],
                "timestamp": datetime.now(),
                "project_path": str(self.project_path),
                "iterations_used": len(response.chat_history) if hasattr(response, 'chat_history') else 0,
                "max_iterations": max_iterations,
                "status": "completed",
                "phase": SprintPhase.COMPLETE
            }
            
            # Add to sprint history
            self.sprint_history.append(sprint_results)
            
            logger.info(f"Sprint completed for feature: {feature_request}")
            return sprint_results
            
        except Exception as e:
            logger.error(f"Sprint execution failed: {str(e)}")
            error_results = {
                "feature_request": feature_request,
                "error": str(e),
                "timestamp": datetime.now(),
                "status": "failed",
                "phase": SprintPhase.DEVELOPMENT
            }
            self.sprint_history.append(error_results)
            return error_results
    
    def run_code_review(self, code_path: Path, review_criteria: Optional[List[str]] = None) -> Dict:
        """Execute a comprehensive code review session."""
        
        default_criteria = [
            "Code quality and maintainability",
            "Security best practices",
            "Performance optimization",
            "Test coverage and quality",
            "Documentation completeness",
            "Architecture alignment",
            "Error handling",
            "Code style consistency"
        ]
        
        criteria = review_criteria or default_criteria
        
        review_message = f"""
        🔍 CODE REVIEW SESSION
        
        Code Path: {code_path}
        
        Team, let's conduct a thorough code review. Each role should contribute their expertise:
        
        **Technical Architect**: Review architectural decisions, design patterns, and long-term maintainability
        **Senior Developer**: Review code quality, algorithms, and implementation details
        **QA Engineer**: Review testability, edge cases, and quality assurance aspects
        **DevOps Engineer**: Review deployment readiness, security, and operational concerns
        **Product Owner**: Verify feature completeness and user requirements fulfillment
        
        **Review Criteria:**
        {chr(10).join(f'- {criterion}' for criterion in criteria)}
        
        Please provide:
        1. Specific feedback with file/line references where applicable
        2. Severity levels (Critical, High, Medium, Low) for issues
        3. Actionable recommendations for improvement
        4. Positive recognition for good practices
        
        Focus on constructive feedback that improves code quality and team learning.
        """
        
        response = run_group_chat(
            pattern=self.team_pattern,
            messages=review_message,
            max_rounds=10,
        )
        
        return {
            "code_path": str(code_path),
            "review_results": response.summary,
            "criteria": criteria,
            "timestamp": datetime.now(),
            "reviewers": list(self.agents.keys())
        }
    
    def run_retrospective(self) -> Dict:
        """Conduct a sprint retrospective to identify improvements."""
        
        retrospective_message = """
        🔄 SPRINT RETROSPECTIVE
        
        Team, let's reflect on our recent sprint and identify opportunities for improvement.
        
        Please share your thoughts on:
        
        **What Went Well? (Continue)**
        - What practices, processes, or behaviors should we continue?
        - What contributed to our success?
        
        **What Didn't Go Well? (Stop)**
        - What challenges did we face?
        - What should we stop doing or change?
        
        **What Can We Improve? (Start)**
        - What new practices should we try?
        - How can we work more effectively together?
        
        **Action Items**
        - Specific, actionable improvements for the next sprint
        - Who will be responsible for each action?
        
        Let's have an open and honest discussion to continuously improve our team performance.
        """
        
        response = run_group_chat(
            pattern=self.team_pattern,
            messages=retrospective_message,
            max_rounds=8,
        )
        
        retrospective_results = {
            "retrospective_discussion": response.summary,
            "timestamp": datetime.now(),
            "participants": list(self.agents.keys()),
            "sprint_history_count": len(self.sprint_history)
        }
        
        return retrospective_results
    
    def get_team_status(self) -> Dict:
        """Get current status of the development team and ongoing work."""
        return {
            "team_composition": {
                role.value: agent.name for role, agent in self.agents.items()
            },
            "current_sprint": self.current_sprint,
            "backlog_size": len(self.backlog),
            "sprint_history_count": len(self.sprint_history),
            "project_path": str(self.project_path),
            "sprint_config": {
                "duration_days": self.sprint_config.duration_days,
                "capacity_points": self.sprint_config.capacity_points,
                "focus_areas": self.sprint_config.focus_areas
            }
        }
    
    def export_sprint_history(self, output_path: Optional[Path] = None) -> Path:
        """Export sprint history to JSON file."""
        output_path = output_path or (self.project_path / "sprint_history.json")
        
        export_data = {
            "team_config": self.get_team_status(),
            "backlog": [
                {
                    "id": story.id,
                    "title": story.title,
                    "description": story.description,
                    "acceptance_criteria": story.acceptance_criteria,
                    "story_points": story.story_points,
                    "priority": story.priority,
                    "status": story.status,
                    "created_at": story.created_at.isoformat()
                } for story in self.backlog
            ],
            "sprint_history": self.sprint_history,
            "exported_at": datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Sprint history exported to: {output_path}")
        return output_path


def create_agent_dev_team(
    llm_config: LLMConfig,
    project_path: Optional[Path] = None,
    sprint_duration_days: int = 14,
    capacity_points: int = 40,
    focus_areas: Optional[List[str]] = None
) -> AgentDevTeam:
    """
    Factory function to create a pre-configured Agent Development Team.
    
    Args:
        llm_config: Language model configuration
        project_path: Path to project directory
        sprint_duration_days: Length of sprints in days
        capacity_points: Team capacity in story points
        focus_areas: Areas of focus for development
        
    Returns:
        Configured AgentDevTeam instance
    """
    sprint_config = SprintConfig(
        duration_days=sprint_duration_days,
        capacity_points=capacity_points,
        focus_areas=focus_areas or ["functionality", "quality", "performance", "maintainability"]
    )
    
    return AgentDevTeam(
        llm_config=llm_config,
        project_path=project_path,
        sprint_config=sprint_config
    )


def create_self_improving_team(
    llm_config: LLMConfig,
    project_path: Path,
    improvement_areas: Optional[List[str]] = None
) -> AgentDevTeam:
    """
    Create a specialized team focused on self-improvement and codebase enhancement.
    
    Args:
        llm_config: Language model configuration
        project_path: Path to the project to improve
        improvement_areas: Specific areas to focus improvements on
        
    Returns:
        AgentDevTeam configured for self-improvement workflows
    """
    improvement_areas = improvement_areas or [
        "code_quality", "performance", "security", "maintainability", 
        "test_coverage", "documentation", "architecture"
    ]
    
    sprint_config = SprintConfig(
        duration_days=7,  # Shorter sprints for continuous improvement
        capacity_points=30,
        focus_areas=improvement_areas,
        max_iterations=15,
        auto_testing=True,
        code_review_required=True
    )
    
    return AgentDevTeam(
        llm_config=llm_config,
        project_path=project_path, 
        sprint_config=sprint_config
    )