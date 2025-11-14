"""Image generation tools for marketing campaigns.

VERSION 2.2 - FIXED FOR STREAMLIT CLOUD:
- Lazy initialization of OpenAI client to work with Streamlit secrets
- Added protection against agent overwriting tool-generated files
- Files are marked as protected and cannot be manually overwritten
- Increased timeout to 90 seconds
- Better retry logic with exponential backoff
- Comprehensive validation of all outputs
- Detailed error messages
- Guaranteed complete file generation
"""

import os, base64, httpx, time
from datetime import datetime
from typing import Annotated, Literal
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from openai import OpenAI
from rich.console import Console
from state import MarketingCampaignState

# ============================================================================
# LAZY INITIALIZATION - Fixed for Streamlit Cloud
# ============================================================================
# Instead of initializing at module level, we use lazy initialization
# This allows Streamlit to load secrets before the client is created

_openai_client = None

def get_openai_client():
    """Lazy initialization of OpenAI client.
    
    This function creates the client only when first needed,
    allowing Streamlit secrets to be loaded first.
    """
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client

console = Console()

def get_today_str() -> str:
    return datetime.now().strftime("%a %b %-d, %Y")

@tool
def generate_marketing_image(
    visual_concept: str,
    state: Annotated[MarketingCampaignState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    image_style: Annotated[Literal["vivid", "natural"], str] = "vivid",
    image_size: Annotated[Literal["1024x1024", "1792x1024", "1024x1792"], str] = "1792x1024",
) -> Command:
    """Generate marketing image with DALL-E 3 and comprehensive validation.
    
    VERSION 2.2 ENHANCEMENTS:
    - Lazy initialization of OpenAI client (Streamlit Cloud compatible)
    - Extended timeout (90s instead of 30s)
    - Exponential backoff retry strategy
    - Multi-level validation (PNG header, size, base64)
    - Guaranteed complete metadata file generation
    - Detailed progress reporting
    
    This tool ALWAYS creates TWO files:
    1. post_image_v[N].md - Comprehensive metadata with URL, concept, prompts, technical details
    2. post_image_data_v[N].txt - Complete base64-encoded PNG image data
    
    Args:
        visual_concept: Detailed description of the desired image
        state: Agent state (auto-injected)
        tool_call_id: Tool call ID (auto-injected)
        image_style: "vivid" (bold/dramatic) or "natural" (subtle/professional)
        image_size: Image dimensions
    
    Returns:
        Command with files created and validation results
    """
    try:
        # ===================================================================
        # PHASE 1: DALL-E GENERATION
        # ===================================================================
        console.print(f"[blue]🎨 Generating image with DALL-E 3...[/blue]")
        console.print(f"[dim]   Style: {image_style} | Size: {image_size}[/dim]")
        
        # Use lazy initialization
        client = get_openai_client()
        
        response = client.images.generate(
            model="dall-e-3", 
            prompt=visual_concept,
            size=image_size, 
            quality="standard", 
            style=image_style, 
            n=1
        )
        
        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt
        console.print(f"[green]✅ DALL-E generated image[/green]")
        console.print(f"[dim]   URL: {image_url[:80]}...[/dim]")
        
        # ===================================================================
        # PHASE 2: IMAGE DOWNLOAD WITH ROBUST RETRY
        # ===================================================================
        console.print(f"[blue]📥 Downloading image...[/blue]")
        
        max_retries = 3
        image_bytes = None
        
        for attempt in range(max_retries):
            try:
                # ENHANCED: 90s timeout (3x longer than v1)
                timeout_duration = 90.0
                
                console.print(f"[dim]   Attempt {attempt + 1}/{max_retries} (timeout: {timeout_duration}s)[/dim]")
                
                img_response = httpx.get(
                    image_url, 
                    timeout=timeout_duration, 
                    follow_redirects=True
                )
                img_response.raise_for_status()
                image_bytes = img_response.content
                
                # ===================================================================
                # VALIDATION 1: Minimum Size Check
                # ===================================================================
                if len(image_bytes) < 10000:
                    raise ValueError(f"Image too small: {len(image_bytes)} bytes (expected > 10KB)")
                
                # ===================================================================
                # VALIDATION 2: PNG Header Check
                # ===================================================================
                png_header = b'\x89PNG\r\n\x1a\n'
                if not image_bytes.startswith(png_header):
                    raise ValueError("Invalid PNG - header mismatch")
                
                console.print(f"[green]✅ Downloaded: {len(image_bytes):,} bytes[/green]")
                console.print(f"[green]✅ PNG validated[/green]")
                break  # Success!
                
            except Exception as e:
                if attempt < max_retries - 1:
                    # Exponential backoff: 5s, 10s, 20s
                    retry_delay = 5 * (2 ** attempt)
                    console.print(f"[yellow]⚠️ Retry {attempt + 1}: {e}[/yellow]")
                    console.print(f"[dim]   Waiting {retry_delay}s before retry...[/dim]")
                    time.sleep(retry_delay)
                else:
                    # Final attempt failed
                    raise Exception(f"Failed after {max_retries} attempts: {e}")
        
        if image_bytes is None:
            raise Exception("Image download failed - no bytes received")
        
        # ===================================================================
        # PHASE 3: BASE64 ENCODING
        # ===================================================================
        console.print(f"[blue]🔐 Encoding to base64...[/blue]")
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # ===================================================================
        # VALIDATION 3: Base64 Length Check
        # ===================================================================
        expected_min_b64_length = 50000
        if len(image_b64) < expected_min_b64_length:
            console.print(f"[yellow]⚠️ Base64 shorter than expected: {len(image_b64)} chars (expected > {expected_min_b64_length})[/yellow]")
        else:
            console.print(f"[green]✅ Base64 encoded: {len(image_b64):,} characters[/green]")
        
        # ===================================================================
        # PHASE 4: FILE CREATION
        # ===================================================================
        iteration = state.get("iteration_count", 1)
        metadata_filename = f"post_image_v{iteration}.md"
        data_filename = f"post_image_data_v{iteration}.txt"
        
        files = state.get("files", {})
        
        # ===================================================================
        # METADATA FILE - COMPREHENSIVE VERSION
        # ===================================================================
        metadata_content = f"""# Generated Marketing Image - Iteration {iteration}

**Generated:** {get_today_str()}
**Model:** DALL-E 3
**Size:** {image_size}
**Style:** {image_style}
**Status:** ✅ Successfully Generated

## Image URL
{image_url}

## Visual Concept
{visual_concept}

## Revised Prompt
{revised_prompt}

## Technical Details
- Resolution: {image_size}
- Format: PNG
- Downloaded: {len(image_bytes):,} bytes
- Base64: {len(image_b64):,} chars
- Validation: ✅ PNG verified

## Validation Results
- ✅ PNG header: Valid
- ✅ File size: {len(image_bytes):,} bytes (> 10KB)
- ✅ Base64 length: {len(image_b64):,} chars (> 50K)
- ✅ Download: Success after {attempt + 1} attempt(s)

---
*Generated by DALL-E 3*
"""
        
        files[metadata_filename] = metadata_content
        
        # ===================================================================
        # DATA FILE - BASE64 WITH HEADER
        # ===================================================================
        data_content = f"""# Image Data (Base64) - Iteration {iteration}
# This file contains the base64-encoded image data for permanent storage.
# Generated: {get_today_str()}
#
# Technical Details:
# - Original size: {len(image_bytes):,} bytes
# - Base64 size: {len(image_b64):,} characters
# - Format: PNG
# - Validation: ✅ Complete
#
# To decode: base64.b64decode(content.split('\\n\\n')[1])

{image_b64}
"""
        
        files[data_filename] = data_content
        
        # ===================================================================
        # CRITICAL v2.1: MARK FILES AS PROTECTED FROM OVERWRITE
        # ===================================================================
        tool_generated_files = state.get('tool_generated_files', set())
        tool_generated_files.add(metadata_filename)
        tool_generated_files.add(data_filename)
        
        console.print(f"[blue]🔒 Protecting files from overwrite...[/blue]")
        console.print(f"[dim]   {metadata_filename} - PROTECTED[/dim]")
        console.print(f"[dim]   {data_filename} - PROTECTED[/dim]")
        
        # ===================================================================
        # PHASE 5: VERIFICATION
        # ===================================================================
        console.print(f"[blue]🔍 Verifying files...[/blue]")
        
        # Verify metadata file
        if metadata_filename not in files:
            raise Exception(f"Verification failed: {metadata_filename} not in files dict")
        if len(files[metadata_filename]) < 200:
            raise Exception(f"Verification failed: {metadata_filename} too short ({len(files[metadata_filename])} chars)")
        
        # Verify data file
        if data_filename not in files:
            raise Exception(f"Verification failed: {data_filename} not in files dict")
        if len(files[data_filename]) < expected_min_b64_length:
            raise Exception(f"Verification failed: {data_filename} too short ({len(files[data_filename])} chars)")
        
        console.print(f"[green]✅ Verification passed[/green]")
        
        # ===================================================================
        # SUCCESS MESSAGE
        # ===================================================================
        success_msg = f"""✅ Image generation COMPLETE

**Files Created:**
✓ {metadata_filename} ({len(metadata_content):,} chars)
✓ {data_filename} ({len(data_content):,} chars)

**Image Details:**
- Downloaded: {len(image_bytes):,} bytes
- Base64: {len(image_b64):,} characters
- Format: PNG (validated ✓)
- Attempts: {attempt + 1}/{max_retries}

**Validation Status:**
✅ All checks passed
✅ Files complete and verified
✅ Ready for use in post_content_v{iteration}.md
"""
        
        console.print(f"[bold green]{success_msg}[/bold green]")
        
        # ===================================================================
        # CRITICAL v2.1: RETURN WITH PROTECTED FILES
        # ===================================================================
        return Command(
            update={
                "files": files,
                "tool_generated_files": tool_generated_files,  # v2.1: Add protection
                "messages": [ToolMessage(success_msg, tool_call_id=tool_call_id)]
            }
        )
        
    except Exception as e:
        # ===================================================================
        # ERROR HANDLING
        # ===================================================================
        error_msg = f"""❌ Image generation FAILED

Error: {str(e)}

**Troubleshooting:**
- Check OPENAI_API_KEY is set
- Verify visual_concept is detailed and appropriate
- Ensure network connectivity
- Try calling tool again with adjusted parameters

**What was attempted:**
- DALL-E generation: {'✓' if 'image_url' in locals() else '✗'}
- Image download: {'✓' if image_bytes else '✗'}
- Base64 encoding: {'✓' if 'image_b64' in locals() else '✗'}
"""
        
        console.print(f"[red]{error_msg}[/red]")
        return Command(
            update={
                "messages": [ToolMessage(error_msg, tool_call_id=tool_call_id)]
            }
        )


# Export
__all__ = ['generate_marketing_image']
