# Copyright (c) 2023 - 2025, Clippy Kernel Development Team
#
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for the Agent Development Team functionality.

This module tests the core functionality of the AgentDevTeam class including:
- Agent creation and role specialization
- Sprint planning and execution
- Code review processes
- Retrospectives and continuous improvement
- Self-improving team workflows
"""

import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from autogen.llm_config import LLMConfig
from autogen.agentchat.agent_dev_team import (
    AgentDevTeam,
    create_agent_dev_team,
    create_self_improving_team,
    SprintConfig,
    UserStory,
    AgentRole,
    SprintPhase
)


class TestSprintConfig:
    """Test the SprintConfig dataclass."""
    
    def test_default_sprint_config(self):
        """Test default sprint configuration values."""
        config = SprintConfig()
        
        assert config.duration_days == 14
        assert config.capacity_points == 40
        assert config.focus_areas == ["functionality", "quality", "performance"]
        assert config.max_iterations == 10
        assert config.auto_testing is True
        assert config.code_review_required is True
    
    def test_custom_sprint_config(self):
        """Test custom sprint configuration values."""
        config = SprintConfig(
            duration_days=7,
            capacity_points=30,
            focus_areas=["security", "performance"],
            max_iterations=15,
            auto_testing=False,
            code_review_required=False
        )
        
        assert config.duration_days == 7
        assert config.capacity_points == 30
        assert config.focus_areas == ["security", "performance"]
        assert config.max_iterations == 15
        assert config.auto_testing is False
        assert config.code_review_required is False


class TestUserStory:
    """Test the UserStory dataclass."""
    
    def test_user_story_creation(self):
        """Test creating a user story."""
        story = UserStory(
            id="US-001",
            title="User Authentication",
            description="Implement user login and registration",
            acceptance_criteria=["User can login", "User can register", "Passwords are secure"],
            story_points=8,
            priority=1
        )
        
        assert story.id == "US-001"
        assert story.title == "User Authentication"
        assert story.description == "Implement user login and registration"
        assert len(story.acceptance_criteria) == 3
        assert story.story_points == 8
        assert story.priority == 1
        assert story.status == "backlog"
        assert story.assigned_to is None
        assert isinstance(story.created_at, datetime)


class TestAgentDevTeam:
    """Test the AgentDevTeam class."""
    
    @pytest.fixture
    def mock_llm_config(self):
        """Create a mock LLM configuration."""
        return Mock(spec=LLMConfig)
    
    @pytest.fixture
    def temp_project_path(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_agent_dev_team_initialization(self, mock_llm_config, temp_project_path):
        """Test AgentDevTeam initialization."""
        team = AgentDevTeam(
            llm_config=mock_llm_config,
            project_path=temp_project_path
        )
        
        assert team.llm_config == mock_llm_config
        assert team.project_path == temp_project_path
        assert isinstance(team.sprint_config, SprintConfig)
        assert team.current_sprint is None
        assert len(team.backlog) == 0
        assert len(team.sprint_history) == 0
        assert len(team.agents) == 6  # All agent roles
        
        # Check that all agent roles are present
        expected_roles = {
            AgentRole.PRODUCT_OWNER,
            AgentRole.TECH_ARCHITECT,
            AgentRole.SENIOR_DEVELOPER,
            AgentRole.QA_ENGINEER,
            AgentRole.DEVOPS_ENGINEER,
            AgentRole.SCRUM_MASTER
        }
        assert set(team.agents.keys()) == expected_roles
    
    def test_create_user_story(self, mock_llm_config, temp_project_path):
        """Test user story creation."""
        team = AgentDevTeam(
            llm_config=mock_llm_config,
            project_path=temp_project_path
        )
        
        story = team.create_user_story(
            title="Test Feature",
            description="A test feature for the application",
            acceptance_criteria=["Feature works", "Feature is tested"],
            story_points=5,
            priority=2
        )
        
        assert story.id == "US-001"
        assert story.title == "Test Feature"
        assert story.description == "A test feature for the application"
        assert story.acceptance_criteria == ["Feature works", "Feature is tested"]
        assert story.story_points == 5
        assert story.priority == 2
        assert len(team.backlog) == 1
        assert team.backlog[0] == story
    
    def test_plan_sprint(self, mock_llm_config, temp_project_path):
        """Test sprint planning functionality."""
        team = AgentDevTeam(
            llm_config=mock_llm_config,
            project_path=temp_project_path
        )
        
        # Create some user stories
        story1 = team.create_user_story("Feature 1", "Description 1", ["AC1"], 10, 1)
        story2 = team.create_user_story("Feature 2", "Description 2", ["AC2"], 15, 2)
        story3 = team.create_user_story("Feature 3", "Description 3", ["AC3"], 20, 3)
        
        # Plan sprint with auto-selection
        sprint = team.plan_sprint("Implement core features")
        
        assert sprint["id"] == "Sprint-1"
        assert sprint["goal"] == "Implement core features"
        assert sprint["phase"] == SprintPhase.PLANNING
        assert sprint["capacity"] == 40
        assert len(sprint["stories"]) == 2  # Should select story1 and story2 (25 points total)
        
        # Check that stories were updated
        assert story1.status == "sprint_backlog"
        assert story2.status == "sprint_backlog"
        assert story3.status == "backlog"  # Didn't fit in capacity
    
    def test_get_team_status(self, mock_llm_config, temp_project_path):
        """Test getting team status."""
        team = AgentDevTeam(
            llm_config=mock_llm_config,
            project_path=temp_project_path
        )
        
        # Add some data
        team.create_user_story("Test Story", "Description", ["AC"], 5, 1)
        team.plan_sprint("Test Sprint")
        
        status = team.get_team_status()
        
        assert "team_composition" in status
        assert "current_sprint" in status
        assert "backlog_size" in status
        assert "sprint_history_count" in status
        assert "project_path" in status
        assert "sprint_config" in status
        
        assert len(status["team_composition"]) == 6
        assert status["backlog_size"] == 1
        assert status["sprint_history_count"] == 0
        assert status["project_path"] == str(temp_project_path)
    
    def test_export_sprint_history(self, mock_llm_config, temp_project_path):
        """Test exporting sprint history."""
        team = AgentDevTeam(
            llm_config=mock_llm_config,
            project_path=temp_project_path
        )
        
        # Add some data
        team.create_user_story("Test Story", "Description", ["AC"], 5, 1)
        team.plan_sprint("Test Sprint")
        
        # Export history
        export_path = team.export_sprint_history()
        
        assert export_path.exists()
        assert export_path.name == "sprint_history.json"
        
        # Read and validate exported data
        with open(export_path) as f:
            data = json.load(f)
        
        assert "team_config" in data
        assert "backlog" in data
        assert "sprint_history" in data
        assert "exported_at" in data
        
        assert len(data["backlog"]) == 1
        assert data["backlog"][0]["title"] == "Test Story"


class TestFactoryFunctions:
    """Test factory functions for creating agent teams."""
    
    @pytest.fixture
    def mock_llm_config(self):
        """Create a mock LLM configuration."""
        return Mock(spec=LLMConfig)
    
    @pytest.fixture
    def temp_project_path(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_create_agent_dev_team(self, mock_llm_config, temp_project_path):
        """Test the create_agent_dev_team factory function."""
        team = create_agent_dev_team(
            llm_config=mock_llm_config,
            project_path=temp_project_path,
            sprint_duration_days=10,
            capacity_points=50,
            focus_areas=["quality", "security"]
        )
        
        assert isinstance(team, AgentDevTeam)
        assert team.llm_config == mock_llm_config
        assert team.project_path == temp_project_path
        assert team.sprint_config.duration_days == 10
        assert team.sprint_config.capacity_points == 50
        assert team.sprint_config.focus_areas == ["quality", "security"]
    
    def test_create_self_improving_team(self, mock_llm_config, temp_project_path):
        """Test the create_self_improving_team factory function."""
        team = create_self_improving_team(
            llm_config=mock_llm_config,
            project_path=temp_project_path,
            improvement_areas=["performance", "security"]
        )
        
        assert isinstance(team, AgentDevTeam)
        assert team.llm_config == mock_llm_config
        assert team.project_path == temp_project_path
        assert team.sprint_config.duration_days == 7  # Shorter sprints for improvement
        assert team.sprint_config.capacity_points == 30
        assert "performance" in team.sprint_config.focus_areas
        assert "security" in team.sprint_config.focus_areas
        assert team.sprint_config.auto_testing is True
        assert team.sprint_config.code_review_required is True


class TestAgentRoleSpecialization:
    """Test agent role specialization and system messages."""
    
    @pytest.fixture
    def mock_llm_config(self):
        """Create a mock LLM configuration."""
        return Mock(spec=LLMConfig)
    
    def test_agent_roles_are_distinct(self, mock_llm_config):
        """Test that each agent role has distinct responsibilities."""
        team = AgentDevTeam(llm_config=mock_llm_config)
        
        # Check that each agent has a unique system message
        system_messages = []
        for agent in team.agents.values():
            system_messages.append(agent.system_message)
        
        # All system messages should be unique
        assert len(set(system_messages)) == len(system_messages)
        
        # Check specific role characteristics
        po_agent = team.agents[AgentRole.PRODUCT_OWNER]
        assert "Product Owner" in po_agent.system_message
        assert "requirements" in po_agent.system_message.lower()
        
        architect_agent = team.agents[AgentRole.TECH_ARCHITECT]
        assert "Technical Architect" in architect_agent.system_message
        assert "architecture" in architect_agent.system_message.lower()
        
        dev_agent = team.agents[AgentRole.SENIOR_DEVELOPER]
        assert "Senior" in dev_agent.system_message
        assert "code" in dev_agent.system_message.lower()
        
        qa_agent = team.agents[AgentRole.QA_ENGINEER]
        assert "Quality" in qa_agent.system_message
        assert "test" in qa_agent.system_message.lower()
        
        devops_agent = team.agents[AgentRole.DEVOPS_ENGINEER]
        assert "DevOps" in devops_agent.system_message
        assert "deployment" in devops_agent.system_message.lower()
        
        scrum_agent = team.agents[AgentRole.SCRUM_MASTER]
        assert "Scrum Master" in scrum_agent.system_message
        assert "SPRINT_COMPLETE!" in scrum_agent.system_message


# Skip tests that require actual LLM API calls
@pytest.mark.skip(reason="Requires actual LLM API calls - run manually for integration testing")
class TestIntegrationScenarios:
    """Integration tests that require actual LLM API calls."""
    
    def test_full_sprint_execution(self):
        """Test a complete sprint execution with real agents."""
        # This would require actual API keys and LLM calls
        # Use for manual integration testing only
        pass
    
    def test_code_review_workflow(self):
        """Test the code review workflow with real agents."""
        # This would require actual API keys and LLM calls
        # Use for manual integration testing only
        pass
    
    def test_retrospective_process(self):
        """Test the retrospective process with real agents."""
        # This would require actual API keys and LLM calls
        # Use for manual integration testing only
        pass


if __name__ == "__main__":
    pytest.main([__file__])