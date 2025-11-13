"""Task delegation tools for context isolation through sub-agents.

This module provides the core infrastructure for creating and managing sub-agents
with isolated contexts. Sub-agents prevent context clash by operating with clean
context windows containing only their specific task description.

FIXED VERSION - Added validation to prevent self-delegation errors
"""

from typing import Annotated, NotRequired
from typing_extensions import TypedDict

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState, create_react_agent
from langgraph.types import Command

from prompts import TASK_DESCRIPTION_PREFIX
from state import MarketingCampaignState


class SubAgent(TypedDict):
    """Configuration for a specialized sub-agent."""
    name: str
    description: str
    prompt: str
    tools: NotRequired[list[str]]


def _create_task_tool(tools, subagents: list[SubAgent], model, state_schema):
    """Create a task delegation tool that enables context isolation through sub-agents.

    This function implements the core pattern for spawning specialized sub-agents with
    isolated contexts, preventing context clash and confusion in complex multi-step tasks.

    Args:
        tools: List of available tools that can be assigned to sub-agents
        subagents: List of specialized sub-agent configurations
        model: The language model to use for all agents
        state_schema: The state schema (MarketingCampaignState)

    Returns:
        A 'task' tool that can delegate work to specialized sub-agents
    """
    # Create agent registry
    agents = {}

    # Build tool name mapping for selective tool assignment
    tools_by_name = {}
    for tool_ in tools:
        if not isinstance(tool_, BaseTool):
            tool_ = tool(tool_)
        tools_by_name[tool_.name] = tool_

    # Create specialized sub-agents based on configurations
    for _agent in subagents:
        if "tools" in _agent:
            # Use specific tools if specified
            _tools = [tools_by_name[t] for t in _agent["tools"]]
        else:
            # Default to all tools
            _tools = tools
        agents[_agent["name"]] = create_react_agent(
            model, 
            prompt=_agent["prompt"], 
            tools=_tools, 
            state_schema=state_schema
        )

    # Generate description of available sub-agents for the tool description
    other_agents_string = [
        f"- {_agent['name']}: {_agent['description']}" for _agent in subagents
    ]
    
    # NEW: Define constants for validation
    ALLOWED_AGENTS = list(agents.keys())
    CALLER_AGENT = "project-manager"  # This tool is only available to project manager

    @tool(description=TASK_DESCRIPTION_PREFIX.format(other_agents='\n'.join(other_agents_string)))
    def task(
        description: str,
        subagent_type: str,
        state: Annotated[MarketingCampaignState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        """Delegate a task to a specialized sub-agent with isolated context.

        This creates a fresh context for the sub-agent containing only the task description,
        preventing context pollution from the parent agent's conversation history.

        Args:
            description: Clear, specific task description for the sub-agent
            subagent_type: Type of agent to use (strategy-planner, content-creator, analytics-agent)
            state: Injected agent state
            tool_call_id: Injected tool call identifier

        Returns:
            Command with updated state including sub-agent results
        """
        
        # ================================================================
        # NEW VALIDATION: Prevent self-delegation
        # ================================================================
        if subagent_type == CALLER_AGENT:
            error_msg = f"""❌ DELEGATION ERROR: Self-delegation not allowed!

You attempted to delegate to: '{subagent_type}'
This is yourself! You cannot delegate tasks to yourself.

**Available agents for delegation:**
{chr(10).join(f'  ✅ {name}' for name in ALLOWED_AGENTS)}

**What to do:**
1. Identify which sub-agent should handle this task:
   - Strategy/Research tasks → 'strategy-planner'
   - Content/Image creation → 'content-creator'
   - Analytics/Metrics → 'analytics-agent'

2. Re-call the task tool with the correct agent name

3. Example:
   ❌ WRONG: task(description="...", subagent_type="project-manager")
   ✅ RIGHT: task(description="...", subagent_type="content-creator")

Please try again with one of the available sub-agent types listed above.
"""
            return Command(
                update={
                    "messages": [
                        ToolMessage(error_msg, tool_call_id=tool_call_id)
                    ]
                }
            )
        
        # ================================================================
        # EXISTING VALIDATION: Check agent exists
        # ================================================================
        if subagent_type not in agents:
            error_msg = f"""❌ AGENT NOT FOUND: Invalid agent type specified!

You tried to delegate to: '{subagent_type}'
This agent type does not exist in the system.

**Available agents:**
{chr(10).join(f'  ✅ {name}' for name in ALLOWED_AGENTS)}

**Common mistakes:**
- Typos in agent name (check spelling)
- Using 'project-manager' (you cannot delegate to yourself)
- Invalid agent type

Please use one of the available agent types listed above.
"""
            return Command(
                update={
                    "messages": [
                        ToolMessage(error_msg, tool_call_id=tool_call_id)
                    ]
                }
            )

        # Get the requested sub-agent
        sub_agent = agents[subagent_type]

        # Get current iteration to pass to sub-agent
        current_iteration = state.get("iteration_count", 1)
        
        # CRITICAL FIX: Add iteration context to task description
        # This ensures sub-agents always know which iteration they're working on
        enhanced_description = f"""**CURRENT ITERATION: {current_iteration}**

You are working on iteration {current_iteration} of the campaign.
All files you create MUST use the version number v{current_iteration}.

{description}

REMINDER: Use iteration {current_iteration} in all filenames (e.g., strategy_report_v{current_iteration}.md)
"""
        
        # Create isolated context with only the task description
        # This is the key to context isolation - no parent history
        isolated_state = {
            "messages": [{"role": "user", "content": enhanced_description}],
            "files": state.get("files", {}),  # Share filesystem
            "iteration_count": current_iteration,  # Share iteration info (explicit value)
            "campaign_goal": state.get("campaign_goal", ""),
            "target_audience": state.get("target_audience", ""),
            "product_info": state.get("product_info", ""),
        }

        # Execute the sub-agent in isolation
        result = sub_agent.invoke(isolated_state)

        # Return results to parent agent via Command state update
        return Command(
            update={
                "files": result.get("files", {}),  # Merge any file changes
                "messages": [
                    # Sub-agent result becomes a ToolMessage in parent context
                    ToolMessage(
                        result["messages"][-1].content, 
                        tool_call_id=tool_call_id
                    )
                ],
            }
        )

    return task