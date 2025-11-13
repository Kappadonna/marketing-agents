"""State management for marketing campaign multi-agent system.

This module defines the agent state structure that supports:
- Task planning and progress tracking through TODO lists
- Context offloading through a virtual file system stored in state
- Campaign iteration tracking and status management
- Efficient state merging with reducer functions
"""

from typing import Annotated, Literal, NotRequired
from typing_extensions import TypedDict

from langgraph.prebuilt.chat_agent_executor import AgentState


class Todo(TypedDict):
    """A structured task item for tracking progress through complex workflows.

    Attributes:
        content: Short, specific description of the task
        status: Current state - pending, in_progress, or completed
    """
    content: str
    status: Literal["pending", "in_progress", "completed"]


def file_reducer(left, right):
    """Merge two file dictionaries, with right side taking precedence.

    Used as a reducer function for the files field in agent state,
    allowing incremental updates to the virtual file system.

    Args:
        left: Left side dictionary (existing files)
        right: Right side dictionary (new/updated files)

    Returns:
        Merged dictionary with right values overriding left values
    """
    if left is None:
        return right
    elif right is None:
        return left
    else:
        return {**left, **right}


class MarketingCampaignState(AgentState):
    """Extended agent state for marketing campaign management.

    Inherits from LangGraph's AgentState and adds:
    - todos: List of Todo items for task planning and progress tracking
    - files: Virtual file system stored as dict mapping filenames to content
    - iteration_count: Current campaign iteration number
    - max_iterations: Maximum number of campaign iterations allowed
    - campaign_status: Current status of the campaign
    - product_info: Information about the product being marketed
    - campaign_goal: Main objective (awareness, engagement, conversion)
    - target_audience: Description of the target audience
    - performance_threshold: Minimum score for positive evaluation (0-100)
    """
    todos: NotRequired[list[Todo]]
    files: Annotated[NotRequired[dict[str, str]], file_reducer]
    iteration_count: NotRequired[int]
    max_iterations: NotRequired[int]
    campaign_status: NotRequired[Literal["planning", "strategy", "content_creation", "analysis", "completed", "failed"]]
    product_info: NotRequired[str]
    campaign_goal: NotRequired[str]
    target_audience: NotRequired[str]
    tool_generated_files: NotRequired[set[str]]
    performance_threshold: NotRequired[float]
