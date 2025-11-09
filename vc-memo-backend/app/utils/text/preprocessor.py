import re
import tiktoken
from typing import List, Dict, Tuple, Optional
import hashlib


class TextPreprocessor:
    """Preprocess and clean text from various document types"""

    def __init__(self):
        # Initialize tokenizer for accurate token counting
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")

        # Common patterns to clean
        self.footer_patterns = [
            r"page\s*\d+\s*of\s*\d+",
            r"confidential.*?proprietary",
            r"\d{1,2}/\d{1,2}/\d{2,4}.*?page\s*\d+",
            r"©.*?\d{4}.*?rights reserved",
            r"prepared\s+by.*?for.*?only",
        ]

        self.header_patterns = [
            r"^.*?investor\s+deck.*?$",
            r"^.*?confidential.*?$",
            r"^.*?proprietary.*?$",
        ]

        # Watermark and signature patterns
        self.watermark_patterns = [
            r"draft|watermark|confidential|proprietary",
            r"do\s+not\s+distribute",
            r"for\s+discussion\s+purposes\s+only",
        ]

    def preprocess_text(self, text: str, source_type: str) -> str:
        """Clean and preprocess text based on source type"""

        # Basic cleaning
        text = self._normalize_whitespace(text)

        # Type-specific cleaning
        if source_type == "pdf":
            text = self._clean_pdf_text(text)
        elif source_type in ["pptx", "ppt"]:
            text = self._clean_presentation_text(text)
        elif source_type in ["docx", "doc"]:
            text = self._clean_document_text(text)
        elif source_type in ["xlsx", "xls", "csv"]:
            text = self._clean_spreadsheet_text(text)

        # Common cleaning
        text = self._remove_boilerplate(text)
        text = self._remove_excessive_whitespace(text)

        return text.strip()

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize various whitespace characters"""
        # Replace various unicode spaces with regular space
        text = re.sub(r"[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000]", " ", text)
        # Replace tabs with spaces
        text = text.replace("\t", " ")
        # Remove zero-width characters
        text = re.sub(r"[\u200B\u200C\u200D\uFEFF]", "", text)
        return text

    def _clean_pdf_text(self, text: str) -> str:
        """PDF-specific cleaning"""
        # Remove common PDF artifacts
        text = re.sub(r"\x00+", "", text)  # Null bytes
        text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)  # Rejoin hyphenated words

        # Remove headers/footers (case-insensitive)
        for pattern in self.footer_patterns + self.header_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)

        return text

    def _clean_presentation_text(self, text: str) -> str:
        """PowerPoint-specific cleaning"""
        # Remove slide numbers
        text = re.sub(r"slide\s*\d+", "", text, flags=re.IGNORECASE)
        # Remove common presentation artifacts
        text = re.sub(r"click to add.*?text", "", text, flags=re.IGNORECASE)
        text = re.sub(r"insert.*?here", "", text, flags=re.IGNORECASE)
        return text

    def _clean_document_text(self, text: str) -> str:
        """Word document-specific cleaning"""
        # Remove track changes artifacts
        text = re.sub(r"\[.*?deleted.*?\]", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\[.*?inserted.*?\]", "", text, flags=re.IGNORECASE)
        # Remove comments markers
        text = re.sub(r"\[comment.*?\]", "", text, flags=re.IGNORECASE)
        return text

    def _clean_spreadsheet_text(self, text: str) -> str:
        """Spreadsheet-specific cleaning"""
        # Remove excessive cell separators
        text = re.sub(r"\|{2,}", "|", text)
        # Clean up table formatting
        text = re.sub(r"-{10,}", "-" * 10, text)  # Limit separator lines
        # Remove 'nan' and 'NaN' values
        text = re.sub(r"\b(nan|NaN)\b", "", text)
        return text

    def _remove_boilerplate(self, text: str) -> str:
        """Remove common boilerplate text"""
        # Remove watermarks (case-insensitive)
        for pattern in self.watermark_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Remove email signatures
        text = re.sub(
            r"best regards.*?$",
            "",
            text,
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
        text = re.sub(
            r"sincerely.*?$", "", text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
        )

        # Remove repeated disclaimers
        lines = text.split("\n")
        unique_lines = []
        seen = set()

        for line in lines:
            line_lower = line.lower().strip()
            # Skip if it's a disclaimer we've seen before
            if "confidential" in line_lower or "proprietary" in line_lower:
                if line_lower in seen:
                    continue
                seen.add(line_lower)
            unique_lines.append(line)

        return "\n".join(unique_lines)

    def _remove_excessive_whitespace(self, text: str) -> str:
        """Remove excessive whitespace while preserving structure"""
        # Replace multiple spaces with single space
        text = re.sub(r" {2,}", " ", text)
        # Replace multiple newlines with double newline
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Remove trailing spaces
        text = re.sub(r" +$", "", text, flags=re.MULTILINE)
        return text

    def compress_text(self, text: str) -> str:
        """Compress text to reduce token count while preserving meaning"""
        # Remove filler words and phrases
        filler_patterns = [
            r"\b(basically|actually|really|very|quite|just|simply)\b",
            r"\b(in order to|in terms of|with regard to)\b",
            r"\b(it is important to note that|it should be noted that)\b",
        ]

        for pattern in filler_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Compress common phrases
        replacements = {
            "annual recurring revenue": "ARR",
            "monthly recurring revenue": "MRR",
            "customer acquisition cost": "CAC",
            "lifetime value": "LTV",
            "month over month": "MoM",
            "year over year": "YoY",
            "total addressable market": "TAM",
            "serviceable addressable market": "SAM",
            "serviceable obtainable market": "SOM",
        }

        for long_form, short_form in replacements.items():
            text = re.sub(long_form, short_form, text, flags=re.IGNORECASE)

        return self._remove_excessive_whitespace(text)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))

    def calculate_text_density(self, text: str) -> float:
        """Calculate information density of text (useful content vs total tokens)"""
        # Count meaningful words (not stopwords or filler)
        words = text.lower().split()
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "been",
        }

        meaningful_words = [w for w in words if w not in stopwords and len(w) > 2]

        if len(words) == 0:
            return 0.0

        return len(meaningful_words) / len(words)

    def hash_text(self, text: str) -> str:
        """Generate SHA256 hash of text for caching"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
