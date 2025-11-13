"""Iteration management tools for campaign workflow control.

This module provides tools for safely managing iteration counts and ensuring
proper state propagation across the multi-agent system.

VERSION 1.0 - Fixes iteration count propagation issues
"""

from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from state import MarketingCampaignState


@tool
def increment_iteration(
    state: Annotated[MarketingCampaignState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Increment the campaign iteration counter and update state.
    
    This tool safely increments the iteration_count in the campaign state,
    ensuring that all subsequent operations use the correct iteration number.
    
    Use this tool when:
    - Moving from one iteration to the next
    - After verify_iteration_complete confirms all files are present
    - Before delegating to strategy-planner for the next iteration
    
    Returns:
        Command with updated iteration_count and confirmation message
    """
    current = state.get("iteration_count", 1)
    max_iterations = state.get("max_iterations", 3)
    
    if current >= max_iterations:
        error_msg = f"""⚠️ Cannot increment: Already at maximum iterations

Current: {current}
Maximum: {max_iterations}

You should proceed to Phase 5 (Campaign Completion) instead of incrementing.
"""
        return Command(
            update={
                "messages": [ToolMessage(error_msg, tool_call_id=tool_call_id)]
            }
        )
    
    new_iteration = current + 1
    
    success_msg = f"""✅ Iteration incremented successfully

Previous iteration: {current}
New iteration: {new_iteration}
Maximum iterations: {max_iterations}
Remaining: {max_iterations - new_iteration}

🎯 Next steps:
1. Update iteration_log.md with completion note
2. Update TODOs to mark iteration {current} complete
3. Delegate to strategy-planner for iteration {new_iteration}

The iteration_count is now {new_iteration} and will be used by all sub-agents.
"""
    
    return Command(
        update={
            "iteration_count": new_iteration,
            "messages": [ToolMessage(success_msg, tool_call_id=tool_call_id)]
        }
    )


@tool
def get_current_iteration(
    state: Annotated[MarketingCampaignState, InjectedState],
) -> str:
    """Get the current iteration number and iteration status.
    
    Use this tool when you need to:
    - Check which iteration you're currently on
    - Verify before delegating to sub-agents
    - Confirm iteration count before file operations
    
    Returns:
        Detailed status of current iteration
    """
    current = state.get("iteration_count", 1)
    max_iterations = state.get("max_iterations", 3)
    campaign_status = state.get("campaign_status", "unknown")
    
    status_msg = f"""📊 Current Iteration Status

Iteration: {current} of {max_iterations}
Campaign Status: {campaign_status}
Progress: {(current / max_iterations) * 100:.1f}% complete

📁 Expected files for iteration {current}:
  - strategy_report_v{current}.md
  - post_content_v{current}.md
  - post_image_v{current}.md
  - post_image_data_v{current}.txt
  - analytics_report_v{current}.md
  - metrics_chart_v{current}.md
  - metrics_chart_data_v{current}.txt

Use this iteration number ({current}) when delegating to sub-agents.
"""
    
    return status_msg


__all__ = ['increment_iteration', 'get_current_iteration']