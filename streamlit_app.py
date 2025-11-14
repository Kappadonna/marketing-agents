"""
Marketing Campaign Multi-Agent System - Streamlit Dashboard
============================================================

VERSION 2.1 - BUG FIXES:
✅ Fixed task counter not updating (0/4 → correct count)
✅ Fixed text visibility in agent cards (white on white)
✅ Fixed files count showing 0
✅ Fixed state synchronization
✅ Real-time updates during campaign execution
"""

import os
import asyncio
import base64
import json
from datetime import datetime
from io import BytesIO

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
# CUSTOM CSS - FIXED VERSION
# ============================================================================

st.markdown("""
<style>
    /* Main theme - Fixed dark mode support */
    .main {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    
    /* Streamlit specific overrides */
    .stMarkdown {
        color: #ffffff;
    }
    
    /* Cards - Fixed contrast */
    .metric-card {
        background: #2d2d2d;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        margin: 10px 0;
        color: #ffffff;
    }
    
    /* Agent cards - FIXED TEXT VISIBILITY */
    .agent-card {
        background: #2d2d2d;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #3d3d3d;
        margin: 10px 0;
        transition: all 0.3s ease;
        min-height: 120px;
    }
    
    .agent-card h4 {
        color: #ffffff !important;
        margin: 0 0 10px 0;
        font-size: 18px;
    }
    
    .agent-card p {
        color: #b0b0b0 !important;
        margin: 5px 0;
        font-size: 14px;
    }
    
    .agent-card .status {
        color: #ffffff !important;
        font-weight: bold;
        margin-top: 10px;
    }
    
    .agent-active {
        border-color: #28a745;
        box-shadow: 0 0 20px rgba(40, 167, 69, 0.4);
        animation: pulse 2s infinite;
    }
    
    .agent-idle {
        border-color: #6c757d;
        opacity: 0.7;
    }
    
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(40, 167, 69, 0.4); }
        50% { box-shadow: 0 0 30px rgba(40, 167, 69, 0.6); }
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
    
    /* Iteration progress */
    .iteration-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    
    /* File list */
    .file-item {
        background: #2d2d2d;
        padding: 10px;
        border-left: 4px solid #667eea;
        margin: 5px 0;
        border-radius: 5px;
        color: #ffffff;
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
    }
    
    /* Event feed */
    .event-item {
        background: #2d2d2d;
        padding: 10px 15px;
        border-left: 4px solid #667eea;
        margin: 5px 0;
        border-radius: 5px;
        animation: slideIn 0.3s ease;
        color: #ffffff;
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
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2d2d2d;
        color: #ffffff;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: #ffffff;
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
# SESSION STATE INITIALIZATION - FIXED VERSION
# ============================================================================

def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'campaign_running': False,
        'campaign_state': None,
        'agent': None,
        'logs': [],
        'events': [],
        'active_agent': None,
        'current_task': None,
        'agent_status': {
            'project-manager': 'idle',
            'strategy-planner': 'idle',
            'content-creator': 'idle',
            'analytics-agent': 'idle'
        },
        'template_config': {},
        'last_update': datetime.now(),  # NEW: Track last update
        'total_tasks': 0,  # NEW: Track total tasks
        'completed_tasks': 0,  # NEW: Track completed tasks
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# UTILITY FUNCTIONS - FIXED VERSION
# ============================================================================

def add_event(event_type: str, agent: str, message: str, details: dict = None):
    """Add a real-time event to the event log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    event = {
        "time": timestamp,
        "type": event_type,
        "agent": agent,
        "message": message,
        "details": details or {}
    }
    st.session_state.events.insert(0, event)
    st.session_state.events = st.session_state.events[:100]
    st.session_state.last_update = datetime.now()

def set_active_agent(agent_name: str, task: str = None):
    """Set the currently active agent and update status"""
    st.session_state.active_agent = agent_name
    st.session_state.current_task = task
    st.session_state.agent_status[agent_name] = 'active'
    st.session_state.last_update = datetime.now()

def set_agent_idle(agent_name: str):
    """Set an agent to idle status"""
    st.session_state.agent_status[agent_name] = 'idle'
    if st.session_state.active_agent == agent_name:
        st.session_state.active_agent = None
        st.session_state.current_task = None
    st.session_state.last_update = datetime.now()

def add_log(message: str, level: str = "info"):
    """Add a log message to the session state"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append({
        "time": timestamp,
        "level": level,
        "message": message
    })
    st.session_state.last_update = datetime.now()

def get_status_badge(status: str) -> str:
    """Generate HTML for status badge"""
    return f'<span class="status-badge status-{status}">{status.replace("_", " ").upper()}</span>'

def decode_base64_image(b64_string: str) -> bytes:
    """Decode base64 string to image bytes"""
    try:
        lines = b64_string.split('\n')
        b64_data = None
        for line in lines:
            line = line.strip()
            if len(line) > 1000:
                b64_data = line
                break
        
        if b64_data:
            return base64.b64decode(b64_data)
    except Exception as e:
        st.error(f"Error decoding image: {e}")
    return None

# ============================================================================
# FIXED: TASK COUNTER FUNCTIONS
# ============================================================================

def count_completed_tasks(todos: list) -> tuple:
    """Count completed tasks from TODO list
    
    Returns:
        tuple: (completed_count, total_count)
    """
    if not todos:
        return (0, 0)
    
    completed = len([t for t in todos if t.get('status') == 'completed'])
    total = len(todos)
    
    return (completed, total)

def update_task_counts():
    """Update task counts from current campaign state"""
    if st.session_state.campaign_state:
        todos = st.session_state.campaign_state.get('todos', [])
        completed, total = count_completed_tasks(todos)
        st.session_state.completed_tasks = completed
        st.session_state.total_tasks = total

# ============================================================================
# VISUALIZATION COMPONENTS - FIXED VERSION
# ============================================================================

def render_campaign_header():
    """Render the main campaign header with live indicator"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🚀 Marketing Campaign Dashboard")
        st.caption("Multi-Agent System with Real-Time Monitoring")
    
    with col2:
        if st.session_state.campaign_state:
            status = st.session_state.campaign_state.get('campaign_status', 'unknown')
            st.markdown(get_status_badge(status), unsafe_allow_html=True)
    
    with col3:
        if st.session_state.campaign_running:
            st.markdown('<div class="live-indicator"><div class="live-dot"></div>LIVE</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown("⚪ **IDLE**")

def render_live_metrics():
    """Render live metrics with FIXED counters"""
    st.markdown("## 📡 Live Campaign Execution")
    
    # Update task counts BEFORE rendering
    update_task_counts()
    
    # Get current state
    files_count = 0
    events_count = len(st.session_state.events)
    
    if st.session_state.campaign_state:
        files = st.session_state.campaign_state.get('files', {})
        # Filter out error files
        files_count = len([f for f in files.keys() if not f.startswith('URL_error')])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Files Generated", files_count)
    
    with col2:
        # FIXED: Show actual task counts
        st.metric("Tasks", f"{st.session_state.completed_tasks}/{st.session_state.total_tasks}")
    
    with col3:
        st.metric("Events", events_count)

def render_iteration_progress():
    """Render iteration progress indicator"""
    if not st.session_state.campaign_state:
        st.info("⏳ Waiting for campaign to start...")
        return
    
    current = st.session_state.campaign_state.get('iteration_count', 0)
    max_iter = st.session_state.campaign_state.get('max_iterations', 3)
    status = st.session_state.campaign_state.get('campaign_status', 'unknown')
    
    # Progress percentage
    progress = (current / max_iter) if max_iter > 0 else 0
    
    st.markdown(f"""
    <div class="iteration-box">
        <h2 style="margin: 0;">Iteration {current} of {max_iter}</h2>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">
            Progress: {int(progress * 100)}%
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(progress)

def render_agent_status():
    """Render agent status cards with FIXED text visibility"""
    st.markdown("### 🤖 Agent Status")
    
    if st.session_state.campaign_running:
        st.markdown('<div class="live-indicator"><div class="live-dot"></div>LIVE</div>', 
                   unsafe_allow_html=True)
    
    # Current task
    if st.session_state.current_task:
        st.info(f"**Current Task:** {st.session_state.current_task[:150]}...")
    
    # Agent cards with FIXED styling
    agents_info = [
        {
            'key': 'project-manager',
            'icon': '🎯',
            'name': 'Project Manager',
            'role': 'Orchestration'
        },
        {
            'key': 'strategy-planner',
            'icon': '📊',
            'name': 'Strategy Planner',
            'role': 'Research & Strategy'
        },
        {
            'key': 'content-creator',
            'icon': '✍️',
            'name': 'Content Creator',
            'role': 'Content & Images'
        },
        {
            'key': 'analytics-agent',
            'icon': '📈',
            'name': 'Analytics Agent',
            'role': 'Performance Analysis'
        }
    ]
    
    cols = st.columns(2)
    
    for idx, agent in enumerate(agents_info):
        with cols[idx % 2]:
            status = st.session_state.agent_status.get(agent['key'], 'idle')
            is_active = status == 'active'
            
            status_class = "agent-active" if is_active else "agent-idle"
            status_emoji = "🟢" if is_active else "⚪"
            
            # FIXED: Clear text visibility
            st.markdown(f"""
            <div class="agent-card {status_class}">
                <h4>{agent['icon']} {agent['name']} {status_emoji}</h4>
                <p>{agent['role']}</p>
                <p class="status">Status: {status.upper()}</p>
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

def render_files_by_iteration():
    """Render files organized by iteration"""
    st.markdown("### 📁 Generated Files")
    
    if not st.session_state.campaign_state:
        st.info("No files yet")
        return
    
    files = st.session_state.campaign_state.get('files', {})
    
    # Filter out error files
    valid_files = {k: v for k, v in files.items() if not k.startswith('URL_error')}
    
    if not valid_files:
        st.info("No files generated yet")
        return
    
    # Organize files by iteration
    iterations = {}
    other_files = []
    
    for filename in sorted(valid_files.keys()):
        if '_v' in filename:
            try:
                iter_num = int(filename.split('_v')[1].split('.')[0])
                if iter_num not in iterations:
                    iterations[iter_num] = []
                iterations[iter_num].append(filename)
            except:
                other_files.append(filename)
        else:
            other_files.append(filename)
    
    # Display by iteration
    for iter_num in sorted(iterations.keys()):
        with st.expander(f"📂 Iteration {iter_num} ({len(iterations[iter_num])} files)", expanded=True):
            for filename in sorted(iterations[iter_num]):
                st.text(f"📄 {filename}")
    
    # Other files
    if other_files:
        with st.expander(f"📂 Other Files ({len(other_files)})", expanded=True):
            for filename in sorted(other_files):
                st.text(f"📄 {filename}")

def render_campaign_images():
    """Render all generated images in a gallery"""
    st.markdown("### 🖼️ Generated Images")
    
    if not st.session_state.campaign_state:
        st.info("No images yet")
        return
    
    files = st.session_state.campaign_state.get('files', {})
    
    # Find all image data files
    image_files = [f for f in files.keys() if '_data' in f and f.endswith('.txt') and 'image' in f.lower()]
    
    if not image_files:
        st.info("🖼️ No images generated yet")
        return
    
    cols = st.columns(2)
    for idx, img_file in enumerate(sorted(image_files)):
        with cols[idx % 2]:
            # Extract iteration number
            iter_match = img_file.split('_v')
            if len(iter_match) > 1:
                iter_num = iter_match[1].split('.')[0]
                st.caption(f"Iteration {iter_num}")
            
            img_bytes = decode_base64_image(files[img_file])
            if img_bytes:
                st.image(img_bytes, use_column_width=True)

def render_logs():
    """Render activity logs"""
    st.markdown("### 📝 Activity Log")
    
    if not st.session_state.logs:
        st.info("No activity logged yet")
        return
    
    for log in reversed(st.session_state.logs[-20:]):
        level_emoji = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        }
        emoji = level_emoji.get(log['level'], 'ℹ️')
        st.text(f"[{log['time']}] {emoji} {log['message']}")

# ============================================================================
# CAMPAIGN EXECUTION - FIXED VERSION
# ============================================================================

async def run_campaign_async(campaign_input, config):
    """Run campaign asynchronously with FIXED state updates"""
    add_log("Campaign started", "success")
    add_event("delegation", "project-manager", "🚀 Campaign started", {})
    set_active_agent("project-manager", "Initializing campaign")
    
    try:
        # Stream events from agent
        async for graph_name, stream_mode, event in st.session_state.agent.astream(
            campaign_input,
            stream_mode=["updates", "values"],
            subgraphs=True,
            config=config
        ):
            if stream_mode == "updates":
                node, result = list(event.items())[0]
                
                # Determine active agent
                agent_name = "project-manager"
                if "strategy" in node.lower():
                    agent_name = "strategy-planner"
                elif "content" in node.lower():
                    agent_name = "content-creator"
                elif "analytics" in node.lower():
                    agent_name = "analytics-agent"
                
                # Log activity
                add_log(f"Agent {agent_name}: {node}", "info")
                
                # Extract task info
                messages = result.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    
                    # Check for tool calls
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        for tool_call in last_message.tool_calls:
                            tool_name = tool_call.get('name', 'unknown')
                            
                            if tool_name == 'task':
                                args = tool_call.get('args', {})
                                target = args.get('subagent_type', 'unknown')
                                task_desc = args.get('description', '')[:100]
                                
                                add_event("delegation", agent_name, 
                                        f"📤 Delegating to {target}", {})
                                set_active_agent(target, task_desc)
                            else:
                                add_event("task", agent_name, 
                                        f"⚙️ Executing: {tool_name}", {})
                    
                    # Check for completion
                    if hasattr(last_message, 'content'):
                        content_str = str(last_message.content)
                        if "✅" in content_str or "complete" in content_str.lower():
                            add_event("completion", agent_name, 
                                    "✅ Task completed", {})
                            set_agent_idle(agent_name)
                
                # CRITICAL FIX: Update state during execution
                st.session_state.campaign_state = dict(result)
                update_task_counts()
                
            # Save final state
            if stream_mode == "values" and len(graph_name) == 0:
                st.session_state.campaign_state = dict(event)
                update_task_counts()
        
        add_log("Campaign completed successfully!", "success")
        add_event("completion", "project-manager", "🎉 Campaign completed", {})
        set_agent_idle("project-manager")
        st.session_state.campaign_running = False
        
    except Exception as e:
        add_log(f"Campaign error: {str(e)}", "error")
        add_event("error", "system", f"❌ Error: {str(e)}", {})
        st.session_state.campaign_running = False
        raise

def run_campaign(campaign_input, config):
    """Wrapper to run async campaign"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_campaign_async(campaign_input, config))
    finally:
        loop.close()

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
            "openai:gpt-4o"
        ],
        index=0
    )
    
    max_iterations = st.slider(
        "Max Iterations",
        min_value=1,
        max_value=5,
        value=1,  # Default to 1 for testing
        help="Maximum number of campaign iterations"
    )
    
    performance_threshold = st.slider(
        "Performance Threshold",
        min_value=50.0,
        max_value=95.0,
        value=75.0,
        step=5.0
    )
    
    st.divider()
    
    # Product details
    st.subheader("📦 Product Details")
    
    template = st.session_state.get('template_config', {})
    
    product_name = st.text_input(
        "Product Name",
        value=template.get('product_name', "NeuroBuds Pro")
    )
    
    product_info = st.text_area(
        "Product Description",
        value=template.get('product_info', """Next-generation wireless earbuds featuring:
- AI adaptive noise cancellation
- Focus Mode for productivity
- Real-time translation
- 48h battery life
Price: €249.99"""),
        height=200
    )
    
    campaign_goal = st.text_area(
        "Campaign Goal",
        value=template.get('campaign_goal', "Generate pre-orders and build anticipation"),
        height=100
    )
    
    target_audience = st.text_area(
        "Target Audience",
        value=template.get('target_audience', "Tech enthusiasts aged 25-40"),
        height=120
    )
    
    st.divider()
    
    # Control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 START", use_container_width=True, disabled=st.session_state.campaign_running, type="primary"):
            # Initialize
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
            st.session_state.completed_tasks = 0
            st.session_state.total_tasks = 0
            
            add_log("Initializing agent system...", "info")
            
            # Run campaign
            config = {"recursion_limit": 200}
            
            with st.spinner("Campaign running..."):
                run_campaign(campaign_input, config)
            
            st.rerun()
    
    with col2:
        if st.button("⏹️ STOP", use_container_width=True, disabled=not st.session_state.campaign_running):
            st.session_state.campaign_running = False
            add_log("Campaign stopped by user", "warning")
            st.rerun()
    
    if st.button("🗑️ Clear All", use_container_width=True):
        for key in ['campaign_state', 'logs', 'events', 'active_agent', 'current_task']:
            st.session_state[key] = None if key in ['campaign_state', 'active_agent', 'current_task'] else []
        st.session_state.campaign_running = False
        st.session_state.completed_tasks = 0
        st.session_state.total_tasks = 0
        st.session_state.agent_status = {
            'project-manager': 'idle',
            'strategy-planner': 'idle',
            'content-creator': 'idle',
            'analytics-agent': 'idle'
        }
        st.rerun()

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

# Header
render_campaign_header()

st.divider()

# Live metrics (always visible)
render_live_metrics()

st.divider()

# Tabs
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
    
    with col2:
        render_todos()

with tab2:
    render_agent_status()
    
    st.divider()
    render_event_feed()

with tab3:
    render_files_by_iteration()

with tab4:
    render_campaign_images()

with tab5:
    render_logs()
    
    if st.button("🔄 Refresh"):
        st.rerun()

with tab6:
    st.subheader("📦 Export Campaign Results")
    
    if not st.session_state.campaign_state:
        st.info("⚠️ No campaign data to export")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📄 Individual Exports")
            
            if st.button("📝 Download Summary (MD)", use_container_width=True):
                summary_md = create_campaign_summary_md(st.session_state.campaign_state)
                st.download_button(
                    label="⬇️ Download",
                    data=summary_md,
                    file_name="campaign_summary.md",
                    mime="text/markdown"
                )
        
        with col2:
            st.markdown("### 📦 Complete Package")
            
            if st.button("🗜️ Generate ZIP", use_container_width=True, type="primary"):
                with st.spinner("Creating ZIP..."):
                    zip_buffer = create_zip_archive(st.session_state.campaign_state)
                    
                    st.download_button(
                        label="⬇️ Download ZIP",
                        data=zip_buffer,
                        file_name=f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip"
                    )

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("Marketing Campaign Multi-Agent System v2.1 - Fixed Version | Powered by LangGraph")
