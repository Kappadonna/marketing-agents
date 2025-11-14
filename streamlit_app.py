"""
Marketing Campaign Multi-Agent System - Streamlit Dashboard
============================================================

Interactive visualization dashboard for monitoring and controlling
the autonomous marketing campaign system.
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
# CUSTOM CSS
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
        background: white;
        padding: 10px;
        border-left: 4px solid #667eea;
        margin: 5px 0;
        border-radius: 5px;
    }
    
    /* Agent cards */
    .agent-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin: 10px 0;
    }
    
    .agent-active {
        border-color: #28a745;
        box-shadow: 0 0 10px rgba(40, 167, 69, 0.3);
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

if 'campaign_running' not in st.session_state:
    st.session_state.campaign_running = False
if 'campaign_state' not in st.session_state:
    st.session_state.campaign_state = None
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'logs' not in st.session_state:
    st.session_state.logs = []

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def add_log(message: str, level: str = "info"):
    """Add a log message to the session state"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append({
        "time": timestamp,
        "level": level,
        "message": message
    })

def get_status_badge(status: str) -> str:
    """Generate HTML for status badge"""
    return f'<span class="status-badge status-{status}">{status.replace("_", " ").upper()}</span>'

def decode_base64_image(b64_string: str) -> bytes:
    """Decode base64 string to image bytes"""
    try:
        # Remove any header lines
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
# VISUALIZATION COMPONENTS
# ============================================================================

def render_campaign_header():
    """Render the main campaign header"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🚀 Marketing Campaign Dashboard")
        st.caption("Multi-Agent System for Autonomous Campaign Management")
    
    with col2:
        if st.session_state.campaign_state:
            status = st.session_state.campaign_state.get('campaign_status', 'unknown')
            st.markdown(get_status_badge(status), unsafe_allow_html=True)
    
    with col3:
        if st.session_state.campaign_running:
            st.markdown("🟢 **CAMPAIGN ACTIVE**")
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
    
    # Progress bar
    st.progress(current / max_iter)

def render_metrics_overview():
    """Render key metrics overview"""
    if not st.session_state.campaign_state:
        st.info("📊 No campaign data available yet")
        return
    
    files = st.session_state.campaign_state.get('files', {})
    todos = st.session_state.campaign_state.get('todos', [])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Files Generated", len(files), delta=None)
    
    with col2:
        completed_todos = len([t for t in todos if t.get('status') == 'completed'])
        st.metric("Tasks Completed", f"{completed_todos}/{len(todos)}", delta=None)
    
    with col3:
        iterations = st.session_state.campaign_state.get('iteration_count', 0)
        st.metric("Iterations", iterations, delta=None)
    
    with col4:
        # Count analytics reports to get performance scores
        analytics_files = [f for f in files.keys() if 'analytics_report' in f]
        st.metric("Reports", len(analytics_files), delta=None)

def render_agent_status():
    """Render status of all agents"""
    st.subheader("🤖 Agent Status")
    
    agents = [
        {
            "name": "Project Manager",
            "icon": "👔",
            "status": "active" if st.session_state.campaign_running else "idle",
            "description": "Orchestrating campaign workflow"
        },
        {
            "name": "Strategy Planner",
            "icon": "🎯",
            "status": "standby",
            "description": "Market research and strategy"
        },
        {
            "name": "Content Creator",
            "icon": "✍️",
            "status": "standby",
            "description": "Creating social media content"
        },
        {
            "name": "Analytics Agent",
            "icon": "📊",
            "status": "standby",
            "description": "Performance analysis"
        }
    ]
    
    cols = st.columns(4)
    for idx, agent in enumerate(agents):
        with cols[idx]:
            active_class = "agent-active" if agent["status"] == "active" else ""
            st.markdown(f"""
            <div class="agent-card {active_class}">
                <h3 style="margin: 0;">{agent['icon']} {agent['name']}</h3>
                <p style="margin: 5px 0; font-size: 0.85em; color: #666;">
                    {agent['description']}
                </p>
                <span style="font-size: 0.8em; color: {'#28a745' if agent['status'] == 'active' else '#6c757d'};">
                    ● {agent['status'].upper()}
                </span>
            </div>
            """, unsafe_allow_html=True)

def render_todos():
    """Render TODO list"""
    if not st.session_state.campaign_state:
        return
    
    todos = st.session_state.campaign_state.get('todos', [])
    
    if not todos:
        st.info("📋 No tasks in the TODO list yet")
        return
    
    st.subheader("📋 Task List")
    
    for idx, todo in enumerate(todos, 1):
        status = todo.get('status', 'pending')
        content = todo.get('content', '')
        
        emoji_map = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅'
        }
        emoji = emoji_map.get(status, '❓')
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"{emoji} **{idx}.** {content}")
        with col2:
            st.caption(status.replace('_', ' ').title())

def render_files_by_iteration():
    """Render files organized by iteration"""
    if not st.session_state.campaign_state:
        return
    
    files = st.session_state.campaign_state.get('files', {})
    
    if not files:
        st.info("📁 No files generated yet")
        return
    
    st.subheader("📁 Generated Files")
    
    # Group files by iteration
    iterations = {}
    other_files = []
    
    for filename in files.keys():
        # Extract iteration number from filename
        if '_v' in filename:
            try:
                parts = filename.split('_v')
                iter_num = int(parts[1].split('.')[0])
                if iter_num not in iterations:
                    iterations[iter_num] = []
                iterations[iter_num].append(filename)
            except:
                other_files.append(filename)
        else:
            other_files.append(filename)
    
    # Display by iteration
    for iter_num in sorted(iterations.keys()):
        with st.expander(f"🔄 Iteration {iter_num} ({len(iterations[iter_num])} files)", expanded=(iter_num == max(iterations.keys()))):
            for filename in sorted(iterations[iter_num]):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"📄 `{filename}`")
                with col2:
                    if st.button("View", key=f"view_{filename}"):
                        st.session_state[f'viewing_{filename}'] = True
                
                # Show file content if viewing
                if st.session_state.get(f'viewing_{filename}', False):
                    content = files[filename]
                    
                    # Handle images
                    if filename.endswith('_data.txt') or 'image_data' in filename:
                        st.caption("🖼️ Image Data (Base64)")
                        img_bytes = decode_base64_image(content)
                        if img_bytes:
                            st.image(img_bytes, use_container_width=True)
                        else:
                            st.text_area("Raw Content", content[:500] + "...", height=100)
                    else:
                        st.text_area("File Content", content, height=300)
                    
                    if st.button("Close", key=f"close_{filename}"):
                        st.session_state[f'viewing_{filename}'] = False
                        st.rerun()
    
    # Other files
    if other_files:
        with st.expander(f"📦 Other Files ({len(other_files)} files)"):
            for filename in sorted(other_files):
                st.markdown(f"📄 `{filename}`")

def render_campaign_images():
    """Render all generated images in a gallery"""
    if not st.session_state.campaign_state:
        return
    
    files = st.session_state.campaign_state.get('files', {})
    
    # Find all image data files
    image_files = [f for f in files.keys() if '_data' in f and f.endswith('.txt')]
    
    if not image_files:
        st.info("🖼️ No images generated yet")
        return
    
    st.subheader("🖼️ Generated Images")
    
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
                st.image(img_bytes, use_container_width=True)
            
            # Show metadata if available
            metadata_file = img_file.replace('_data.txt', '.md')
            if metadata_file in files:
                with st.expander("ℹ️ Image Details"):
                    st.markdown(files[metadata_file])

def render_logs():
    """Render activity logs"""
    st.subheader("📝 Activity Log")
    
    if not st.session_state.logs:
        st.info("No activity logged yet")
        return
    
    log_container = st.container()
    with log_container:
        for log in reversed(st.session_state.logs[-20:]):  # Show last 20
            level_emoji = {
                'info': 'ℹ️',
                'success': '✅',
                'warning': '⚠️',
                'error': '❌'
            }
            emoji = level_emoji.get(log['level'], 'ℹ️')
            st.text(f"[{log['time']}] {emoji} {log['message']}")

# ============================================================================
# CAMPAIGN EXECUTION
# ============================================================================

async def run_campaign_async(campaign_input, config):
    """Run campaign asynchronously with state updates"""
    add_log("Campaign started", "success")
    
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
                add_log(f"Agent: {node} - Processing...", "info")
                
            # Save final state from "values" stream
            if stream_mode == "values" and len(graph_name) == 0:
                st.session_state.campaign_state = dict(event)
        
        add_log("Campaign completed successfully!", "success")
        st.session_state.campaign_running = False
        
    except Exception as e:
        add_log(f"Campaign error: {str(e)}", "error")
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
    
    # Campaign template selector
    st.subheader("📋 Quick Start Templates")
    
    use_template = st.checkbox("Use Pre-configured Template", value=False)
    
    if use_template:
        template_category = st.selectbox(
            "Category",
            list(CATEGORIES.keys()),
            help="Choose a campaign category"
        )
        
        campaigns_in_category = CATEGORIES[template_category]
        selected_template = st.selectbox(
            "Campaign Template",
            campaigns_in_category,
            help="Select a pre-configured campaign"
        )
        
        if st.button("📥 Load Template"):
            config = get_campaign_config(selected_template)
            st.session_state.template_config = config
            st.success(f"✅ Loaded: {config['product_name']}")
            st.rerun()
    
    st.divider()
    
    # Model selection
    model_choice = st.selectbox(
        "LLM Model",
        ["openai:gpt-4o", "openai:gpt-4o-mini"],
        index=1,
        help="GPT-4o-mini is faster and cheaper, GPT-4o is more powerful"
    )
    
    # Campaign parameters
    st.subheader("Campaign Parameters")
    
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
    
    # Use template config if available
    template = st.session_state.get('template_config', {})
    
    product_name = st.text_input(
        "Product Name",
        value=template.get('product_name', "NeuroBuds Pro"),
        help="Name of the product/service"
    )
    
    product_info = st.text_area(
        "Product Description",
        value=template.get('product_info', """Next-generation wireless earbuds featuring:
- AI adaptive noise cancellation (99% external noise blocked)
- Focus Mode: audio stimulation to boost concentration (+35% productivity)
- Real-time translation in 40+ languages
- Integrated biometric sensors (heart rate, stress level)
- 48h battery life with wireless charging
- IPX8 waterproof rating
Price: €249.99 (early bird: €199.99)"""),
        height=200,
        help="Detailed product information"
    )
    
    campaign_goal = st.text_area(
        "Campaign Goal",
        value=template.get('campaign_goal', "Generate pre-orders and build anticipation for product launch targeting early adopters"),
        height=100,
        help="Main objective of the campaign"
    )
    
    target_audience = st.text_area(
        "Target Audience",
        value=template.get('target_audience', "Tech enthusiasts and professionals aged 25-40, remote workers and commuters seeking productivity enhancement, fitness-conscious individuals interested in health tracking"),
        height=120,
        help="Description of target audience"
    )
    
    st.divider()
    
    # Start/Stop buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 START", use_container_width=True, disabled=st.session_state.campaign_running):
            # Create agent
            add_log("Initializing agent system...", "info")
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
            
            st.session_state.campaign_running = True
            
            # Run campaign in background
            config = {"recursion_limit": 200}
            
            with st.spinner("🔄 Campaign running..."):
                run_campaign(campaign_input, config)
            
            st.rerun()
    
    with col2:
        if st.button("⏹️ STOP", use_container_width=True, disabled=not st.session_state.campaign_running):
            st.session_state.campaign_running = False
            add_log("Campaign stopped by user", "warning")
            st.rerun()
    
    # Clear button
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.campaign_state = None
        st.session_state.logs = []
        st.session_state.campaign_running = False
        add_log("Dashboard cleared", "info")
        st.rerun()

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

# Header
render_campaign_header()

st.divider()

# Main content tabs
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
        st.write("Download all campaign files and reports in various formats:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📄 Individual Exports")
            
            # Markdown summary
            if st.button("📝 Download Summary (MD)", use_container_width=True):
                summary_md = create_campaign_summary_md(st.session_state.campaign_state)
                st.download_button(
                    label="⬇️ Download Markdown",
                    data=summary_md,
                    file_name="campaign_summary.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            # JSON export
            if st.button("📊 Download Data (JSON)", use_container_width=True):
                json_data = create_campaign_json(st.session_state.campaign_state)
                st.download_button(
                    label="⬇️ Download JSON",
                    data=json_data,
                    file_name="campaign_data.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            # HTML report
            if st.button("🌐 Download Report (HTML)", use_container_width=True):
                html_report = create_html_report(st.session_state.campaign_state)
                st.download_button(
                    label="⬇️ Download HTML",
                    data=html_report,
                    file_name="campaign_report.html",
                    mime="text/html",
                    use_container_width=True
                )
        
        with col2:
            st.markdown("### 📦 Complete Package")
            
            st.info("""
            **ZIP Archive includes:**
            - Campaign summary (MD)
            - Campaign data (JSON)
            - All generated files
            - Decoded PNG images
            - Organized by iteration
            """)
            
            if st.button("🗜️ Generate ZIP Archive", use_container_width=True, type="primary"):
                with st.spinner("Creating ZIP archive..."):
                    zip_buffer = create_zip_archive(st.session_state.campaign_state)
                    
                    product_name = st.session_state.campaign_state.get('product_info', 'campaign').split('\n')[0][:30]
                    filename = get_export_filename(product_name)
                    
                    st.download_button(
                        label="⬇️ Download ZIP",
                        data=zip_buffer,
                        file_name=filename,
                        mime="application/zip",
                        use_container_width=True
                    )
                    
                    st.success("✅ ZIP archive created successfully!")
        
        st.divider()
        
        # Preview section
        with st.expander("👁️ Preview Campaign Summary"):
            summary_md = create_campaign_summary_md(st.session_state.campaign_state)
            st.markdown(summary_md)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("Marketing Campaign Multi-Agent System v1.0 | Powered by LangGraph & Claude")
