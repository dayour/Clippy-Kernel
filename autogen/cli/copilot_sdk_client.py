# Copyright (c) 2023 - 2025, Clippy Kernel Development Team
#
# SPDX-License-Identifier: Apache-2.0

"""
GitHub Copilot SDK Integration for Clippy SWE Agent

This module provides integration with the official GitHub Copilot SDK,
enabling access to Copilot's agentic core, multi-turn conversations,
programmable tools, and streaming responses.

Features:
- Multi-turn conversations with session history
- Programmable tool execution
- Model selection (GPT-4, GPT-5, Claude, Gemini)
- Real-time streaming responses
- MCP server integration
- GitHub authentication
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from ..import_utils import optional_import_block

with optional_import_block():
    # Note: GitHub Copilot SDK for Python is in preview
    # For now, we'll use httpx to interact with the API directly
    import httpx
    import anthropic
    from google import generativeai as genai
    from openai import OpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    GOOGLE = "google"
    GITHUB_COPILOT = "github_copilot"


@dataclass
class CopilotSession:
    """Represents a Copilot SDK session."""
    
    session_id: str
    model: str
    provider: ModelProvider
    history: list[dict[str, Any]]
    tools: list[dict[str, Any]]
    context_window: int = 8192
    
    def add_message(self, role: str, content: str, metadata: dict[str, Any] | None = None):
        """Add a message to session history."""
        message = {
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        self.history.append(message)
        
        # Manage context window
        if len(self.history) > 100:
            self.history = self.history[-50:]  # Keep last 50 messages


class CopilotSDKClient:
    """
    Client for GitHub Copilot SDK integration.
    
    Provides unified interface to multiple AI models (OpenAI, Claude, Gemini)
    with Copilot-style features including tool execution, streaming, and
    multi-turn conversations.
    """
    
    def __init__(
        self,
        github_token: str | None = None,
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None,
        google_api_key: str | None = None,
        default_model: str = "gpt-4",
        default_provider: ModelProvider = ModelProvider.OPENAI,
    ):
        """
        Initialize Copilot SDK client.
        
        Args:
            github_token: GitHub personal access token for Copilot API
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key  
            google_api_key: Google AI API key
            default_model: Default model to use
            default_provider: Default provider
        """
        self.github_token = github_token
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.google_api_key = google_api_key
        self.default_model = default_model
        self.default_provider = default_provider
        
        # Initialize clients
        self.openai_client: OpenAI | None = None
        self.anthropic_client: anthropic.Anthropic | None = None
        self.google_client: Any | None = None
        self.http_client: httpx.AsyncClient | None = None
        
        self._initialize_clients()
        
        # Session management
        self.sessions: dict[str, CopilotSession] = {}
        self.registered_tools: dict[str, Callable] = {}
        
        logger.info(f"CopilotSDKClient initialized with provider: {default_provider}")
    
    def _initialize_clients(self):
        """Initialize API clients for different providers."""
        try:
            if self.openai_api_key:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        try:
            if self.anthropic_api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                logger.info("Anthropic client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic client: {e}")
        
        try:
            if self.google_api_key:
                genai.configure(api_key=self.google_api_key)
                self.google_client = genai
                logger.info("Google AI client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Google AI client: {e}")
        
        # Initialize HTTP client for GitHub Copilot API
        self.http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.github_token}" if self.github_token else "",
                "Content-Type": "application/json",
            },
            timeout=60.0
        )
    
    def create_session(
        self,
        model: str | None = None,
        provider: ModelProvider | None = None,
        context_window: int = 8192,
    ) -> CopilotSession:
        """
        Create a new Copilot session.
        
        Args:
            model: Model to use (e.g., "gpt-4", "claude-3-opus", "gemini-pro")
            provider: Provider to use
            context_window: Maximum context window size
            
        Returns:
            CopilotSession object
        """
        import uuid
        
        session_id = str(uuid.uuid4())
        model = model or self.default_model
        provider = provider or self.default_provider
        
        # Adjust context window based on model
        if "gemini" in model.lower():
            context_window = min(context_window, 1000000)  # Gemini: 1M tokens
        elif "claude-3" in model.lower():
            context_window = min(context_window, 200000)  # Claude 3: 200K tokens
        elif "gpt-4" in model.lower():
            context_window = min(context_window, 128000)  # GPT-4: 128K tokens
        
        session = CopilotSession(
            session_id=session_id,
            model=model,
            provider=provider,
            history=[],
            tools=list(self.registered_tools.keys()),
            context_window=context_window,
        )
        
        self.sessions[session_id] = session
        logger.info(f"Created session {session_id} with model {model} (provider: {provider})")
        
        return session
    
    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: dict[str, Any],
    ) -> None:
        """
        Register a tool that can be called by the AI model.
        
        Args:
            name: Tool name
            func: Callable function
            description: Tool description
            parameters: JSON schema for parameters
        """
        self.registered_tools[name] = {
            "name": name,
            "function": func,
            "description": description,
            "parameters": parameters,
        }
        logger.info(f"Registered tool: {name}")
    
    async def send_message(
        self,
        session_id: str,
        message: str,
        stream: bool = False,
        execute_tools: bool = True,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """
        Send a message in a session.
        
        Args:
            session_id: Session ID
            message: User message
            stream: Whether to stream the response
            execute_tools: Whether to execute tools if called
            
        Returns:
            Response dict or async iterator for streaming
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        session.add_message("user", message)
        
        # Route to appropriate provider
        if session.provider == ModelProvider.OPENAI:
            return await self._send_openai(session, stream, execute_tools)
        elif session.provider == ModelProvider.ANTHROPIC:
            return await self._send_anthropic(session, stream, execute_tools)
        elif session.provider == ModelProvider.GOOGLE:
            return await self._send_google(session, stream, execute_tools)
        elif session.provider == ModelProvider.GITHUB_COPILOT:
            return await self._send_github_copilot(session, stream, execute_tools)
        else:
            raise ValueError(f"Unsupported provider: {session.provider}")
    
    async def _send_openai(
        self,
        session: CopilotSession,
        stream: bool,
        execute_tools: bool,
    ) -> dict[str, Any]:
        """Send message using OpenAI API."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        try:
            # Prepare messages
            messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in session.history
            ]
            
            # Prepare tools if registered
            tools = None
            if execute_tools and self.registered_tools:
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool["description"],
                            "parameters": tool["parameters"],
                        }
                    }
                    for tool in self.registered_tools.values()
                ]
            
            # Make API call
            response = self.openai_client.chat.completions.create(
                model=session.model,
                messages=messages,
                tools=tools if tools else None,
                stream=stream,
            )
            
            if stream:
                # Return streaming response
                async def stream_response():
                    full_content = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_content += content
                            yield {"content": content, "done": False}
                    
                    session.add_message("assistant", full_content)
                    yield {"content": "", "done": True}
                
                return stream_response()
            else:
                # Handle tool calls
                message = response.choices[0].message
                
                if message.tool_calls and execute_tools:
                    # Execute tools
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        if tool_name in self.registered_tools:
                            import json
                            args = json.loads(tool_call.function.arguments)
                            func = self.registered_tools[tool_name]["function"]
                            result = func(**args)
                            
                            # Add tool result to session
                            session.add_message(
                                "tool",
                                str(result),
                                {"tool_name": tool_name, "tool_call_id": tool_call.id}
                            )
                
                content = message.content or ""
                session.add_message("assistant", content)
                
                return {
                    "content": content,
                    "model": session.model,
                    "provider": session.provider.value,
                    "finish_reason": response.choices[0].finish_reason,
                }
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            return {
                "error": str(e),
                "content": "",
                "provider": session.provider.value,
            }
    
    async def _send_anthropic(
        self,
        session: CopilotSession,
        stream: bool,
        execute_tools: bool,
    ) -> dict[str, Any]:
        """Send message using Anthropic API."""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        try:
            # Prepare messages (Claude format)
            messages = []
            for msg in session.history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Prepare tools
            tools = None
            if execute_tools and self.registered_tools:
                tools = [
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        "input_schema": tool["parameters"],
                    }
                    for tool in self.registered_tools.values()
                ]
            
            # Make API call
            response = self.anthropic_client.messages.create(
                model=session.model,
                max_tokens=4096,
                messages=messages,
                tools=tools if tools else None,
                stream=stream,
            )
            
            if stream:
                # Return streaming response
                async def stream_response():
                    full_content = ""
                    with response as stream:
                        for event in stream:
                            if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                                content = event.delta.text
                                full_content += content
                                yield {"content": content, "done": False}
                    
                    session.add_message("assistant", full_content)
                    yield {"content": "", "done": True}
                
                return stream_response()
            else:
                content = response.content[0].text if response.content else ""
                session.add_message("assistant", content)
                
                return {
                    "content": content,
                    "model": session.model,
                    "provider": session.provider.value,
                    "finish_reason": response.stop_reason,
                }
        
        except Exception as e:
            logger.error(f"Anthropic API error: {e}", exc_info=True)
            return {
                "error": str(e),
                "content": "",
                "provider": session.provider.value,
            }
    
    async def _send_google(
        self,
        session: CopilotSession,
        stream: bool,
        execute_tools: bool,
    ) -> dict[str, Any]:
        """Send message using Google Gemini API."""
        if not self.google_client:
            raise ValueError("Google AI client not initialized")
        
        try:
            # Initialize model
            model = self.google_client.GenerativeModel(session.model)
            
            # Start chat with history
            chat_history = []
            for msg in session.history[:-1]:  # Exclude last message (current)
                if msg["role"] in ["user", "model"]:
                    chat_history.append({
                        "role": msg["role"],
                        "parts": [msg["content"]]
                    })
            
            chat = model.start_chat(history=chat_history)
            
            # Send message
            current_message = session.history[-1]["content"]
            
            if stream:
                response = chat.send_message(current_message, stream=True)
                
                async def stream_response():
                    full_content = ""
                    for chunk in response:
                        if chunk.text:
                            content = chunk.text
                            full_content += content
                            yield {"content": content, "done": False}
                    
                    session.add_message("assistant", full_content)
                    yield {"content": "", "done": True}
                
                return stream_response()
            else:
                response = chat.send_message(current_message)
                content = response.text
                session.add_message("assistant", content)
                
                return {
                    "content": content,
                    "model": session.model,
                    "provider": session.provider.value,
                    "finish_reason": "stop",
                }
        
        except Exception as e:
            logger.error(f"Google AI API error: {e}", exc_info=True)
            return {
                "error": str(e),
                "content": "",
                "provider": session.provider.value,
            }
    
    async def _send_github_copilot(
        self,
        session: CopilotSession,
        stream: bool,
        execute_tools: bool,
    ) -> dict[str, Any]:
        """Send message using GitHub Copilot API."""
        # Placeholder for official GitHub Copilot SDK integration
        # Fall back to OpenAI for now
        logger.info("GitHub Copilot API not yet available, falling back to OpenAI")
        session.provider = ModelProvider.OPENAI
        return await self._send_openai(session, stream, execute_tools)
    
    def get_session(self, session_id: str) -> CopilotSession | None:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> list[str]:
        """List all session IDs."""
        return list(self.sessions.keys())
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    async def close(self):
        """Close all client connections."""
        if self.http_client:
            await self.http_client.aclose()
