# Copyright (c) 2023 - 2025, AG2ai, Inc., AG2ai open-source projects maintainers and core contributors
#
# SPDX-License-Identifier: Apache-2.0

"""
AG2 MCP Server

This server exposes the full AG2 toolkit via MCP (Model Context Protocol) for use with
VSCode extensions, Claude Code, and other MCP-compatible clients.

The server provides natural language interfaces to:
- Create and manage AG2 agents
- Run multi-agent conversations
- Execute code with various interpreters
- Access tool functionality
- Manage conversation state and memory
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union
from contextlib import asynccontextmanager

from ..import_utils import optional_import_block, require_optional_import
from ..agentchat import ConversableAgent
from ..llm_config import LLMConfig
from ..tools import Tool, Toolkit

with optional_import_block():
    from mcp.types import (
        Resource,
        Tool as MCPTool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        CallToolResult,
        GetPromptResult,
        ListPromptsResult,
        ListResourcesResult,
        ListToolsResult,
        ReadResourceResult,
    )
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.server.sse import sse_server
    from mcp import StdioServerParameters


class AG2MCPServer:
    """MCP Server that exposes AG2 functionality via natural language interface."""
    
    def __init__(self, name: str = "ag2-mcp-server"):
        self.name = name
        self.server = None
        self.agents: Dict[str, ConversableAgent] = {}
        self.active_conversations: Dict[str, List[Dict]] = {}
        self.memory_store: Dict[str, Any] = {}
        self.available_tools: Dict[str, Tool] = {}
        
        # Initialize MCP server
        self._setup_server()
    
    def _setup_server(self):
        """Set up the MCP server with AG2 tools and resources."""
        try:
            self.server = Server(self.name)
            
            # Register MCP tools
            self._register_tools()
            self._register_resources()
            self._register_prompts()
            
        except ImportError:
            print("MCP libraries not available. Install with: pip install mcp")
            sys.exit(1)
    
    def _register_tools(self):
        """Register AG2 tools as MCP tools."""
        
        @self.server.call_tool()
        async def create_agent(
            name: str,
            system_message: str = "You are a helpful AI assistant.",
            llm_config: Optional[Dict[str, Any]] = None
        ) -> CallToolResult:
            """Create a new AG2 conversable agent."""
            try:
                if llm_config is None:
                    llm_config = {"model": "gpt-4", "temperature": 0.7}
                
                agent = ConversableAgent(
                    name=name,
                    system_message=system_message,
                    llm_config=LLMConfig(llm_config),
                    human_input_mode="NEVER"
                )
                
                self.agents[name] = agent
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Successfully created agent '{name}' with system message: {system_message}"
                    )]
                )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"Error creating agent: {str(e)}"
                    )],
                    isError=True
                )
        
        @self.server.call_tool()
        async def list_agents() -> CallToolResult:
            """List all available AG2 agents."""
            agent_list = list(self.agents.keys())
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Available agents: {', '.join(agent_list) if agent_list else 'None'}"
                )]
            )
        
        @self.server.call_tool()
        async def send_message(
            agent_name: str,
            message: str,
            recipient_name: Optional[str] = None
        ) -> CallToolResult:
            """Send a message to an agent or between agents."""
            try:
                if agent_name not in self.agents:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"Agent '{agent_name}' not found. Available agents: {list(self.agents.keys())}"
                        )],
                        isError=True
                    )
                
                sender = self.agents[agent_name]
                
                if recipient_name and recipient_name in self.agents:
                    # Agent-to-agent communication
                    recipient = self.agents[recipient_name]
                    response = await sender.a_send_message(
                        message={"content": message, "role": "user"},
                        recipient=recipient
                    )
                else:
                    # Direct message to agent
                    response = await sender.a_generate_reply(
                        messages=[{"content": message, "role": "user"}]
                    )
                
                # Store conversation in memory
                conv_key = f"{agent_name}-{recipient_name}" if recipient_name else agent_name
                if conv_key not in self.active_conversations:
                    self.active_conversations[conv_key] = []
                
                self.active_conversations[conv_key].append({
                    "sender": agent_name,
                    "recipient": recipient_name,
                    "message": message,
                    "response": response if isinstance(response, str) else str(response),
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=str(response)
                    )]
                )
                
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Error sending message: {str(e)}"
                    )],
                    isError=True
                )
        
        @self.server.call_tool()
        async def run_group_chat(
            participant_names: List[str],
            initial_message: str,
            max_rounds: int = 5
        ) -> CallToolResult:
            """Run a group chat between multiple agents."""
            try:
                # Validate all participants exist
                missing_agents = [name for name in participant_names if name not in self.agents]
                if missing_agents:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"Missing agents: {missing_agents}. Available: {list(self.agents.keys())}"
                        )],
                        isError=True
                    )
                
                participants = [self.agents[name] for name in participant_names]
                
                # Simple group chat simulation
                conversation_log = []
                current_message = initial_message
                
                for round_num in range(max_rounds):
                    for i, agent in enumerate(participants):
                        response = await agent.a_generate_reply(
                            messages=[{"content": current_message, "role": "user"}]
                        )
                        
                        conversation_log.append({
                            "round": round_num + 1,
                            "agent": participant_names[i],
                            "message": current_message,
                            "response": str(response)
                        })
                        
                        current_message = str(response)
                
                # Store conversation
                conv_key = f"group-{'-'.join(participant_names)}"
                self.active_conversations[conv_key] = conversation_log
                
                # Format response
                formatted_log = "\n".join([
                    f"Round {entry['round']} - {entry['agent']}: {entry['response']}"
                    for entry in conversation_log
                ])
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Group chat completed:\n{formatted_log}"
                    )]
                )
                
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Error running group chat: {str(e)}"
                    )],
                    isError=True
                )
        
        @self.server.call_tool()
        async def execute_code(
            code: str,
            language: str = "python",
            agent_name: Optional[str] = None
        ) -> CallToolResult:
            """Execute code using AG2's code execution capabilities."""
            try:
                # This is a simplified version - in practice you'd want to use
                # AG2's proper code execution environment
                if language.lower() == "python":
                    # For safety, we'll just return what would be executed
                    # In a real implementation, you'd use AG2's CodeExecutor
                    result = f"Code would be executed:\n```python\n{code}\n```"
                else:
                    result = f"Unsupported language: {language}. Supported: python"
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=result
                    )]
                )
                
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Error executing code: {str(e)}"
                    )],
                    isError=True
                )
        
        @self.server.call_tool()
        async def save_memory(
            key: str,
            content: Any,
            context: str = "general"
        ) -> CallToolResult:
            """Save content to the memory store."""
            memory_key = f"{context}:{key}"
            self.memory_store[memory_key] = {
                "content": content,
                "context": context,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Saved to memory: {memory_key}"
                )]
            )
        
        @self.server.call_tool()
        async def retrieve_memory(
            key: str,
            context: str = "general"
        ) -> CallToolResult:
            """Retrieve content from the memory store."""
            memory_key = f"{context}:{key}"
            if memory_key in self.memory_store:
                content = self.memory_store[memory_key]
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Retrieved from memory: {json.dumps(content, indent=2)}"
                    )]
                )
            else:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"No content found for key: {memory_key}"
                    )]
                )
    
    def _register_resources(self):
        """Register AG2 resources accessible via MCP."""
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available AG2 resources."""
            resources = [
                Resource(
                    uri="ag2://agents",
                    name="AG2 Agents",
                    description="List of all created AG2 agents",
                    mimeType="application/json"
                ),
                Resource(
                    uri="ag2://conversations", 
                    name="Conversations",
                    description="All active conversations and chat logs",
                    mimeType="application/json"
                ),
                Resource(
                    uri="ag2://memory",
                    name="Memory Store",
                    description="Content stored in the memory engine",
                    mimeType="application/json"
                )
            ]
            return ListResourcesResult(resources=resources)
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read AG2 resource content."""
            if uri == "ag2://agents":
                content = {
                    "agents": {
                        name: {
                            "name": agent.name,
                            "system_message": getattr(agent, "system_message", ""),
                            "human_input_mode": getattr(agent, "human_input_mode", "NEVER")
                        }
                        for name, agent in self.agents.items()
                    }
                }
            elif uri == "ag2://conversations":
                content = {"conversations": self.active_conversations}
            elif uri == "ag2://memory":
                content = {"memory": self.memory_store}
            else:
                return ReadResourceResult(
                    contents=[TextContent(
                        type="text",
                        text=f"Unknown resource: {uri}"
                    )]
                )
            
            return ReadResourceResult(
                contents=[TextContent(
                    type="text",
                    text=json.dumps(content, indent=2)
                )]
            )
    
    def _register_prompts(self):
        """Register AG2 prompt templates."""
        
        @self.server.list_prompts()
        async def list_prompts() -> ListPromptsResult:
            """List available AG2 prompt templates."""
            # This would include common AG2 prompt patterns
            return ListPromptsResult(prompts=[])
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Optional[Dict[str, str]] = None) -> GetPromptResult:
            """Get AG2 prompt template."""
            # This would return formatted prompt templates
            return GetPromptResult(
                description=f"AG2 prompt template: {name}",
                messages=[]
            )
    
    async def run_stdio(self):
        """Run the server using stdio transport."""
        try:
            from mcp.server.stdio import stdio_server
            
            async with stdio_server() as streams:
                await self.server.run(
                    streams[0], streams[1],
                    init_options={"server_name": self.name}
                )
        except ImportError:
            print("MCP stdio server not available")
            sys.exit(1)
    
    async def run_sse(self, host: str = "localhost", port: int = 8765):
        """Run the server using SSE transport."""
        try:
            from mcp.server.sse import sse_server
            
            async with sse_server(host, port) as server:
                await self.server.run_sse(server)
        except ImportError:
            print("MCP SSE server not available")
            sys.exit(1)


async def main():
    """Main entry point for the AG2 MCP server."""
    if len(sys.argv) < 2:
        print("Usage: python ag2_mcp_server.py [stdio|sse] [--port PORT]")
        sys.exit(1)
    
    transport = sys.argv[1].lower()
    server = AG2MCPServer()
    
    if transport == "stdio":
        await server.run_stdio()
    elif transport == "sse":
        port = 8765
        if "--port" in sys.argv:
            try:
                port_idx = sys.argv.index("--port") + 1
                port = int(sys.argv[port_idx])
            except (IndexError, ValueError):
                print("Invalid port specified")
                sys.exit(1)
        
        print(f"Starting AG2 MCP server on http://localhost:{port}/sse")
        await server.run_sse(port=port)
    else:
        print(f"Unknown transport: {transport}. Use 'stdio' or 'sse'")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())