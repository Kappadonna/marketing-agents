"""Utility functions for displaying messages and agent outputs in Jupyter notebooks.

FIXED VERSION - Added filtering for URL_error_* files in save_campaign_output
"""

import json
import os
import base64
import re

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def format_message_content(message):
    """Convert message content to displayable string."""
    parts = []
    tool_calls_processed = False

    # Handle both dict and Message objects
    if isinstance(message, dict):
        # Message is a dictionary
        content = message.get("content", "")
        message_type = message.get("type", "")
    else:
        # Message is a Message object
        content = getattr(message, "content", "")
        message_type = None

    # Handle main content
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, list):
        # Handle complex content like tool calls (Anthropic format)
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item["text"])
                elif item.get("type") == "tool_use":
                    parts.append(f"\n🔧 Tool Call: {item['name']}")
                    parts.append(f"   Args: {json.dumps(item['input'], indent=2, ensure_ascii=False)}")
                    parts.append(f"   ID: {item.get('id', 'N/A')}")
                    tool_calls_processed = True
            else:
                parts.append(str(item))
    elif content:
        parts.append(str(content))

    # Handle tool calls attached to the message (OpenAI format) - only if not already processed
    if not tool_calls_processed:
        # Try to get tool_calls from dict or object
        tool_calls = None
        if isinstance(message, dict):
            tool_calls = message.get("tool_calls")
        elif hasattr(message, "tool_calls"):
            tool_calls = message.tool_calls
        
        if tool_calls:
            for tool_call in tool_calls:
                if isinstance(tool_call, dict):
                    parts.append(f"\n🔧 Tool Call: {tool_call.get('name', 'Unknown')}")
                    parts.append(f"   Args: {json.dumps(tool_call.get('args', {}), indent=2, ensure_ascii=False)}")
                    parts.append(f"   ID: {tool_call.get('id', 'N/A')}")
                else:
                    # tool_call is an object
                    parts.append(f"\n🔧 Tool Call: {getattr(tool_call, 'name', 'Unknown')}")
                    parts.append(f"   Args: {json.dumps(getattr(tool_call, 'args', {}), indent=2, ensure_ascii=False)}")
                    parts.append(f"   ID: {getattr(tool_call, 'id', 'N/A')}")

    return "\n".join(parts) if parts else "[Empty message]"




def format_messages(messages):
    """Format and display a list of messages with Rich formatting."""
    for m in messages:
        # Handle both dict and Message objects
        if isinstance(m, dict):
            # Dictionary format - get type from 'type' or 'role' key
            msg_type = m.get("type", m.get("role", "Unknown"))
            # Normalize type names
            if msg_type == "human" or msg_type == "user":
                msg_type = "Human"
            elif msg_type == "ai" or msg_type == "assistant":
                msg_type = "Ai"
            elif msg_type == "tool":
                msg_type = "Tool"
            else:
                msg_type = msg_type.capitalize()
        else:
            # Message object - get class name
            msg_type = m.__class__.__name__.replace("Message", "")
        
        content = format_message_content(m)

        if msg_type == "Human":
            console.print(Panel(content, title="🧑 Human", border_style="blue"))
        elif msg_type == "Ai":
            console.print(Panel(content, title="🤖 Assistant", border_style="green"))
        elif msg_type == "Tool":
            console.print(Panel(content, title="🔧 Tool Output", border_style="yellow"))
        else:
            console.print(Panel(content, title=f"📋 {msg_type}", border_style="white"))




def format_message(messages):
    """Alias for format_messages for backward compatibility."""
    return format_messages(messages)


def show_prompt(prompt_text: str, title: str = "Prompt", border_style: str = "blue"):
    """Display a prompt with rich formatting and XML tag highlighting.

    Args:
        prompt_text: The prompt string to display
        title: Title for the panel (default: "Prompt")
        border_style: Border color style (default: "blue")
    """
    # Create a formatted display of the prompt
    formatted_text = Text(prompt_text)
    formatted_text.highlight_regex(r"<[^>]+>", style="bold blue")  # Highlight XML tags
    formatted_text.highlight_regex(
        r"##[^#\n]+", style="bold magenta"
    )  # Highlight headers
    formatted_text.highlight_regex(
        r"###[^#\n]+", style="bold cyan"
    )  # Highlight sub-headers

    # Display in a panel for better presentation
    console.print(
        Panel(
            formatted_text,
            title=f"[bold green]{title}[/bold green]",
            border_style=border_style,
            padding=(1, 2),
        )
    )


async def stream_agent(agent, query, config=None):
    """Stream agent execution with formatted output for both updates and values.
    
    Args:
        agent: The LangGraph agent to execute
        query: Input query/state for the agent
        config: Optional configuration dictionary
        
    Returns:
        Final state after agent execution
    """
    # Set default recursion limit if not provided
    if config is None:
        config = {"recursion_limit": 150}
    elif "recursion_limit" not in config:
        config["recursion_limit"] = 150
    
    async for graph_name, stream_mode, event in agent.astream(
        query,
        stream_mode=["updates", "values"], 
        subgraphs=True,
        config=config
    ):
        if stream_mode == "updates":
            print(f'Graph: {graph_name if len(graph_name) > 0 else "root"}')
            
            node, result = list(event.items())[0]
            
            # Print node name
            console.print(f"[bold cyan]Node: {node}[/bold cyan]")
            
            # Display messages if present
            messages = result.get("messages", [])
            if messages:
                format_messages(messages)
        
        # Save final state from "values" stream
        if stream_mode == "values" and len(graph_name) == 0:
            final_state = event
    
    return final_state


def print_campaign_summary(state):
    """Print a formatted summary of campaign results."""
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]                     CAMPAIGN SUMMARY                              [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════════[/bold cyan]\n")
    
    # Basic info
    console.print(f"[bold]Campaign Status:[/bold] {state.get('campaign_status', 'Unknown')}")
    console.print(f"[bold]Iterations Completed:[/bold] {state.get('iteration_count', 0)}")
    console.print(f"[bold]Max Iterations:[/bold] {state.get('max_iterations', 'N/A')}")
    console.print(f"[bold]Performance Threshold:[/bold] {state.get('performance_threshold', 'N/A')}")
    
    # Files
    files = state.get("files", {})
    if files:
        console.print(f"\n[bold]Files Generated ({len(files)}):[/bold]")
        for filename in files.keys():
            console.print(f"  📄 {filename}")
    else:
        console.print("[bold]Files:[/bold] None yet")
    
    # TODOs
    todos = state.get("todos", [])
    if todos:
        console.print(f"\n[bold]TODOs ({len(todos)}):[/bold]")
        for i, todo in enumerate(todos, 1):
            status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
            emoji = status_emoji.get(todo["status"], "❓")
            console.print(f"  {emoji} {todo['content']}")
    else:
        console.print("\n[bold]TODOs:[/bold] None")
    
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════════[/bold cyan]\n")


def _is_valid_base64(s):
    """Check if a string is valid base64.
    
    Args:
        s: String to check
        
    Returns:
        bool: True if valid base64, False otherwise
    """
    # Base64 pattern: alphanumeric + / and + characters, with optional = padding
    base64_pattern = re.compile(r'^[A-Za-z0-9+/]+={0,2}$')
    
    if not base64_pattern.match(s):
        return False
    
    # Check if length is valid (must be multiple of 4)
    if len(s) % 4 != 0:
        return False
    
    return True


def save_campaign_output(state, output_dir="campaign_output"):
    """Save all campaign files to disk for review, including decoded images.
    
    FIXED VERSION - Filters out URL_error_* files from output
    
    This function:
    1. Filters out error files (URL_error_*.md)
    2. Saves all valid text files from the virtual filesystem
    3. Automatically detects image data files (post_image_data_*.txt)
    4. Decodes base64 image data and saves as PNG files
    
    Args:
        state: MarketingCampaignState object
        output_dir: Directory to save files to (default: 'campaign_output')
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    files = state.get("files", {})
    text_files_saved = 0
    images_decoded = 0
    
    # ============================================================================
    # NEW: Filter out error files before processing
    # ============================================================================
    valid_files = {}
    skipped_files = []
    
    for filename, content in files.items():
        # Skip URL error files - these are failed web fetches
        if filename.startswith("URL_error_"):
            skipped_files.append(filename)
            continue
        
        # Keep all other files
        valid_files[filename] = content
    
    # Report skipped files
    if skipped_files:
        console.print(f"\n[yellow]⊘ Skipping {len(skipped_files)} error file(s):[/yellow]")
        for filename in skipped_files:
            console.print(f"   [dim]{filename}[/dim]")
        console.print()
    
    # ============================================================================
    # Process all valid files (existing code continues)
    # ============================================================================
    for filename, content in valid_files.items():
        filepath = os.path.join(output_dir, filename)
        
        # Check if this is an image data file (base64) - handle multiple types
        is_image_data_file = (
            (filename.startswith("post_image_data_") and filename.endswith(".txt")) or
            (filename.startswith("metrics_chart_data_") and filename.endswith(".txt")) or
            (filename == "iteration_comparison_chart_data.txt")
        )
        
        if is_image_data_file:
            # Save the text file first
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                text_files_saved += 1
                console.print(f"[green]✓[/green] Saved: {filepath}")
            except Exception as e:
                console.print(f"[red]✗[/red] Error saving {filepath}: {str(e)}")
                continue
            
            # Try to decode and save as PNG
            try:
                # Determine output PNG filename based on input filename type
                if filename.startswith("post_image_data_v"):
                    # DALL-E generated images (e.g., post_image_data_v1.txt -> post_image_v1.png)
                    parts = filename.replace("post_image_data_v", "").replace(".txt", "").split("_")
                    iteration = parts[0]
                    image_filename = f"post_image_v{iteration}.png"
                elif filename.startswith("metrics_chart_data_v"):
                    # Metrics chart images (e.g., metrics_chart_data_v1.txt -> metrics_chart_v1.png)
                    parts = filename.replace("metrics_chart_data_v", "").replace(".txt", "").split("_")
                    iteration = parts[0]
                    image_filename = f"metrics_chart_v{iteration}.png"
                elif filename == "iteration_comparison_chart_data.txt":
                    # Comparison chart (iteration_comparison_chart_data.txt -> iteration_comparison_chart.png)
                    image_filename = "iteration_comparison_chart.png"
                else:
                    # Generic fallback
                    image_filename = filename.replace("_data.txt", ".png")
                
                # Find base64 data in the content
                # New visualization tools save pure base64, old image tools might have formatting
                b64_data = None
                
                # First, try treating entire content as base64 (for visualization charts)
                content_stripped = content.strip()
                if len(content_stripped) > 1000 and _is_valid_base64(content_stripped):
                    b64_data = content_stripped
                else:
                    # Fall back to line-by-line search (for DALL-E images)
                    lines = content.split('\n')
                    for line in lines:
                        line_stripped = line.strip()
                        if len(line_stripped) > 1000 and _is_valid_base64(line_stripped):
                            b64_data = line_stripped
                            break
                
                if b64_data:
                    # Decode base64 to bytes
                    try:
                        image_bytes = base64.b64decode(b64_data)
                        
                        # Verify it's actually image data (PNG starts with specific bytes)
                        if len(image_bytes) > 8:
                            # PNG magic number: 89 50 4E 47 0D 0A 1A 0A
                            png_header = b'\x89PNG\r\n\x1a\n'
                            is_png = image_bytes[:8] == png_header
                            
                            if is_png or len(image_bytes) > 10000:  # Accept if > 10KB (likely an image)
                                # Save as PNG (filename already determined above)
                                image_path = os.path.join(output_dir, image_filename)
                                
                                with open(image_path, 'wb') as f:
                                    f.write(image_bytes)
                                
                                images_decoded += 1
                                console.print(f"[green]✅[/green] Decoded and saved image: {image_path} ({len(image_bytes):,} bytes)")
                            else:
                                console.print(f"[yellow]⚠️ [/yellow] Decoded data from {filename} doesn't appear to be a valid PNG")
                        else:
                            console.print(f"[yellow]⚠️ [/yellow] Decoded data from {filename} is too small to be an image")
                    
                    except Exception as e:
                        console.print(f"[yellow]⚠️ [/yellow] Could not decode base64 from {filename}: {str(e)}")
                else:
                    console.print(f"[yellow]⚠️ [/yellow] Could not find valid base64 data in {filename}")
                
            except Exception as e:
                console.print(f"[yellow]⚠️ [/yellow] Error processing image from {filename}: {str(e)}")
        
        else:
            # Regular text file - save normally
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                text_files_saved += 1
                console.print(f"[green]✓[/green] Saved: {filepath}")
            except Exception as e:
                console.print(f"[red]✗[/red] Error saving {filepath}: {str(e)}")
    
    # Print summary
    console.print(f"\n[bold green]{'='*40}[/bold green]")
    console.print(f"[bold green]Successfully saved {text_files_saved} file(s) to '{output_dir}/'[/bold green]")
    if images_decoded > 0:
        console.print(f"[bold green]Decoded and saved {images_decoded} image(s) as PNG[/bold green]")
    if skipped_files:
        console.print(f"[yellow]Skipped {len(skipped_files)} error file(s)[/yellow]")
    console.print(f"[bold green]{'='*40}[/bold green]")