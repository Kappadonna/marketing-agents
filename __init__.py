"""Marketing Campaign Multi-Agent System.

This package implements an autonomous marketing campaign system using LangGraph
and the Deep Agents pattern. The system coordinates multiple specialized agents
to plan, execute, and optimize marketing campaigns through iterative feedback loops.

Architecture:
- Project Manager Agent: Orchestrates the entire campaign workflow
- Strategy Planner Agent: Conducts market research and develops strategies
- Content Creator Agent: Creates social media content (text and visuals)
- Analytics Agent: Simulates metrics and analyzes campaign performance

Key Features:
- TODO-based task tracking
- Virtual filesystem for context offloading
- Isolated sub-agent contexts to prevent context pollution
- Iterative improvement based on simulated performance feedback
"""

__version__ = "1.0.0"
