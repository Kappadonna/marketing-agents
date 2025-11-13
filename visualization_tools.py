"""Visualization tools for creating marketing campaign charts and graphs.

VERSION 2.1 - CRITICAL FIX:
- Added protection against agent overwriting tool-generated chart files
- Chart files are marked as protected and cannot be manually overwritten
- This prevents agents from destroying complete charts with placeholders

This module provides tools for generating visual representations of campaign metrics,
including comparison charts, performance graphs, and metric dashboards.
"""

import json
import base64
from io import BytesIO
from typing import Annotated, Literal
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command
from langgraph.prebuilt import InjectedState

from state import MarketingCampaignState


def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")


@tool
def create_metrics_chart(
    metrics_data: str,
    chart_title: str,
    state: Annotated[MarketingCampaignState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    chart_type: Annotated[Literal["bar", "line", "subplot"], str] = "subplot",
) -> Command:
    """Create a visual chart from campaign metrics data and save as PNG.
    
    This tool generates professional-looking charts comparing actual metrics against
    thresholds. Perfect for visualizing campaign performance at the end of iterations.
    
    Args:
        metrics_data: JSON string containing metrics with 'actual' and 'threshold' values.
                     Format: {"metric_name": {"actual": value, "threshold": value}, ...}
        chart_title: Title for the chart (e.g., "Campaign Performance Metrics")
        state: Injected agent state
        tool_call_id: Injected tool call identifier
        chart_type: Type of chart - "bar", "line", or "subplot" (default: subplot with separate panels)
    
    Returns:
        Command with chart saved to files and success message
        
    Example metrics_data:
        {
            "engagement_rate": {"actual": 2.5, "threshold": 2.0},
            "reach": {"actual": 15000, "threshold": 10000},
            "ctr": {"actual": 1.8, "threshold": 1.5}
        }
    """
    try:
        # Parse the metrics data
        metrics = json.loads(metrics_data)
        
        # Get iteration count
        iteration = state.get("iteration_count", 1)
        
        # Prepare data for plotting
        metric_names = list(metrics.keys())
        num_metrics = len(metric_names)
        
        if chart_type == "subplot":
            # Create figure with subplots - one for each metric
            fig, axes = plt.subplots(1, num_metrics, figsize=(6*num_metrics, 5))
            
            # If only one metric, axes is not a list
            if num_metrics == 1:
                axes = [axes]
            
            # Define colors for bars (light blue, light green, light red/pink)
            bar_colors = ['#87CEEB', '#90EE90', '#FFB6C1']
            
            for idx, (metric_name, ax) in enumerate(zip(metric_names, axes)):
                metric_data = metrics[metric_name]
                actual = metric_data["actual"]
                threshold = metric_data["threshold"]
                
                # Create bar for actual value
                bar_color = bar_colors[idx % len(bar_colors)]
                ax.bar([iteration], [actual], width=0.6, 
                      color=bar_color, alpha=0.7, label='Valore Reale')
                
                # Add threshold line
                ax.axhline(y=threshold, color='red', linestyle='--', 
                          linewidth=2, label=f'Soglia ({threshold:,.0f})')
                
                # Customize subplot
                metric_display = metric_name.replace('_', ' ').title()
                ax.set_title(metric_display, fontsize=12, fontweight='bold')
                ax.set_xlabel('Iterazione', fontsize=10)
                ax.set_ylabel(metric_display.split()[0] if len(metric_display.split()) > 1 else 'Value', 
                             fontsize=10)
                
                # Set x-axis
                ax.set_xlim(0.5, iteration + 0.5)
                ax.set_xticks([iteration])
                ax.set_xticklabels([f'{iteration}.0'])
                
                # Add legend
                ax.legend(fontsize=9, loc='upper right')
                
                # Add grid
                ax.grid(axis='y', alpha=0.3, linestyle='--')
                ax.set_facecolor('#F5F5F5')
            
            # Main title
            fig.suptitle(chart_title, fontsize=16, fontweight='bold', y=1.02)
            fig.patch.set_facecolor('white')
            
        else:
            # Original bar/line chart implementations
            actual_values = [metrics[m]["actual"] for m in metric_names]
            threshold_values = [metrics[m]["threshold"] for m in metric_names]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            x = np.arange(len(metric_names))
            width = 0.35
            
            if chart_type == "bar":
                bars1 = ax.bar(x - width/2, actual_values, width, 
                              label='Actual', color='#2E86AB', alpha=0.8)
                bars2 = ax.bar(x + width/2, threshold_values, width,
                              label='Threshold', color='#A23B72', alpha=0.8)
                
                for bars in [bars1, bars2]:
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:,.1f}',
                               ha='center', va='bottom', fontsize=9)
            
            else:  # line chart
                ax.plot(x, actual_values, marker='o', linewidth=2, 
                       label='Actual', color='#2E86AB', markersize=8)
                ax.plot(x, threshold_values, marker='s', linewidth=2, linestyle='--',
                       label='Threshold', color='#A23B72', markersize=8)
                
                for i, (actual, threshold) in enumerate(zip(actual_values, threshold_values)):
                    ax.text(i, actual, f'{actual:,.1f}', ha='center', va='bottom', fontsize=9)
                    ax.text(i, threshold, f'{threshold:,.1f}', ha='center', va='top', fontsize=9)
            
            ax.set_xlabel('Metrics', fontsize=12, fontweight='bold')
            ax.set_ylabel('Values', fontsize=12, fontweight='bold')
            ax.set_title(chart_title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xticks(x)
            ax.set_xticklabels([m.replace('_', ' ').title() for m in metric_names])
            ax.legend(fontsize=10)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            ax.set_facecolor('#F8F9FA')
            fig.patch.set_facecolor('white')
        
        # Tight layout
        plt.tight_layout()
        
        # Save to BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        
        # Convert to base64
        img_bytes = buf.read()
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
        # Close the figure to free memory
        plt.close(fig)
        
        # Create filenames with iteration number
        chart_filename = f"metrics_chart_v{iteration}.png"
        chart_data_filename = f"metrics_chart_data_v{iteration}.txt"
        chart_metadata_filename = f"metrics_chart_v{iteration}.md"
        
        # Get files from state
        files = state.get("files", {})
        
        # Save base64 encoded image
        files[chart_data_filename] = img_b64
        
        # Save metadata
        metadata_content = f"""# Metrics Performance Chart - Iteration {iteration}

**Generated:** {get_today_str()}
**Chart Type:** {chart_type.title()} Chart
**Title:** {chart_title}

## Metrics Visualized

"""
        for metric, values in metrics.items():
            metric_display = metric.replace('_', ' ').title()
            actual = values["actual"]
            threshold = values["threshold"]
            performance = "✅ Above Threshold" if actual >= threshold else "⚠️ Below Threshold"
            
            metadata_content += f"""### {metric_display}
- **Actual:** {actual:,.2f}
- **Threshold:** {threshold:,.2f}
- **Status:** {performance}

"""
        
        metadata_content += f"""## Chart Details
- **Resolution:** 300 DPI
- **Format:** PNG
- **Size:** {len(img_bytes):,} bytes
- **Iteration:** {iteration}

## How to View
The chart is saved as:
1. **PNG Image**: Decode base64 from `{chart_data_filename}`
2. **Metadata**: This file with interpretation

---
*Chart generated by Marketing Campaign Analytics System*
"""
        
        files[chart_metadata_filename] = metadata_content
        
        # ===================================================================
        # CRITICAL v2.1: MARK CHART FILES AS PROTECTED FROM OVERWRITE
        # ===================================================================
        tool_generated_files = state.get('tool_generated_files', set())
        tool_generated_files.add(chart_metadata_filename)
        tool_generated_files.add(chart_data_filename)
        
        # Return success message
        message = f"""✅ Chart generated successfully!

**Files Created:**
- `{chart_metadata_filename}` - Chart metadata and metrics summary
- `{chart_data_filename}` - Base64 encoded PNG image

**Metrics Visualized:** {', '.join([m.replace('_', ' ').title() for m in metric_names])}
**Iteration:** {iteration}

The chart compares actual campaign performance against thresholds. All files are saved in the virtual filesystem and will be included in campaign output.
"""
        
        # ===================================================================
        # CRITICAL v2.1: RETURN WITH PROTECTED FILES
        # ===================================================================
        return Command(
            update={
                "files": files,
                "tool_generated_files": tool_generated_files,  # v2.1: Add protection
                "messages": [{"role": "tool", "content": message, "tool_call_id": tool_call_id}]
            }
        )
        
    except json.JSONDecodeError as e:
        error_msg = f"❌ Error: Invalid JSON format in metrics_data. {str(e)}"
        return Command(
            update={
                "messages": [{"role": "tool", "content": error_msg, "tool_call_id": tool_call_id}]
            }
        )
    except Exception as e:
        error_msg = f"❌ Error generating chart: {str(e)}"
        return Command(
            update={
                "messages": [{"role": "tool", "content": error_msg, "tool_call_id": tool_call_id}]
            }
        )


@tool
def create_iteration_comparison_chart(
    iterations_data: str,
    state: Annotated[MarketingCampaignState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Create a chart comparing metrics across multiple campaign iterations.
    
    This tool generates a multi-series chart showing how metrics evolved across iterations,
    perfect for the final campaign summary.
    
    Args:
        iterations_data: JSON string with metrics for each iteration.
                        Format: {"iteration_1": {"metric": value, ...}, "iteration_2": {...}}
        state: Injected agent state
        tool_call_id: Injected tool call identifier
    
    Returns:
        Command with comparison chart saved and success message
    """
    try:
        # Parse iterations data
        iterations = json.loads(iterations_data)
        
        # Get number of iterations
        num_iterations = len(iterations)
        
        # Extract metrics and iterations
        iteration_labels = sorted(iterations.keys())
        
        # Get all unique metrics
        all_metrics = set()
        for iter_data in iterations.values():
            all_metrics.update(iter_data.keys())
        
        metrics_list = sorted(list(all_metrics))
        
        # Prepare data for each metric
        data_by_metric = {metric: [] for metric in metrics_list}
        for iter_label in iteration_labels:
            iter_data = iterations[iter_label]
            for metric in metrics_list:
                data_by_metric[metric].append(iter_data.get(metric, 0))
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Plot lines for each metric
        x = np.arange(len(iteration_labels))
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']
        
        for i, (metric, values) in enumerate(data_by_metric.items()):
            color = colors[i % len(colors)]
            ax.plot(x, values, marker='o', linewidth=2.5, label=metric.replace('_', ' ').title(),
                   color=color, markersize=10)
            
            # Add value labels
            for j, val in enumerate(values):
                ax.text(j, val, f'{val:,.1f}', ha='center', va='bottom', fontsize=9)
        
        # Customize
        ax.set_xlabel('Campaign Iteration', fontsize=12, fontweight='bold')
        ax.set_ylabel('Metric Values', fontsize=12, fontweight='bold')
        ax.set_title('Campaign Performance Across Iterations', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels([label.replace('_', ' ').title() for label in iteration_labels])
        ax.legend(fontsize=10, loc='best')
        ax.grid(axis='both', alpha=0.3, linestyle='--')
        ax.set_facecolor('#F8F9FA')
        fig.patch.set_facecolor('white')
        
        plt.tight_layout()
        
        # Save to BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        
        # Convert to base64
        img_bytes = buf.read()
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
        plt.close(fig)
        
        # Create filenames
        chart_filename = "iteration_comparison_chart.png"
        chart_data_filename = "iteration_comparison_chart_data.txt"
        chart_metadata_filename = "iteration_comparison_chart.md"
        
        # Get files from state
        files = state.get("files", {})
        
        # Save files
        files[chart_data_filename] = img_b64
        
        metadata_content = f"""# Iteration Comparison Chart

**Generated:** {get_today_str()}
**Iterations Compared:** {num_iterations}
**Metrics Tracked:** {len(metrics_list)}

## Performance Evolution

This chart shows how campaign metrics evolved across {num_iterations} iteration(s).

"""
        
        for metric in metrics_list:
            values = data_by_metric[metric]
            metadata_content += f"""### {metric.replace('_', ' ').title()}
- **Starting Value:** {values[0]:,.2f}
- **Final Value:** {values[-1]:,.2f}
- **Change:** {values[-1] - values[0]:+,.2f} ({((values[-1] - values[0]) / values[0] * 100):+.1f}%)

"""
        
        metadata_content += f"""## Chart Details
- **Resolution:** 300 DPI
- **Format:** PNG
- **Size:** {len(img_bytes):,} bytes

---
*Generated by Marketing Campaign Analytics System*
"""
        
        files[chart_metadata_filename] = metadata_content
        
        # ===================================================================
        # CRITICAL v2.1: MARK COMPARISON CHART FILES AS PROTECTED
        # ===================================================================
        tool_generated_files = state.get('tool_generated_files', set())
        tool_generated_files.add(chart_metadata_filename)
        tool_generated_files.add(chart_data_filename)
        
        message = f"""✅ Iteration comparison chart generated!

**Files Created:**
- `{chart_metadata_filename}` - Chart analysis
- `{chart_data_filename}` - Base64 encoded PNG

**Showing:** Performance trends across {num_iterations} iterations
"""
        
        # ===================================================================
        # CRITICAL v2.1: RETURN WITH PROTECTED FILES
        # ===================================================================
        return Command(
            update={
                "files": files,
                "tool_generated_files": tool_generated_files,  # v2.1: Add protection
                "messages": [{"role": "tool", "content": message, "tool_call_id": tool_call_id}]
            }
        )
        
    except Exception as e:
        error_msg = f"❌ Error creating comparison chart: {str(e)}"
        return Command(
            update={
                "messages": [{"role": "tool", "content": error_msg, "tool_call_id": tool_call_id}]
            }
        )
        

import re
from typing import Annotated

@tool
def extract_all_iteration_metrics(
    state: Annotated[MarketingCampaignState, InjectedState],
) -> str:
    """Estrae automaticamente metriche da tutti i report analytics e ritorna JSON valido.
    
    Questo tool legge tutti i file analytics_report_v*.md nel filesystem,
    estrae le metriche principali, e crea un JSON formattato correttamente
    per essere usato con create_iteration_comparison_chart.
    
    Returns:
        JSON string con formato: {"iteration_1": {"metric": value, ...}, ...}
    """
    files = state.get("files", {})
    iterations_data = {}
    
    # Pattern per estrarre numeri da testo
    number_pattern = r'[-+]?[0-9]*\.?[0-9]+'
    
    # Trova tutti i report analytics
    analytics_files = [f for f in files.keys() if f.startswith("analytics_report_v") and f.endswith(".md")]
    analytics_files.sort()  # Ordina per iterazione
    
    for filename in analytics_files:
        # Estrai numero iterazione
        match = re.search(r'analytics_report_v(\d+)\.md', filename)
        if not match:
            continue
        
        iteration_num = match.group(1)
        iteration_key = f"iteration_{iteration_num}"
        
        content = files[filename]
        metrics = {}
        
        # Cerca Performance Score (obbligatorio)
        score_match = re.search(r'Performance Score:\s*(\d+)/100', content)
        if score_match:
            metrics['performance_score'] = float(score_match.group(1))
        else:
            # Fallback: cerca qualsiasi numero prima di "/100"
            score_match = re.search(r'(\d+)/100', content)
            if score_match:
                metrics['performance_score'] = float(score_match.group(1))
        
        # Cerca altre metriche comuni
        # Engagement Rate
        eng_match = re.search(r'Engagement Rate.*?(\d+\.?\d*)%', content, re.IGNORECASE)
        if eng_match:
            metrics['engagement_rate'] = float(eng_match.group(1))
        
        # Reach / Impressions
        reach_match = re.search(r'(?:Reach|Impressions).*?(\d{1,3}(?:,\d{3})*)', content, re.IGNORECASE)
        if reach_match:
            reach_str = reach_match.group(1).replace(',', '')
            metrics['reach'] = int(reach_str)
        
        # CTR
        ctr_match = re.search(r'CTR.*?(\d+\.?\d*)%', content, re.IGNORECASE)
        if ctr_match:
            metrics['ctr'] = float(ctr_match.group(1))
        
        # Salva solo se abbiamo almeno performance_score
        if 'performance_score' in metrics:
            iterations_data[iteration_key] = metrics
    
    if not iterations_data:
        return json.dumps({
            "error": "No analytics reports found with extractable metrics",
            "available_files": list(files.keys())
        })
    
    # Ritorna JSON valido
    return json.dumps(iterations_data, indent=2)


@tool
def create_iteration_comparison_chart_auto(
    state: Annotated[MarketingCampaignState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Versione automatica che estrae metriche ed crea il chart in un solo step.
    
    Questo tool:
    1. Usa extract_all_iteration_metrics() internamente
    2. Passa il JSON a create_iteration_comparison_chart()
    3. Gestisce errori automaticamente
    
    Uso semplificato per il Project Manager.
    """
    # Estrai metriche
    metrics_json = extract_all_iteration_metrics(state)
    
    # Verifica se c'è errore
    try:
        metrics_data = json.loads(metrics_json)
        if "error" in metrics_data:
            error_msg = f"⚠️ Could not extract metrics: {metrics_data['error']}"
            return Command(update={"messages": [{"role": "tool", "content": error_msg, "tool_call_id": tool_call_id}]})
    except json.JSONDecodeError:
        error_msg = "❌ Invalid JSON from metric extraction"
        return Command(update={"messages": [{"role": "tool", "content": error_msg, "tool_call_id": tool_call_id}]})
    
    # Delega al tool originale
    return create_iteration_comparison_chart(
        iterations_data=metrics_json,
        state=state,
        tool_call_id=tool_call_id
    )