"""
CLI tool for generating memos from terminal
"""
import click
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from app.services.pipeline import run_memo_pipeline
from app.core.models import DEFAULT_TEMPLATE
from app.services.template_parser import TemplateParser
from app.utils.ollama_setup import get_ollama_status, setup_ollama_automatically


def format_confidence_table(confidence_scores: dict) -> str:
    """Format confidence scores as a table"""
    if not confidence_scores:
        return "  No confidence scores available"
    
    lines = []
    for section, score in confidence_scores.items():
        # Format section name (replace underscores with spaces, title case)
        section_name = section.replace("_", " ").title()
        # Color code based on score
        if score >= 0.8:
            indicator = "🟢"
        elif score >= 0.6:
            indicator = "🟡"
        else:
            indicator = "🔴"
        lines.append(f"  {indicator} {section_name:25} {score:.2f}")
    
    return "\n".join(lines)


def format_flagged_items(flagged_items: List[dict]) -> str:
    """Format flagged items for display"""
    if not flagged_items:
        return "  None"
    
    lines = []
    for item in flagged_items:
        section = item.get("section", "unknown")
        reason = item.get("reason", "Unknown reason")
        lines.append(f"  ⚠️  {section}: {reason}")
        
        if item.get("missing_data"):
            missing = ", ".join(item["missing_data"])
            lines.append(f"     Missing: {missing}")
        
        if item.get("inconsistencies"):
            inconsistencies = ", ".join(item["inconsistencies"])
            lines.append(f"     Inconsistencies: {inconsistencies}")
    
    return "\n".join(lines)


def format_uncertainty_flags(uncertainty_flags: List[dict]) -> str:
    """Format uncertainty flags for display"""
    if not uncertainty_flags:
        return "  None"
    
    lines = []
    for flag in uncertainty_flags:
        section = flag.get("section", "unknown")
        data_type = flag.get("data_type", "unknown")
        flag_text = flag.get("flag", "unknown")
        lines.append(f"  ⚠️  {section} ({data_type}): {flag_text}")
    
    return "\n".join(lines)


def save_memo_to_file(
    memo_content: str,
    confidence_scores: dict,
    flagged_items: List[dict],
    uncertainty_flags: List[dict],
    output_path: Path,
    company_name: str,
    funding_stage: str
) -> None:
    """Save memo and metadata to markdown file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"""# Investment Memo: {company_name}

**Funding Stage:** {funding_stage}  
**Generated:** {timestamp}

---

## Memo Content

{memo_content}

---

## Metadata

### Confidence Scores

"""
    
    if confidence_scores:
        for section, score in confidence_scores.items():
            section_name = section.replace("_", " ").title()
            content += f"- **{section_name}**: {score:.2f}\n"
    else:
        content += "No confidence scores available.\n"
    
    content += "\n### Flagged Items\n\n"
    if flagged_items:
        for item in flagged_items:
            section = item.get("section", "unknown")
            reason = item.get("reason", "Unknown reason")
            content += f"- **{section}**: {reason}\n"
            if item.get("missing_data"):
                content += f"  - Missing: {', '.join(item['missing_data'])}\n"
            if item.get("inconsistencies"):
                content += f"  - Inconsistencies: {', '.join(item['inconsistencies'])}\n"
    else:
        content += "None\n"
    
    content += "\n### Uncertainty Flags\n\n"
    if uncertainty_flags:
        for flag in uncertainty_flags:
            section = flag.get("section", "unknown")
            data_type = flag.get("data_type", "unknown")
            flag_text = flag.get("flag", "unknown")
            content += f"- **{section}** ({data_type}): {flag_text}\n"
    else:
        content += "None\n"
    
    output_path.write_text(content, encoding="utf-8")


@click.command()
@click.option(
    "--files",
    multiple=True,
    required=True,
    help="File paths to process (can specify multiple times)"
)
@click.option(
    "--company-name",
    required=True,
    help="Company name"
)
@click.option(
    "--funding-stage",
    required=True,
    help="Funding stage (e.g., 'Series A')"
)
@click.option(
    "--template",
    type=click.Path(exists=True),
    help="Optional template file path"
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file path (default: memo_{timestamp}.md)"
)
@click.option(
    "--no-file",
    is_flag=True,
    help="Disable file output, show in terminal only"
)
def generate_memo(
    files: tuple,
    company_name: str,
    funding_stage: str,
    template: Optional[str],
    output: Optional[str],
    no_file: bool
):
    """Generate investment memo from deal documents"""
    
    # Validate files exist
    file_paths = [Path(f) for f in files]
    missing_files = [f for f in file_paths if not f.exists()]
    if missing_files:
        click.echo(f"❌ Error: Files not found: {', '.join(str(f) for f in missing_files)}", err=True)
        return
    
    # Prepare documents
    documents = []
    for file_path in file_paths:
        with open(file_path, "rb") as f:
            content = f.read()
        
        # Determine content type
        ext = file_path.suffix.lower()
        content_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".txt": "text/plain",
            ".md": "text/markdown",
        }
        content_type = content_types.get(ext, "application/octet-stream")
        
        documents.append({
            "filename": file_path.name,
            "content": content,
            "content_type": content_type,
        })
    
    # Parse template if provided
    template_structure = DEFAULT_TEMPLATE
    if template:
        try:
            parser = TemplateParser()
            template_structure = parser.parse_template_file(template)
            click.echo(f"✓ Loaded template from {template}")
        except Exception as e:
            click.echo(f"⚠️  Failed to load template: {e}. Using default template.", err=True)
    
    # Check and setup Ollama if needed
    click.echo("\n" + "=" * 70)
    click.echo("CHECKING OLLAMA STATUS")
    click.echo("=" * 70)
    
    installed, running, model_available, status_message = get_ollama_status()
    click.echo(f"Status: {status_message}")
    
    # Check if auto-setup is enabled
    auto_setup = os.getenv("OLLAMA_AUTO_SETUP", "false").lower() == "true"
    auto_install = os.getenv("OLLAMA_AUTO_INSTALL", "false").lower() == "true"
    
    if not (installed and running and model_available):
        if auto_setup:
            click.echo("\n🔧 Auto-setup enabled, configuring Ollama...")
            try:
                success, setup_msg = asyncio.run(
                    setup_ollama_automatically(auto_install=auto_install)
                )
                if success:
                    click.echo(f"✅ {setup_msg}")
                    # Re-check status after setup
                    installed, running, model_available, status_message = get_ollama_status()
                else:
                    click.echo(f"⚠️  {setup_msg}")
                    click.echo("   Continuing with OpenAI fallback...")
            except Exception as e:
                click.echo(f"⚠️  Auto-setup failed: {e}")
                click.echo("   Continuing with OpenAI fallback...")
        else:
            click.echo("\n💡 Tip: Set OLLAMA_AUTO_SETUP=true to auto-configure Ollama")
            click.echo("   For now, using OpenAI for all extractions")
    else:
        click.echo("✅ Ollama ready - will be used for non-critical extractions (market, company, team)")
    
    click.echo("")
    
    # Generate memo
    click.echo("=" * 70)
    click.echo("GENERATING INVESTMENT MEMO")
    click.echo("=" * 70)
    click.echo(f"Company: {company_name}")
    click.echo(f"Funding Stage: {funding_stage}")
    click.echo(f"Files: {len(documents)}")
    click.echo("")
    click.echo("⏳ Starting pipeline... This may take a few minutes.")
    click.echo("   You'll see progress updates as it processes.\n")
    
    import sys
    sys.stdout.flush()  # Ensure output is visible
    
    try:
        result = asyncio.run(
            run_memo_pipeline(
                job_id="cli_job",
                documents=documents,
                template_structure=template_structure
            )
        )
        
        if not result.get("success"):
            click.echo(f"❌ Error: {result.get('error', 'Unknown error')}", err=True)
            return
        
        # Display results
        click.echo("\n" + "=" * 70)
        click.echo("GENERATED MEMO")
        click.echo("=" * 70)
        memo_content = result.get("memo_content", "")
        click.echo(memo_content)
        
        # Cost summary note
        click.echo("\n" + "=" * 70)
        click.echo("COST SUMMARY")
        click.echo("=" * 70)
        click.echo("💡 Cost breakdown shown above for each operation:")
        click.echo("   - Ollama: FREE (local processing)")
        click.echo("   - GPT-4o: ~$2.50 per 1M input tokens, ~$10.00 per 1M output tokens")
        click.echo("   - GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens")
        click.echo("   - Cache hits: FREE (no API call)")
        click.echo("\n   Review the extraction and generation logs above for detailed costs.")
        
        # Confidence scores
        confidence_scores = result.get("confidence_scores", {})
        if confidence_scores:
            click.echo("\n" + "=" * 70)
            click.echo("CONFIDENCE SCORES")
            click.echo("=" * 70)
            click.echo(format_confidence_table(confidence_scores))
        
        # Flagged items
        flagged_items = result.get("flagged_items", [])
        if flagged_items:
            click.echo("\n" + "=" * 70)
            click.echo(f"FLAGGED ITEMS ({len(flagged_items)})")
            click.echo("=" * 70)
            click.echo(format_flagged_items(flagged_items))
        
        # Uncertainty flags
        uncertainty_flags = result.get("uncertainty_flags", [])
        if uncertainty_flags:
            click.echo("\n" + "=" * 70)
            click.echo(f"UNCERTAINTY FLAGS ({len(uncertainty_flags)})")
            click.echo("=" * 70)
            click.echo(format_uncertainty_flags(uncertainty_flags))
        
        # Save to file if not disabled
        if not no_file:
            if output:
                output_path = Path(output)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_company = "".join(c for c in company_name if c.isalnum() or c in (" ", "-", "_")).strip()
                safe_company = safe_company.replace(" ", "_")
                output_path = Path(f"memo_{safe_company}_{timestamp}.md")
            
            save_memo_to_file(
                memo_content,
                confidence_scores,
                flagged_items,
                uncertainty_flags,
                output_path,
                company_name,
                funding_stage
            )
            
            click.echo("\n" + "=" * 70)
            click.echo(f"✅ Memo saved to: {output_path.absolute()}")
            click.echo("=" * 70)
        
    except Exception as e:
        click.echo(f"❌ Error generating memo: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)


if __name__ == "__main__":
    generate_memo()

