import PyPDF2
from docx import Document as DocxDocument
import io
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from llm_config import get_extraction_llm
import json
import re
import yaml


class TemplateParser:
    """Extract memo structure from example memo documents"""

    def __init__(self):
        self.llm = get_extraction_llm()

    async def parse_template(self, template_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Parse uploaded template document and extract structure"""
        filename = template_doc["filename"]
        content = template_doc["content"]
        file_type = filename.split(".")[-1].lower()

        # Handle YAML templates directly (already structured)
        if file_type in ["yaml", "yml"]:
            return self._parse_yaml_template(content)

        # Extract structured text with headings for other formats
        if file_type == "pdf":
            structured_text = self._extract_pdf_structure(content)
        elif file_type in ["docx", "doc"]:
            structured_text = self._extract_docx_structure(content)
        elif file_type in ["txt", "md"]:
            structured_text = self._extract_text_structure(content)
        else:
            raise ValueError(
                f"Unsupported template file type: {file_type}. Supported: PDF, DOCX, TXT, MD, YAML, YML"
            )

        # Use LLM to extract template structure
        template_structure = await self._extract_template_structure(structured_text)

        return template_structure

    def _extract_pdf_structure(self, content: bytes) -> str:
        """Extract text with basic structure from PDF"""
        structured_lines = []
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    # Split by lines and identify potential headings
                    lines = text.split("\n")
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue

                        # Heuristic: lines that are short, all caps, or start with numbers might be headings
                        is_potential_heading = (
                            len(line.split()) < 10
                            and line.isupper()
                            or re.match(r"^[\d\.]+\s+[A-Z]", line)
                            or re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", line)
                            and len(line.split()) <= 5
                        )

                        if is_potential_heading:
                            structured_lines.append(f"## {line}")
                        else:
                            structured_lines.append(line)

        except Exception as e:
            print(f"Error extracting PDF structure: {e}")

        return "\n".join(structured_lines)

    def _extract_docx_structure(self, content: bytes) -> str:
        """Extract text with structure from DOCX, preserving heading styles"""
        structured_lines = []
        try:
            doc = DocxDocument(io.BytesIO(content))

            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue

                # Check if paragraph has heading style
                style_name = para.style.name.lower() if para.style else ""

                if "heading" in style_name or "title" in style_name:
                    # Determine heading level
                    if "heading 1" in style_name or "title" in style_name:
                        structured_lines.append(f"# {text}")
                    elif "heading 2" in style_name:
                        structured_lines.append(f"## {text}")
                    elif "heading 3" in style_name:
                        structured_lines.append(f"### {text}")
                    else:
                        structured_lines.append(f"## {text}")
                else:
                    # Regular paragraph
                    structured_lines.append(text)

        except Exception as e:
            print(f"Error extracting DOCX structure: {e}")

        return "\n".join(structured_lines)

    def _parse_yaml_template(self, content: bytes) -> Dict[str, Any]:
        """Parse YAML template file directly (no LLM needed)"""
        try:
            yaml_text = content.decode("utf-8", errors="ignore")
            template_structure = yaml.safe_load(yaml_text)

            # Validate and normalize structure
            return self._validate_template_structure(template_structure)

        except yaml.YAMLError as e:
            print(f"Error parsing YAML template: {e}")
            return self._get_fallback_template()
        except Exception as e:
            print(f"Error processing YAML template: {e}")
            return self._get_fallback_template()

    def _extract_text_structure(self, content: bytes) -> str:
        """Extract structure from plain text/markdown files"""
        try:
            text = content.decode("utf-8", errors="ignore")
            lines = text.split("\n")
            structured_lines = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Detect markdown-style headings
                if line.startswith("#"):
                    structured_lines.append(line)
                # Detect numbered sections (e.g., "1. Section Title")
                elif re.match(r"^\d+[\.\)]\s+[A-Z]", line):
                    structured_lines.append(f"## {line}")
                # Detect all-caps short lines (potential headings)
                elif len(line.split()) < 10 and line.isupper() and len(line) > 3:
                    structured_lines.append(f"## {line}")
                else:
                    structured_lines.append(line)

            return "\n".join(structured_lines)

        except Exception as e:
            print(f"Error extracting text structure: {e}")
            return content.decode("utf-8", errors="ignore")

    async def _extract_template_structure(self, structured_text: str) -> Dict[str, Any]:
        """Use LLM to extract memo template structure from structured text"""

        prompt = ChatPromptTemplate.from_template(
            """
You are analyzing a venture capital investment memo template to extract its structure.

Below is the content of an example memo with its structure preserved:

{structured_text}

Your task is to identify all the main sections of this memo and extract:
1. Section titles (exact headings used)
2. Section descriptions (what type of content belongs in each section)
3. Section order
4. Any patterns or formatting preferences

Return a JSON object with this structure:
{{
    "template_name": "Name of the template (e.g., 'Standard VC Investment Memo')",
    "sections": [
        {{
            "title": "Exact section title as it appears",
            "key": "snake_case_key_for_section",
            "required": true,
            "min_paragraphs": 1,
            "max_paragraphs": 3,
            "description": "Description of what should be in this section based on the example"
        }}
    ]
}}

Guidelines:
- Map common section types to standard keys:
  * Executive Summary / Summary / Overview → "exec_summary"
  * Company Overview / Company / Business → "company_overview"
  * Market / Market Opportunity / Market Analysis → "market_opportunity"
  * Progress / Metrics / Traction → "progress_metrics"
  * Financial / Funding / Cap Table → "financial_overview"
  * Team / Management / Founders → "team"
  * Thesis / Risks / Investment Thesis → "thesis_risks"
  * Recommendation / Decision / Conclusion → "recommendation"
- For custom sections, create descriptive snake_case keys
- Estimate paragraph counts based on example content length
- Include all major sections, even if they're custom

Return ONLY valid JSON, no additional text.
"""
        )

        try:
            # Use rate limiter for template parsing
            from rate_limiter import RateLimiter

            rate_limiter = RateLimiter(max_retries=5, initial_delay=1.0, max_delay=60.0)

            response = await rate_limiter.execute(
                self.llm.ainvoke,
                prompt.format_messages(structured_text=structured_text[:8000]),
            )

            # Extract JSON from response
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                # Extract JSON from code block
                lines = content.split("\n")
                json_lines = [
                    line for line in lines if not line.strip().startswith("```")
                ]
                content = "\n".join(json_lines)

            # Parse JSON
            template_structure = json.loads(content)

            # Validate and normalize structure
            return self._validate_template_structure(template_structure)

        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            print(f"Response content: {content[:500]}")
            # Fallback to default template if parsing fails
            return self._get_fallback_template()

        except Exception as e:
            print(f"Error extracting template structure: {e}")
            return self._get_fallback_template()

    def _validate_template_structure(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize template structure"""
        if "template_name" not in template:
            template["template_name"] = "Custom VC Investment Memo"

        if "sections" not in template or not isinstance(template["sections"], list):
            return self._get_fallback_template()

        # Validate each section
        validated_sections = []
        for section in template["sections"]:
            if not isinstance(section, dict):
                continue

            validated_section = {
                "title": section.get("title", "Untitled Section"),
                "key": section.get("key", self._generate_key(section.get("title", ""))),
                "required": section.get("required", True),
                "min_paragraphs": max(1, int(section.get("min_paragraphs", 1))),
                "max_paragraphs": max(
                    int(section.get("min_paragraphs", 1)),
                    int(section.get("max_paragraphs", 3)),
                ),
                "description": section.get(
                    "description", "Section content to be generated"
                ),
            }
            validated_sections.append(validated_section)

        if not validated_sections:
            return self._get_fallback_template()

        return {
            "template_name": template["template_name"],
            "sections": validated_sections,
        }

    def _generate_key(self, title: str) -> str:
        """Generate snake_case key from section title"""
        # Convert to lowercase and replace spaces/special chars with underscores
        key = re.sub(r"[^a-z0-9]+", "_", title.lower())
        key = re.sub(r"_+", "_", key)  # Remove multiple underscores
        return key.strip("_")

    def _get_fallback_template(self) -> Dict[str, Any]:
        """Return default template if extraction fails"""
        from models import DEFAULT_TEMPLATE

        return DEFAULT_TEMPLATE
