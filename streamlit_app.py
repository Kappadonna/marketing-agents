"""
Marketing Campaign Multi-Agent System - Streamlit Dashboard
============================================================

VERSION 3.1 - FIXED SESSION STATE IN THREADS:
✅ Thread-safe state management with Queue
✅ Real-time updates without ScriptRunContext errors
✅ Shared state dictionary for thread communication
✅ Non-blocking UI with proper state synchronization
"""

import os
import asyncio
import base64
import json
import threading
import time
from datetime import datetime
from io import BytesIO
from queue import Queue
from typing import Dict, Any

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
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .main { background-color: #1e1e1e; color: #ffffff; }
    .stMarkdown { color: #ffffff; }
    
    .metric-card {
        background: #2d2d2d;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        margin: 10px 0;
        color: #ffffff;
    }
    
    .agent-card {
        background: #2d2d2d;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #3d3d3d;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    
    .agent-card h4 { color: #ffffff !important; margin: 0 0 10px 0; }
    .agent-card p { color: #b0b0b0 !important; margin: 5px 0; }
    
    .agent-active {
        border-color: #28a745;
        box-shadow: 0 0 20px rgba(40, 167, 69, 0.4);
        animation: pulse 2s infinite;
    }
    
    .agent-idle { border-color: #6c757d; opacity: 0.7; }
    
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(40, 167, 69, 0.4); }
        50% { box-shadow: 0 0 30px rgba(40, 167, 69, 0.6); }
    }
    
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
    
    .event-item {
        background: #2d2d2d;
        padding: 10px 15px;
        border-left: 4px solid #667eea;
        margin: 5px 0;
        border-radius: 5px;
        color: #ffffff;
        animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
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
    
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    if "TAVILY_API_KEY" in st.secrets:
        os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]
    
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ Missing OPENAI_API_KEY")
        st.stop()
    if not os.getenv("TAVILY_API_KEY"):
        st.error("❌ Missing TAVILY_API_KEY")
        st.stop()
    
    return True

setup_environment()

# ============================================================================
# SHARED STATE FOR THREAD COMMUNICATION
# ============================================================================

class SharedState:
    """Thread-safe state container for campaign execution"""
    def __init__(self):
        self.lock = threading.Lock()
        self.data: Dict[str, Any] = {
            'campaign_state': None,
            'logs': [],
            'events': [],
            'active_agent': None,
            'current_phase': 'Idle',
            'agent_status': {
                'project-manager': 'idle',
                'strategy-planner': 'idle',
                'content-creator': 'idle',
                'analytics-agent': 'idle'
            },
            'total_tasks': 0,
            'completed_tasks': 0,
            'current_iteration': 1,
            'files_count': 0,
            'campaign_running': False,
            'campaign_error': None,
            'last_update': datetime.now(),
        }
    
    def get(self, key: str, default=None):
        with self.lock:
            return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        with self.lock:
            self.data[key] = value
            self.data['last_update'] = datetime.now()
    
    def update(self, updates: dict):
        with self.lock:
            self.data.update(updates)
            self.data['last_update'] = datetime.now()
    
    def append_log(self, message: str, level: str = "info"):
        with self.lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.data['logs'].append({
                "timestamp": timestamp,
                "message": message,
                "level": level
            })
            self.data['last_update'] = datetime.now()
    
    def append_event(self, event_type: str, agent: str, description: str, data: dict = None):
        with self.lock:
            self.data['events'].append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "type": event_type,
                "agent": agent,
                "description": description,
                "data": data or {}
            })
            self.data['last_update'] = datetime.now()

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if 'shared_state' not in st.session_state:
        st.session_state.shared_state = SharedState()
    
    defaults = {
        'agent': None,
        'template_config': {},
        'max_iterations': 2,
        'campaign_thread': None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def sync_from_shared_state():
    """Sync data from shared state to session state for display"""
    shared = st.session_state.shared_state
    
    # Create convenience accessors
    st.session_state.campaign_state = shared.get('campaign_state')
    st.session_state.logs = shared.get('logs', [])
    st.session_state.events = shared.get('events', [])
    st.session_state.active_agent = shared.get('active_agent')
    st.session_state.current_phase = shared.get('current_phase', 'Idle')
    st.session_state.agent_status = shared.get('agent_status', {})
    st.session_state.total_tasks = shared.get('total_tasks', 0)
    st.session_state.completed_tasks = shared.get('completed_tasks', 0)
    st.session_state.current_iteration = shared.get('current_iteration', 1)
    st.session_state.files_count = shared.get('files_count', 0)
    st.session_state.campaign_running = shared.get('campaign_running', False)
    st.session_state.campaign_error = shared.get('campaign_error')

# ============================================================================
# CAMPAIGN EXECUTION - THREAD-SAFE VERSION
# ============================================================================

async def run_campaign_async(agent, campaign_input, config, shared_state: SharedState):
    """Run campaign asynchronously with thread-safe state updates"""
    try:
        shared_state.append_log("Starting campaign execution...", "info")
        shared_state.append_event("start", "system", "🚀 Campaign started", {})
        shared_state.set('current_phase', "Initializing")
        shared_state.set('campaign_running', True)
        
        async for graph_name, stream_mode, event in agent.astream(
            campaign_input,
            stream_mode=["updates", "values"],
            subgraphs=True,
            config=config
        ):
            if stream_mode == "updates":
                node, result = list(event.items())[0]
                
                # Detect agent activity
                agent_name = "project-manager"
                
                if 'messages' in result and result['messages']:
                    last_message = result['messages'][-1]
                    
                    # Tool calls indicate delegation
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        for tool_call in last_message.tool_calls:
                            if tool_call.get('name') == 'task':
                                args = tool_call.get('args', {})
                                subagent = args.get('subagent_type', '')
                                if subagent:
                                    agent_name = subagent
                                    shared_state.update({
                                        'active_agent': agent_name,
                                        'current_phase': f"Running {agent_name}"
                                    })
                                    agent_status = shared_state.get('agent_status', {})
                                    agent_status[agent_name] = 'active'
                                    shared_state.set('agent_status', agent_status)
                                    shared_state.append_event("delegation", "project-manager",
                                                            f"➡️ Delegated to {agent_name}", {'subagent': agent_name})
                    
                    # Tool results indicate completion
                    if hasattr(last_message, 'content'):
                        content_str = str(last_message.content)
                        if "✅" in content_str or "complete" in content_str.lower():
                            shared_state.append_event("completion", agent_name, "✅ Task completed", {})
                            agent_status = shared_state.get('agent_status', {})
                            agent_status[agent_name] = 'idle'
                            shared_state.set('agent_status', agent_status)
                            if shared_state.get('active_agent') == agent_name:
                                shared_state.set('active_agent', None)
                
                # Update campaign state
                shared_state.set('campaign_state', dict(result))
                
                # Update task counts
                campaign_state = shared_state.get('campaign_state')
                if campaign_state:
                    todos = campaign_state.get('todos', [])
                    shared_state.update({
                        'total_tasks': len(todos),
                        'completed_tasks': len([t for t in todos if t.get('status') == 'completed']),
                        'files_count': len([f for f in campaign_state.get('files', {}).keys() if not f.startswith('URL_error')]),
                        'current_iteration': campaign_state.get('iteration_count', 1)
                    })
            
            # Save final state
            if stream_mode == "values" and len(graph_name) == 0:
                shared_state.set('campaign_state', dict(event))
                campaign_state = shared_state.get('campaign_state')
                if campaign_state:
                    todos = campaign_state.get('todos', [])
                    shared_state.update({
                        'total_tasks': len(todos),
                        'completed_tasks': len([t for t in todos if t.get('status') == 'completed']),
                        'files_count': len([f for f in campaign_state.get('files', {}).keys() if not f.startswith('URL_error')]),
                        'current_iteration': campaign_state.get('iteration_count', 1)
                    })
        
        shared_state.append_log("Campaign completed successfully!", "success")
        shared_state.append_event("completion", "system", "🎉 Campaign completed", {})
        shared_state.update({
            'current_phase': "Completed",
            'campaign_running': False
        })
        
    except Exception as e:
        shared_state.append_log(f"Campaign error: {str(e)}", "error")
        shared_state.append_event("error", "system", f"❌ Error: {str(e)}", {})
        shared_state.update({
            'campaign_error': str(e),
            'campaign_running': False
        })

def run_campaign_thread(agent, campaign_input, config, shared_state: SharedState):
    """Run campaign in background thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_campaign_async(agent, campaign_input, config, shared_state))
    finally:
        loop.close()

# ============================================================================
# RENDERING FUNCTIONS
# ============================================================================

def render_campaign_header():
    """Render the main header with campaign status"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🚀 Marketing Campaign Dashboard")
    
    with col2:
        if st.session_state.campaign_running:
            st.markdown('<div class="live-indicator"><div class="live-dot"></div>LIVE</div>', 
                       unsafe_allow_html=True)
    
    with col3:
        if st.session_state.campaign_state:
            status = st.session_state.campaign_state.get('campaign_status', 'unknown')
            st.markdown(f'<span class="status-badge status-{status}">{status.upper()}</span>', 
                       unsafe_allow_html=True)

def render_live_metrics():
    """Render live metrics cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        iteration = st.session_state.current_iteration
        max_iter = st.session_state.max_iterations
        st.metric(
            label="📊 Iteration",
            value=f"{iteration}/{max_iter}",
            delta=f"{(iteration/max_iter*100):.0f}% complete"
        )
    
    with col2:
        completed = st.session_state.completed_tasks
        total = st.session_state.total_tasks
        st.metric(
            label="✅ Tasks",
            value=f"{completed}/{total}",
            delta=f"{completed} done"
        )
    
    with col3:
        files_count = st.session_state.files_count
        st.metric(
            label="📁 Files",
            value=files_count,
            delta=f"+{files_count}"
        )
    
    with col4:
        active_agent = st.session_state.active_agent or "None"
        st.metric(
            label="🤖 Active Agent",
            value=active_agent.replace('-', ' ').title() if active_agent != "None" else "None"
        )

def render_agent_status():
    """Render agent status cards"""
    st.subheader("🤖 Agent Status")
    
    agents = {
        'project-manager': {'name': 'Project Manager', 'icon': '👔', 'role': 'Orchestrates campaign workflow'},
        'strategy-planner': {'name': 'Strategy Planner', 'icon': '📊', 'role': 'Market research & strategy'},
        'content-creator': {'name': 'Content Creator', 'icon': '✍️', 'role': 'Creates social content'},
        'analytics-agent': {'name': 'Analytics Agent', 'icon': '📈', 'role': 'Analyzes performance'}
    }
    
    cols = st.columns(2)
    
    for idx, (agent_id, info) in enumerate(agents.items()):
        with cols[idx % 2]:
            status = st.session_state.agent_status.get(agent_id, 'idle')
            status_class = 'agent-active' if status == 'active' else 'agent-idle'
            status_emoji = '🟢' if status == 'active' else '⚪'
            
            st.markdown(f"""
            <div class="agent-card {status_class}">
                <h4>{info['icon']} {info['name']}</h4>
                <p>{info['role']}</p>
                <p class="status">{status_emoji} {status.upper()}</p>
            </div>
            """, unsafe_allow_html=True)

def render_event_feed():
    """Render recent events"""
    st.subheader("📢 Recent Events")
    
    if not st.session_state.events:
        st.info("No events yet")
        return
    
    for event in reversed(st.session_state.events[-10:]):
        st.markdown(f"""
        <div class="event-item">
            <strong>{event['timestamp']}</strong> - {event['agent']} - {event['description']}
        </div>
        """, unsafe_allow_html=True)

def render_logs():
    """Render system logs"""
    st.subheader("📝 System Logs")
    
    if not st.session_state.logs:
        st.info("No logs yet")
        return
    
    for log in reversed(st.session_state.logs[-20:]):
        icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}.get(log['level'], "ℹ️")
        st.text(f"{icon} {log['timestamp']} - {log['message']}")

def render_files_by_iteration():
    """Render files organized by iteration"""
    st.subheader("📁 Generated Files")
    
    if not st.session_state.campaign_state:
        st.info("No files yet")
        return
    
    files = st.session_state.campaign_state.get('files', {})
    files = {k: v for k, v in files.items() if not k.startswith('URL_error')}
    
    if not files:
        st.info("No files generated yet")
        return
    
    # Group by iteration
    iterations = {}
    other_files = []
    
    for filename in sorted(files.keys()):
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
    
    for iter_num in sorted(iterations.keys()):
        with st.expander(f"📂 Iteration {iter_num} ({len(iterations[iter_num])} files)"):
            for filename in sorted(iterations[iter_num]):
                file_icon = "🖼️" if "image" in filename else "📊" if "chart" in filename else "📄"
                st.markdown(f"{file_icon} `{filename}`")
    
    if other_files:
        with st.expander(f"📂 Other Files ({len(other_files)} files)"):
            for filename in sorted(other_files):
                st.markdown(f"📄 `{filename}`")

def render_campaign_images():
    """Render generated images"""
    st.subheader("🖼️ Generated Images")
    
    if not st.session_state.campaign_state:
        st.info("No images yet")
        return
    
    files = st.session_state.campaign_state.get('files', {})
    image_files = [f for f in files.keys() if 'image_data' in f or 'chart_data' in f]
    
    if not image_files:
        st.info("No images generated yet")
        return
    
    for img_file in sorted(image_files):
        try:
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
                st.image(img_bytes, caption=img_file, use_container_width=True)
        except:
            st.warning(f"Could not display {img_file}")

# ============================================================================
# SIDEBAR - CAMPAIGN CONFIGURATION
# ============================================================================

with st.sidebar:
    st.header("⚙️ Campaign Configuration")
    
    # Template selection
    st.subheader("📋 Templates")
    
    category = st.selectbox("Category", options=list(CATEGORIES.keys()), index=0)
    campaign_options = CATEGORIES[category]
    selected_campaign = st.selectbox("Select Template", options=campaign_options, index=0)
    
    if st.button("📥 Load Template"):
        config = get_campaign_config(selected_campaign)
        st.session_state.template_config = config
        st.success(f"✅ Loaded: {selected_campaign}")
        st.rerun()
    
    st.divider()
    
    # Model settings
    st.subheader("🤖 Model Settings")
    model_choice = st.selectbox("LLM Model", options=["openai:gpt-4o-mini", "openai:gpt-4o"], index=0)
    max_iterations = st.slider("Max Iterations", 1, 5, 2)
    performance_threshold = st.slider("Performance Threshold", 50.0, 95.0, 75.0, 5.0)
    
    st.divider()
    
    # Product details
    st.subheader("📦 Product Details")
    template = st.session_state.get('template_config', {})
    
    product_name = st.text_input("Product Name", value=template.get('product_name', "NeuroBuds Pro"))
    product_info = st.text_area("Product Description", value=template.get('product_info', """AI-powered wireless earbuds"""), height=150)
    campaign_goal = st.text_area("Campaign Goal", value=template.get('campaign_goal', "Generate awareness"), height=80)
    target_audience = st.text_area("Target Audience", value=template.get('target_audience', "Tech enthusiasts aged 25-40"), height=80)
    
    st.divider()
    
    # Control buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 START", use_container_width=True, disabled=st.session_state.campaign_running, type="primary"):
            # Initialize agent
            st.session_state.agent = create_marketing_campaign_agent(
                model_name=model_choice,
                max_iterations=max_iterations,
                performance_threshold=performance_threshold
            )
            
            # Create campaign input
            campaign_input = create_campaign_input(
                product_info=f"{product_name}\n\n{product_info}",
                campaign_goal=campaign_goal,
                target_audience=target_audience,
                max_iterations=max_iterations,
                performance_threshold=performance_threshold
            )
            
            # Reset shared state
            st.session_state.shared_state = SharedState()
            st.session_state.shared_state.set('campaign_running', True)
            st.session_state.max_iterations = max_iterations
            
            # Run in background thread
            config = {"recursion_limit": 200}
            thread = threading.Thread(
                target=run_campaign_thread,
                args=(st.session_state.agent, campaign_input, config, st.session_state.shared_state),
                daemon=True
            )
            thread.start()
            st.session_state.campaign_thread = thread
            
            st.session_state.shared_state.append_log("Campaign started in background", "info")
            st.rerun()
    
    with col2:
        if st.button("⏹️ STOP", use_container_width=True, disabled=not st.session_state.campaign_running):
            st.session_state.shared_state.set('campaign_running', False)
            st.session_state.shared_state.append_log("Campaign stopped by user", "warning")
            st.rerun()
    
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.shared_state = SharedState()
        st.session_state.agent = None
        st.rerun()

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

# Sync from shared state
sync_from_shared_state()

# Header
render_campaign_header()

# Show current phase
if st.session_state.campaign_running:
    st.info(f"📍 Current Phase: {st.session_state.current_phase}")

# Show error if any
if st.session_state.campaign_error:
    st.error(f"❌ Error: {st.session_state.campaign_error}")

st.divider()

# Live metrics
render_live_metrics()

st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Overview", "🤖 Agents", "📁 Files", "🖼️ Images", "📝 Logs", "📦 Export"])

with tab1:
    st.subheader("📊 Campaign Overview")
    if st.session_state.campaign_state:
        todos = st.session_state.campaign_state.get('todos', [])
        if todos:
            st.write("**Tasks:**")
            for todo in todos:
                status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(todo['status'], "❓")
                st.write(f"{status_emoji} {todo['content']}")
    else:
        st.info("No campaign data yet")

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

with tab6:
    st.subheader("📦 Export Results")
    if not st.session_state.campaign_state:
        st.info("⚠️ No data to export")
    else:
        if st.button("🗜️ Download ZIP", type="primary"):
            with st.spinner("Creating ZIP..."):
                zip_buffer = create_zip_archive(st.session_state.campaign_state)
                st.download_button(
                    label="⬇️ Download",
                    data=zip_buffer,
                    file_name=f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )

# ============================================================================
# AUTO-REFRESH DURING CAMPAIGN
# ============================================================================

if st.session_state.campaign_running:
    time.sleep(2)
    st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
last_update = st.session_state.shared_state.get('last_update', datetime.now())
st.caption(f"Marketing Campaign System v3.1 | Last update: {last_update.strftime('%H:%M:%S')}")
