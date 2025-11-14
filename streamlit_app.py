"""
Marketing Campaign Multi-Agent System - Real-Time Streamlit Dashboard
======================================================================

VERSION 2.0 - REAL-TIME UPDATES
- Live agent activity monitoring
- Real-time task delegation visualization
- Progressive UI updates during campaign execution
- No UI blocking during long operations
"""

import os
import asyncio
import base64
import json
from datetime import datetime
from io import BytesIO
from typing import Dict, Any
import time

import streamlit as st
from dotenv import load_dotenv

# Import campaign modules
from agent import create_marketing_campaign_agent, create_campaign_input
from state import MarketingCampaignState
from campaign_examples import get_all_campaigns, get_campaign_config, CATEGORIES
from export_utils import (
    create_campaign_summary_md, 
    create_campaign_json,
    create_zip_archive,
    get_export_filename,
    create_html_report
)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Marketing Campaign Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS - Enhanced for Real-Time Updates
# ============================================================================

st.markdown("""
<style>
    /* Main theme */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Cards */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85em;
    }
    
    .status-planning { background: #fff3cd; color: #856404; }
    .status-strategy { background: #d1ecf1; color: #0c5460; }
    .status-content_creation { background: #d4edda; color: #155724; }
    .status-analysis { background: #cce5ff; color: #004085; }
    .status-completed { background: #d4edda; color: #155724; }
    .status-failed { background: #f8d7da; color: #721c24; }
    .status-running { background: #e7f3ff; color: #0066cc; }
    
    /* Agent activity indicators */
    .agent-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    
    .agent-active {
        border-color: #28a745;
        box-shadow: 0 0 20px rgba(40, 167, 69, 0.4);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(40, 167, 69, 0.4); }
        50% { box-shadow: 0 0 30px rgba(40, 167, 69, 0.6); }
    }
    
    .agent-idle {
        border-color: #6c757d;
        opacity: 0.7;
    }
    
    /* Live event feed */
    .event-item {
        background: white;
        padding: 10px 15px;
        border-left: 4px solid #667eea;
        margin: 5px 0;
        border-radius: 5px;
        animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .event-delegation { border-left-color: #667eea; }
    .event-task { border-left-color: #28a745; }
    .event-completion { border-left-color: #ffc107; }
    .event-error { border-left-color: #dc3545; }
    
    /* Progress indicators */
    .progress-container {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Iteration box */
    .iteration-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    
    /* Live indicator */
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 5px 15px;
        background: #ff4444;
        color: white;
        border-radius: 20px;
        font-weight: 600;
        animation: blink 1.5s infinite;
    }
    
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: white;
        border-radius: 50%;
        animation: pulse-dot 1.5s infinite;
    }
    
    @keyframes pulse-dot {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.3); }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

@st.cache_resource
def setup_environment():
    """Setup environment variables and API keys"""
    load_dotenv()
    
    # Try Streamlit secrets if .env not available
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    if "TAVILY_API_KEY" in st.secrets:
        os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]
    
    # Verify keys exist
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ Missing OPENAI_API_KEY - check .env or Streamlit Secrets")
        st.stop()
    if not os.getenv("TAVILY_API_KEY"):
        st.error("❌ Missing TAVILY_API_KEY - check .env or Streamlit Secrets")
        st.stop()
    
    return True

setup_environment()

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'campaign_running': False,
        'campaign_state': None,
        'agent': None,
        'logs': [],
        'events': [],  # NEW: Real-time events
        'active_agent': None,  # NEW: Currently active agent
        'current_task': None,  # NEW: Current task description
        'agent_status': {  # NEW: Status of each agent
            'project-manager': 'idle',
            'strategy-planner': 'idle',
            'content-creator': 'idle',
            'analytics-agent': 'idle'
        },
        'template_config': {},
        'iteration_files': {},  # NEW: Track files by iteration
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# REAL-TIME EVENT SYSTEM
# ============================================================================

def add_event(event_type: str, agent: str, message: str, details: Dict[str, Any] = None):
    """Add a real-time event to the event log
    
    Args:
        event_type: Type of event (delegation, task, completion, error)
        agent: Agent performing the action
        message: Human-readable message
        details: Additional event details
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    event = {
        "time": timestamp,
        "type": event_type,
        "agent": agent,
        "message": message,
        "details": details or {}
    }
    st.session_state.events.insert(0, event)  # Insert at beginning for newest first
    
    # Keep only last 100 events to prevent memory issues
    st.session_state.events = st.session_state.events[:100]

def set_active_agent(agent_name: str, task: str = None):
    """Set the currently active agent and update status
    
    Args:
        agent_name: Name of the agent
        task: Description of current task
    """
    st.session_state.active_agent = agent_name
    st.session_state.current_task = task
    st.session_state.agent_status[agent_name] = 'active'

def set_agent_idle(agent_name: str):
    """Set an agent to idle status"""
    st.session_state.agent_status[agent_name] = 'idle'
    if st.session_state.active_agent == agent_name:
        st.session_state.active_agent = None
        st.session_state.current_task = None

def add_log(message: str, level: str = "info"):
    """Add a log message to the session state"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append({
        "time": timestamp,
        "level": level,
        "message": message
    })

# ============================================================================
# CAMPAIGN EXECUTION WITH REAL-TIME UPDATES
# ============================================================================

async def stream_campaign_execution(agent, campaign_input, config, 
                                   progress_container, 
                                   event_container,
                                   agent_container):
    """Execute campaign with real-time streaming updates
    
    This function streams the campaign execution and updates the UI
    in real-time using dynamic containers.
    
    Args:
        agent: The campaign agent
        campaign_input: Campaign configuration
        config: LangGraph config
        progress_container: Streamlit container for progress updates
        event_container: Streamlit container for event feed
        agent_container: Streamlit container for agent status
    """
    try:
        # Initial setup
        add_event("delegation", "project-manager", "🚀 Campaign started", {
            "max_iterations": campaign_input.get('max_iterations', 3),
            "threshold": campaign_input.get('performance_threshold', 75)
        })
        
        set_active_agent("project-manager", "Initializing campaign workflow")
        
        # Stream through agent execution
        async for graph_name, stream_mode, event in agent.astream(
            campaign_input,
            stream_mode=["updates", "values"], 
            subgraphs=True,
            config=config
        ):
            if stream_mode == "updates":
                node, result = list(event.items())[0]
                
                # Determine which agent is active
                agent_name = "project-manager"  # Default
                if "strategy" in node.lower():
                    agent_name = "strategy-planner"
                elif "content" in node.lower():
                    agent_name = "content-creator"
                elif "analytics" in node.lower():
                    agent_name = "analytics-agent"
                
                # Extract message content
                messages = result.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    
                    # Check for tool calls (delegation events)
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        for tool_call in last_message.tool_calls:
                            if tool_call['name'] == 'task':
                                # Delegation event
                                args = tool_call.get('args', {})
                                target_agent = args.get('subagent_type', 'unknown')
                                task_desc = args.get('description', '')[:100]
                                
                                add_event("delegation", agent_name, 
                                        f"📤 Delegating to {target_agent}", {
                                            "target": target_agent,
                                            "task_preview": task_desc
                                        })
                                
                                set_active_agent(target_agent, task_desc)
                            
                            elif tool_call['name'] in ['write_file', 'generate_marketing_image', 
                                                      'create_metrics_chart', 'verify_iteration_complete']:
                                # Task execution event
                                add_event("task", agent_name, 
                                        f"⚙️ Executing: {tool_call['name']}", {
                                            "tool": tool_call['name']
                                        })
                    
                    # Check for tool results (completion events)
                    if hasattr(last_message, 'content') and last_message.content:
                        content_str = str(last_message.content)
                        
                        # Check for completion indicators
                        if "✅" in content_str or "complete" in content_str.lower():
                            add_event("completion", agent_name, 
                                    "✅ Task completed successfully", {})
                            set_agent_idle(agent_name)
                        
                        # Check for errors
                        elif "❌" in content_str or "error" in content_str.lower():
                            add_event("error", agent_name, 
                                    "⚠️ Task encountered an issue", {})
                
                # Update state
                st.session_state.campaign_state = result
                
                # Update UI containers
                with progress_container:
                    render_live_progress()
                
                with event_container:
                    render_event_feed()
                
                with agent_container:
                    render_live_agent_status()
                
                # Small delay to allow UI to update
                await asyncio.sleep(0.1)
            
            # Capture final state
            if stream_mode == "values" and len(graph_name) == 0:
                st.session_state.campaign_state = event
        
        # Campaign completed
        add_event("completion", "project-manager", "🎉 Campaign completed successfully", {
            "iterations": st.session_state.campaign_state.get('iteration_count', 0),
            "files": len(st.session_state.campaign_state.get('files', {}))
        })
        
        set_agent_idle("project-manager")
        st.session_state.campaign_running = False
        
        return st.session_state.campaign_state
        
    except Exception as e:
        add_event("error", "system", f"❌ Campaign failed: {str(e)}", {})
        add_log(f"Campaign error: {str(e)}", "error")
        st.session_state.campaign_running = False
        raise

# ============================================================================
# REAL-TIME VISUALIZATION COMPONENTS
# ============================================================================

def render_live_progress():
    """Render live progress indicators"""
    if not st.session_state.campaign_state:
        st.info("⏳ Waiting for campaign to start...")
        return
    
    current = st.session_state.campaign_state.get('iteration_count', 0)
    max_iter = st.session_state.campaign_state.get('max_iterations', 3)
    status = st.session_state.campaign_state.get('campaign_status', 'unknown')
    
    # Iteration progress
    st.markdown(f"""
    <div class="iteration-box">
        <h2 style="margin: 0;">Iteration {current} of {max_iter}</h2>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">
            Status: {status.replace('_', ' ').title()}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(current / max_iter if max_iter > 0 else 0)
    
    # Live metrics
    files = st.session_state.campaign_state.get('files', {})
    todos = st.session_state.campaign_state.get('todos', [])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Files Generated", len(files))
    
    with col2:
        completed = len([t for t in todos if t.get('status') == 'completed'])
        st.metric("Tasks", f"{completed}/{len(todos)}")
    
    with col3:
        events_count = len(st.session_state.events)
        st.metric("Events", events_count)

def render_live_agent_status():
    """Render real-time agent activity status"""
    st.markdown("### 🤖 Agent Activity")
    
    if st.session_state.campaign_running:
        st.markdown('<div class="live-indicator"><div class="live-dot"></div>LIVE</div>', 
                   unsafe_allow_html=True)
    
    # Current task
    if st.session_state.current_task:
        st.info(f"**Current Task:** {st.session_state.current_task[:150]}...")
    
    # Agent cards
    agents_info = {
        'project-manager': {
            'name': '🎯 Project Manager',
            'role': 'Orchestrates workflow'
        },
        'strategy-planner': {
            'name': '📊 Strategy Planner',
            'role': 'Market research & strategy'
        },
        'content-creator': {
            'name': '✍️ Content Creator',
            'role': 'Content & visuals'
        },
        'analytics-agent': {
            'name': '📈 Analytics Agent',
            'role': 'Performance analysis'
        }
    }
    
    for agent_key, agent_info in agents_info.items():
        status = st.session_state.agent_status.get(agent_key, 'idle')
        is_active = status == 'active'
        
        status_class = "agent-active" if is_active else "agent-idle"
        status_emoji = "🟢" if is_active else "⚪"
        
        st.markdown(f"""
        <div class="agent-card {status_class}">
            <strong>{agent_info['name']}</strong> {status_emoji}<br>
            <small style="color: #6c757d;">{agent_info['role']}</small><br>
            <small><strong>Status:</strong> {status.upper()}</small>
        </div>
        """, unsafe_allow_html=True)

def render_event_feed():
    """Render real-time event feed"""
    st.markdown("### 📡 Live Event Feed")
    
    if not st.session_state.events:
        st.info("No events yet. Events will appear here in real-time.")
        return
    
    # Show last 20 events
    for event in st.session_state.events[:20]:
        event_class = f"event-{event['type']}"
        
        icon_map = {
            'delegation': '📤',
            'task': '⚙️',
            'completion': '✅',
            'error': '❌'
        }
        icon = icon_map.get(event['type'], '•')
        
        st.markdown(f"""
        <div class="event-item {event_class}">
            <strong>[{event['time']}]</strong> {icon} <strong>{event['agent']}</strong><br>
            {event['message']}
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# STANDARD VISUALIZATION COMPONENTS (Same as before)
# ============================================================================

def render_campaign_header():
    """Render the main campaign header"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🚀 Marketing Campaign Dashboard")
        st.caption("Multi-Agent System with Real-Time Monitoring")
    
    with col2:
        if st.session_state.campaign_state:
            status = st.session_state.campaign_state.get('campaign_status', 'unknown')
            status_badge = f'<span class="status-badge status-{status}">{status.replace("_", " ").upper()}</span>'
            st.markdown(status_badge, unsafe_allow_html=True)
    
    with col3:
        if st.session_state.campaign_running:
            st.markdown('<div class="live-indicator"><div class="live-dot"></div>ACTIVE</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown("⚪ **IDLE**")

def render_iteration_progress():
    """Render iteration progress indicator"""
    if not st.session_state.campaign_state:
        return
    
    current = st.session_state.campaign_state.get('iteration_count', 0)
    max_iter = st.session_state.campaign_state.get('max_iterations', 3)
    
    st.markdown(f"""
    <div class="iteration-box">
        <h2 style="margin: 0;">Iteration {current} of {max_iter}</h2>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">
            Progress: {int((current / max_iter) * 100)}%
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(current / max_iter if max_iter > 0 else 0)

def render_metrics_overview():
    """Render key metrics overview"""
    if not st.session_state.campaign_state:
        st.info("📊 No campaign data available yet")
        return
    
    files = st.session_state.campaign_state.get('files', {})
    todos = st.session_state.campaign_state.get('todos', [])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Files Generated", len(files))
    
    with col2:
        completed_todos = len([t for t in todos if t.get('status') == 'completed'])
        st.metric("Tasks Completed", f"{completed_todos}/{len(todos)}")
    
    with col3:
        strategy_files = len([f for f in files.keys() if 'strategy' in f])
        st.metric("Strategy Reports", strategy_files)
    
    with col4:
        content_files = len([f for f in files.keys() if 'post_content' in f])
        st.metric("Content Pieces", content_files)

def render_todos():
    """Render TODO list"""
    st.markdown("### ✅ Tasks")
    
    if not st.session_state.campaign_state:
        st.info("No tasks yet")
        return
    
    todos = st.session_state.campaign_state.get('todos', [])
    
    if not todos:
        st.info("No tasks in the list")
        return
    
    for todo in todos:
        status_emoji = {
            "pending": "⏳",
            "in_progress": "🔄", 
            "completed": "✅"
        }
        emoji = status_emoji.get(todo.get("status", "pending"), "❓")
        
        st.markdown(f"{emoji} {todo.get('content', 'Unknown task')}")

def render_agent_status():
    """Render agent status cards"""
    st.markdown("### 🤖 Agent Status")
    
    agents = [
        {"name": "Project Manager", "icon": "🎯", "role": "Orchestration"},
        {"name": "Strategy Planner", "icon": "📊", "role": "Research & Strategy"},
        {"name": "Content Creator", "icon": "✍️", "role": "Content & Images"},
        {"name": "Analytics Agent", "icon": "📈", "role": "Performance Analysis"}
    ]
    
    cols = st.columns(2)
    for idx, agent in enumerate(agents):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="agent-card">
                <h4 style="margin: 0;">{agent['icon']} {agent['name']}</h4>
                <p style="margin: 5px 0; color: #6c757d;">{agent['role']}</p>
            </div>
            """, unsafe_allow_html=True)

def render_files_by_iteration():
    """Render files organized by iteration"""
    st.markdown("### 📁 Generated Files")
    
    if not st.session_state.campaign_state:
        st.info("No files yet")
        return
    
    files = st.session_state.campaign_state.get('files', {})
    
    if not files:
        st.info("No files generated yet")
        return
    
    # Organize files by iteration
    iterations = {}
    other_files = []
    
    for filename in sorted(files.keys()):
        if '_v' in filename and not filename.startswith('URL_error'):
            try:
                iter_num = int(filename.split('_v')[1].split('.')[0])
                if iter_num not in iterations:
                    iterations[iter_num] = []
                iterations[iter_num].append(filename)
            except:
                other_files.append(filename)
        elif not filename.startswith('URL_error'):
            other_files.append(filename)
    
    # Display by iteration
    for iter_num in sorted(iterations.keys()):
        with st.expander(f"📂 Iteration {iter_num} ({len(iterations[iter_num])} files)", expanded=True):
            for filename in sorted(iterations[iter_num]):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"📄 {filename}")
                with col2:
                    if st.button(f"👁️ View", key=f"view_{filename}"):
                        st.text_area("File Content", files[filename], height=200)
    
    # Other files
    if other_files:
        with st.expander(f"📂 Other Files ({len(other_files)})", expanded=True):
            for filename in sorted(other_files):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"📄 {filename}")
                with col2:
                    if st.button(f"👁️ View", key=f"view_{filename}"):
                        st.text_area("File Content", files[filename], height=200)

def render_campaign_images():
    """Render generated campaign images"""
    st.markdown("### 🖼️ Generated Images")
    
    if not st.session_state.campaign_state:
        st.info("No images yet")
        return
    
    files = st.session_state.campaign_state.get('files', {})
    
    # Find image data files
    image_files = [f for f in files.keys() if '_data.txt' in f and 'image' in f.lower()]
    
    if not image_files:
        st.info("No images generated yet")
        return
    
    for img_file in sorted(image_files):
        try:
            iter_num = img_file.split('_v')[1].split('.')[0] if '_v' in img_file else "unknown"
            
            st.markdown(f"**Iteration {iter_num}**")
            
            # Try to decode and display
            content = files[img_file]
            lines = content.split('\n')
            b64_data = None
            
            for line in lines:
                line = line.strip()
                if len(line) > 1000:
                    b64_data = line
                    break
            
            if b64_data:
                img_bytes = base64.b64decode(b64_data)
                st.image(img_bytes, caption=f"Generated Image - Iteration {iter_num}", use_column_width=True)
            else:
                st.warning(f"Could not decode image from {img_file}")
                
        except Exception as e:
            st.error(f"Error displaying {img_file}: {e}")

def render_logs():
    """Render system logs"""
    st.markdown("### 📝 System Logs")
    
    if not st.session_state.logs:
        st.info("No logs yet")
        return
    
    for log in reversed(st.session_state.logs[-50:]):  # Show last 50
        level_color = {
            "info": "blue",
            "warning": "orange",
            "error": "red",
            "success": "green"
        }
        color = level_color.get(log['level'], "gray")
        
        st.markdown(f"**[{log['time']}]** :{color}[{log['level'].upper()}] {log['message']}")

# ============================================================================
# SIDEBAR - CAMPAIGN CONFIGURATION
# ============================================================================

with st.sidebar:
    st.header("⚙️ Campaign Configuration")
    
    # Template selection
    st.subheader("📋 Campaign Templates")
    
    category = st.selectbox(
        "Category",
        options=list(CATEGORIES.keys()),
        index=0
    )
    
    campaign_options = CATEGORIES[category]
    selected_campaign = st.selectbox(
        "Select Template",
        options=campaign_options,
        index=0
    )
    
    if st.button("📥 Load Template"):
        config = get_campaign_config(selected_campaign)
        st.session_state.template_config = config
        st.success(f"✅ Loaded: {selected_campaign}")
        st.rerun()
    
    st.divider()
    
    # Model selection
    st.subheader("🤖 Model Settings")
    
    model_choice = st.selectbox(
        "LLM Model",
        options=[
            "openai:gpt-4o-mini",
            "openai:gpt-4o",
            "openai:gpt-4-turbo"
        ],
        index=0,
        help="gpt-4o-mini is faster and cheaper, gpt-4o is more capable"
    )
    
    max_iterations = st.slider(
        "Max Iterations",
        min_value=1,
        max_value=5,
        value=2,
        help="Maximum number of campaign iterations"
    )
    
    performance_threshold = st.slider(
        "Performance Threshold",
        min_value=50.0,
        max_value=95.0,
        value=75.0,
        step=5.0,
        help="Minimum score to consider iteration successful"
    )
    
    st.divider()
    
    # Product information
    st.subheader("📦 Product Details")
    
    template = st.session_state.get('template_config', {})
    
    product_name = st.text_input(
        "Product Name",
        value=template.get('product_name', "NeuroBuds Pro"),
        help="Name of the product/service"
    )
    
    product_info = st.text_area(
        "Product Description",
        value=template.get('product_info', """Next-generation wireless earbuds featuring:
- AI adaptive noise cancellation
- Focus Mode for productivity
- Real-time translation
- 48h battery life
Price: €249.99"""),
        height=200,
        help="Detailed product information"
    )
    
    campaign_goal = st.text_area(
        "Campaign Goal",
        value=template.get('campaign_goal', "Generate pre-orders and build anticipation for product launch"),
        height=100,
        help="Main objective of the campaign"
    )
    
    target_audience = st.text_area(
        "Target Audience",
        value=template.get('target_audience', "Tech enthusiasts aged 25-40, professionals seeking productivity tools"),
        height=120,
        help="Description of target audience"
    )
    
    st.divider()
    
    # Start/Stop buttons
    col1, col2 = st.columns(2)
    
    with col1:
        start_disabled = st.session_state.campaign_running
        if st.button("🚀 START", use_container_width=True, disabled=start_disabled, type="primary"):
            # Initialize
            add_log("Initializing agent system...", "info")
            
            st.session_state.agent = create_marketing_campaign_agent(
                model_name=model_choice,
                max_iterations=max_iterations,
                performance_threshold=performance_threshold
            )
            
            campaign_input = create_campaign_input(
                product_info=f"{product_name}\n\n{product_info}",
                campaign_goal=campaign_goal,
                target_audience=target_audience,
                max_iterations=max_iterations,
                performance_threshold=performance_threshold
            )
            
            st.session_state.campaign_running = True
            st.session_state.events = []
            
            add_log("Campaign started", "success")
            st.rerun()
    
    with col2:
        stop_disabled = not st.session_state.campaign_running
        if st.button("⏹️ STOP", use_container_width=True, disabled=stop_disabled):
            st.session_state.campaign_running = False
            add_event("error", "system", "⏹️ Campaign stopped by user", {})
            add_log("Campaign stopped by user", "warning")
            st.rerun()
    
    # Clear button
    if st.button("🗑️ Clear All", use_container_width=True):
        for key in ['campaign_state', 'logs', 'events', 'active_agent', 'current_task']:
            st.session_state[key] = None if key in ['campaign_state', 'active_agent', 'current_task'] else []
        st.session_state.campaign_running = False
        st.session_state.agent_status = {
            'project-manager': 'idle',
            'strategy-planner': 'idle',
            'content-creator': 'idle',
            'analytics-agent': 'idle'
        }
        add_log("Dashboard cleared", "info")
        st.rerun()

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

# Header
render_campaign_header()

st.divider()

# ============================================================================
# REAL-TIME EXECUTION AREA (NEW)
# ============================================================================

if st.session_state.campaign_running and st.session_state.agent:
    st.markdown("## 📡 Live Campaign Execution")
    
    # Create dynamic containers
    col1, col2 = st.columns([2, 1])
    
    with col1:
        progress_placeholder = st.empty()
        event_placeholder = st.empty()
    
    with col2:
        agent_placeholder = st.empty()
    
    # Run campaign with real-time updates
    config = {"recursion_limit": 200}
    
    campaign_input = create_campaign_input(
        product_info=f"{product_name}\n\n{product_info}",
        campaign_goal=campaign_goal,
        target_audience=target_audience,
        max_iterations=max_iterations,
        performance_threshold=performance_threshold
    )
    
    # Execute with streaming
    try:
        final_state = asyncio.run(
            stream_campaign_execution(
                st.session_state.agent,
                campaign_input,
                config,
                progress_placeholder,
                event_placeholder,
                agent_placeholder
            )
        )
        
        st.success("🎉 Campaign completed successfully!")
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ Campaign failed: {str(e)}")
        add_log(f"Campaign error: {str(e)}", "error")
    
    st.session_state.campaign_running = False

# ============================================================================
# STANDARD DASHBOARD TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "🤖 Agents",
    "📁 Files",
    "🖼️ Images",
    "📝 Logs",
    "📦 Export"
])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_iteration_progress()
        render_metrics_overview()
    
    with col2:
        render_todos()

with tab2:
    render_agent_status()
    
    if st.session_state.campaign_state:
        st.divider()
        st.subheader("📈 Campaign Progress")
        status = st.session_state.campaign_state.get('campaign_status', 'unknown')
        st.info(f"Current Status: **{status.replace('_', ' ').title()}**")

with tab3:
    render_files_by_iteration()

with tab4:
    render_campaign_images()

with tab5:
    render_logs()
    
    if st.button("🔄 Refresh Logs"):
        st.rerun()

with tab6:
    st.subheader("📦 Export Campaign Results")
    
    if not st.session_state.campaign_state:
        st.info("⚠️ No campaign data to export. Run a campaign first!")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📄 Individual Exports")
            
            if st.button("📝 Download Summary (MD)", use_container_width=True):
                summary_md = create_campaign_summary_md(st.session_state.campaign_state)
                st.download_button(
                    label="⬇️ Download Markdown",
                    data=summary_md,
                    file_name="campaign_summary.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            if st.button("📊 Download Data (JSON)", use_container_width=True):
                json_data = create_campaign_json(st.session_state.campaign_state)
                st.download_button(
                    label="⬇️ Download JSON",
                    data=json_data,
                    file_name="campaign_data.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col2:
            st.markdown("### 📦 Complete Package")
            
            st.info("""
            **ZIP Archive includes:**
            - Campaign summary
            - All generated files
            - Decoded images
            - Organized by iteration
            """)
            
            if st.button("🗜️ Generate ZIP", use_container_width=True, type="primary"):
                with st.spinner("Creating ZIP..."):
                    zip_buffer = create_zip_archive(st.session_state.campaign_state)
                    product_name_short = st.session_state.campaign_state.get('product_info', 'campaign').split('\n')[0][:30]
                    filename = get_export_filename(product_name_short)
                    
                    st.download_button(
                        label="⬇️ Download ZIP",
                        data=zip_buffer,
                        file_name=filename,
                        mime="application/zip",
                        use_container_width=True
                    )
                    
                    st.success("✅ ZIP ready!")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("Marketing Campaign Multi-Agent System v2.0 | Real-Time Dashboard | Powered by LangGraph")