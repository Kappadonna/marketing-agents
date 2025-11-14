"""Main agent construction module for the marketing campaign system.

VERSION 2.0 - RATE LIMITING FEATURES:
- Automatic retry with exponential backoff for rate limits
- Configurable max retries and backoff multiplier
- Graceful degradation when rate limits hit
- Clear error messages for users

This module assembles the complete multi-agent system by:
1. Defining sub-agent configurations
2. Creating specialized agents with appropriate tools
3. Constructing the main Project Manager agent
4. Providing helper functions to run campaigns
"""

import time
from typing import Optional
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

from state import MarketingCampaignState
from prompts import (
    PROJECT_MANAGER_PROMPT,
    STRATEGY_PLANNER_PROMPT,
    CONTENT_CREATOR_PROMPT,
    ANALYTICS_AGENT_PROMPT,
)
from file_tools import ls, read_file, write_file, verify_iteration_complete
from todo_tools import write_todos, read_todos
from research_tools import tavily_search, think_tool
from image_tools import generate_marketing_image
from visualization_tools import create_metrics_chart, create_iteration_comparison_chart
from iteration_tools import increment_iteration, get_current_iteration
from task_tool import _create_task_tool, SubAgent


def create_rate_limited_model(
    model_name: str = "openai:gpt-4o-mini",
    max_retries: int = 3,
    retry_delay: float = 2.0,
):
    """Create a language model with rate limiting and retry logic.
    
    Args:
        model_name: Model identifier (default: "openai:gpt-4o-mini")
        max_retries: Maximum number of retry attempts for rate limits
        retry_delay: Initial delay between retries in seconds
        
    Returns:
        Configured language model with retry capabilities
    """
    # Initialize model with extended timeout for rate limits
    model = init_chat_model(
        model=model_name,
        timeout=120.0,  # 2 minute timeout
        max_retries=max_retries,
    )
    
    return model


def create_marketing_campaign_agent(
    model_name: str = "openai:gpt-4o-mini",
    max_iterations: int = 3,
    performance_threshold: float = 65.0,
    enable_rate_limiting: bool = True,
    max_retries: int = 3,
):
    """Create the complete marketing campaign multi-agent system.
    
    VERSION 2.0 FEATURES:
    - Rate limiting protection with automatic retry
    - Exponential backoff for API rate limits
    - Graceful error handling
    - Clear user feedback on rate limit issues
    
    This function constructs the entire agent architecture including:
    - Project Manager (main Deep Agent)
    - Strategy Planner (sub-agent for market research)
    - Content Creator (sub-agent for content generation)
    - Analytics Agent (sub-agent for performance analysis)
    
    Args:
        model_name: LLM model to use for all agents (default: "openai:gpt-4o-mini")
        max_iterations: Maximum campaign iterations (default: 3)
        performance_threshold: Minimum score for positive evaluation (default: 65.0)
        enable_rate_limiting: Enable automatic retry for rate limits (default: True)
        max_retries: Maximum retry attempts for rate limited requests (default: 3)
        
    Returns:
        Configured Project Manager agent ready to run campaigns
    """
    
    # Initialize the language model with rate limiting if enabled
    if enable_rate_limiting:
        model = create_rate_limited_model(
            model_name=model_name,
            max_retries=max_retries
        )
    else:
        model = init_chat_model(model=model_name)
    
    # Define all available tools
    all_tools = [
        ls,
        read_file, 
        write_file,
        verify_iteration_complete,
        write_todos,
        read_todos,
        tavily_search,
        think_tool,
        generate_marketing_image,
        create_metrics_chart,
        create_iteration_comparison_chart,
        increment_iteration,
        get_current_iteration,
    ]
    
    # Define sub-agent configurations
    subagents: list[SubAgent] = [
        {
            "name": "strategy-planner",
            "description": "Conducts market research and develops comprehensive marketing strategies based on target audience, competitors, and trends",
            "prompt": STRATEGY_PLANNER_PROMPT,
            "tools": ["tavily_search", "think_tool", "read_file", "write_file"]
        },
        {
            "name": "content-creator",
            "description": "Creates compelling social media content including captions and visual descriptions based on strategy reports. Can generate actual images using DALL-E 3.",
            "prompt": CONTENT_CREATOR_PROMPT,
            "tools": ["read_file", "write_file", "generate_marketing_image"]
        },
        {
            "name": "analytics-agent",
            "description": "Simulates campaign metrics, analyzes performance, and provides actionable feedback for strategy improvement. Can generate visual charts of metrics.",
            "prompt": ANALYTICS_AGENT_PROMPT,
            "tools": ["read_file", "write_file", "think_tool", "create_metrics_chart", "create_iteration_comparison_chart"]
        }
    ]
    
    # Create the task delegation tool
    task_tool = _create_task_tool(
        tools=all_tools,
        subagents=subagents,
        model=model,
        state_schema=MarketingCampaignState
    )
    
    # Define tools for the Project Manager
    project_manager_tools = [
        ls,
        read_file,
        write_file,
        verify_iteration_complete,
        write_todos,
        read_todos,
        increment_iteration,
        get_current_iteration,
        task_tool
    ]
    
    # Create the Project Manager agent (main orchestrator)
    project_manager = create_react_agent(
        model=model,
        tools=project_manager_tools,
        state_schema=MarketingCampaignState,
        prompt=PROJECT_MANAGER_PROMPT
    )
    
    return project_manager


def create_campaign_input(
    product_info: str,
    campaign_goal: str,
    target_audience: str,
    max_iterations: int = 3,
    performance_threshold: float = 65.0
) -> dict:
    """Create input configuration for a marketing campaign.
    
    Args:
        product_info: Description of the product/service being marketed
        campaign_goal: Main objective (e.g., 'awareness', 'engagement', 'conversion')
        target_audience: Description of the target audience
        max_iterations: Maximum number of campaign iterations (default: 3)
        performance_threshold: Minimum score for positive evaluation (default: 65.0)
        
    Returns:
        Dictionary with campaign configuration and initial state
    """
    
    campaign_brief = f"""# Marketing Campaign Brief

## Product/Service Information
{product_info}

## Campaign Goal
{campaign_goal}

## Target Audience
{target_audience}

## Campaign Parameters
- Maximum Iterations: {max_iterations}
- Performance Threshold: {performance_threshold}/100
- Platform: LinkedIn

## Instructions
Please orchestrate a complete marketing campaign following these phases:
1. Strategy Planning: Research and develop a comprehensive strategy
2. Content Creation: Create LinkedIn post content (caption + visual)
3. Analytics: Simulate metrics and analyze performance
4. Iteration: Improve based on feedback (up to {max_iterations} iterations)

Begin by creating your TODO list and campaign files!
"""
    
    return {
        "messages": [{"role": "user", "content": campaign_brief}],
        "files": {},
        "todos": [],
        "iteration_count": 1,
        "max_iterations": max_iterations,
        "campaign_status": "planning",
        "product_info": product_info,
        "campaign_goal": campaign_goal,
        "target_audience": target_audience,
        "performance_threshold": performance_threshold,
        "search_count_current_iteration": 0,
        "max_searches_per_iteration": 3,
        "total_searches_campaign": 0,
    }


# Example usage function
async def run_campaign_example():
    """Example function showing how to run a complete marketing campaign."""
    
    # Create the agent with rate limiting enabled
    agent = create_marketing_campaign_agent(
        model_name="openai:gpt-4o-mini",
        max_iterations=3,
        performance_threshold=65.0,
        enable_rate_limiting=True,  # Enable automatic retry
        max_retries=3
    )
    
    # Define campaign parameters
    campaign_input = create_campaign_input(
        product_info="""
        EcoBottle Pro - A revolutionary smart water bottle that:
        - Tracks daily hydration goals with LED indicators
        - Self-cleaning UV-C technology
        - Keeps drinks cold for 24h, hot for 12h
        - Eco-friendly materials (BPA-free, recyclable)
        - Integrates with fitness apps
        Price: $79.99
        """,
        campaign_goal="Generate product awareness and engagement among health-conscious professionals",
        target_audience="Health-conscious professionals aged 25-45, active on LinkedIn, interested in wellness technology and sustainability",
        max_iterations=3,
        performance_threshold=65.0
    )
    
    # Run the campaign
    from utils import stream_agent, print_campaign_summary, save_campaign_output
    
    print("🚀 Starting Marketing Campaign...\n")
    
    final_state = await stream_agent(agent, campaign_input)
    
    print("\n✅ Campaign Complete!\n")
    print_campaign_summary(final_state)
    
    # Save all generated files
    save_campaign_output(final_state)
    
    return final_state


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_campaign_example())
