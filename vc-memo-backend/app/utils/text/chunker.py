import re
import tiktoken
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from app.utils.text_preprocessor import TextPreprocessor


@dataclass
class DocumentChunk:
    """Represents a chunk of document with metadata"""

    content: str
    metadata: Dict[str, any]
    token_count: int
    chunk_id: str
    source_file: str
    chunk_index: int

    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "metadata": self.metadata,
            "token_count": self.token_count,
            "chunk_id": self.chunk_id,
            "source_file": self.source_file,
            "chunk_index": self.chunk_index,
        }


class SmartChunker:
    """Intelligent document chunking with semantic awareness"""

    def __init__(
        self, min_tokens: int = 800, max_tokens: int = 2000, target_tokens: int = 1200
    ):
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.target_tokens = target_tokens
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.preprocessor = TextPreprocessor()

        # Section headers patterns
        self.section_patterns = [
            r"^#+\s+(.+)$",  # Markdown headers
            r"^([A-Z][A-Z\s]+):?\s*$",  # ALL CAPS headers
            r"^(\d+\.?\s+[A-Z].+)$",  # Numbered sections
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):?\s*$",  # Title Case headers
        ]

    def chunk_document(
        self,
        text: str,
        filename: str,
        file_type: str,
        additional_metadata: Optional[Dict] = None,
    ) -> List[DocumentChunk]:
        """Create smart chunks from document text"""

        # Preprocess text
        cleaned_text = self.preprocessor.preprocess_text(text, file_type)

        # Split by file type
        if file_type in ["pptx", "ppt"]:
            chunks = self._chunk_presentation(
                cleaned_text, filename, additional_metadata
            )
        elif file_type == "pdf":
            chunks = self._chunk_pdf(cleaned_text, filename, additional_metadata)
        elif file_type in ["docx", "doc", "txt", "md"]:
            chunks = self._chunk_document(cleaned_text, filename, additional_metadata)
        elif file_type in ["xlsx", "xls", "csv"]:
            chunks = self._chunk_spreadsheet(
                cleaned_text, filename, additional_metadata
            )
        else:
            chunks = self._chunk_generic(cleaned_text, filename, additional_metadata)

        # Filter out low-quality chunks
        filtered_chunks = self._filter_chunks(chunks)

        # Assign chunk IDs
        for i, chunk in enumerate(filtered_chunks):
            chunk.chunk_index = i
            chunk.chunk_id = (
                f"{filename}_{i}_{self.preprocessor.hash_text(chunk.content)[:8]}"
            )

        return filtered_chunks

    def _chunk_presentation(
        self, text: str, filename: str, metadata: Optional[Dict] = None
    ) -> List[DocumentChunk]:
        """Chunk presentation by slides"""
        chunks = []

        # Split by slide markers
        slide_pattern = r"Slide\s*\d+:?"
        slides = re.split(slide_pattern, text, flags=re.IGNORECASE)

        current_chunk = []
        current_tokens = 0

        for i, slide_content in enumerate(slides):
            if not slide_content.strip():
                continue

            slide_text = slide_content.strip()
            slide_tokens = self._count_tokens(slide_text)

            # Create metadata for this slide
            slide_metadata = {
                "slide_number": i,
                "type": "presentation_slide",
                **(metadata or {}),
            }

            # If slide is too large, split it
            if slide_tokens > self.max_tokens:
                slide_chunks = self._split_large_text(slide_text, slide_metadata)
                chunks.extend(
                    [
                        DocumentChunk(
                            content=chunk_text,
                            metadata=chunk_meta,
                            token_count=self._count_tokens(chunk_text),
                            chunk_id="",  # Will be assigned later
                            source_file=filename,
                            chunk_index=0,  # Will be assigned later
                        )
                        for chunk_text, chunk_meta in slide_chunks
                    ]
                )
            # If adding slide would exceed max, create chunk
            elif current_tokens + slide_tokens > self.max_tokens and current_chunk:
                combined_text = "\n\n".join(current_chunk)
                chunks.append(
                    DocumentChunk(
                        content=combined_text,
                        metadata={
                            "slides": list(range(i - len(current_chunk), i)),
                            "type": "presentation_slides",
                            **(metadata or {}),
                        },
                        token_count=current_tokens,
                        chunk_id="",
                        source_file=filename,
                        chunk_index=0,
                    )
                )
                current_chunk = [f"Slide {i}: {slide_text}"]
                current_tokens = slide_tokens
            else:
                current_chunk.append(f"Slide {i}: {slide_text}")
                current_tokens += slide_tokens

        # Add remaining slides
        if current_chunk:
            combined_text = "\n\n".join(current_chunk)
            chunks.append(
                DocumentChunk(
                    content=combined_text,
                    metadata={
                        "slides": list(
                            range(len(slides) - len(current_chunk), len(slides))
                        ),
                        "type": "presentation_slides",
                        **(metadata or {}),
                    },
                    token_count=current_tokens,
                    chunk_id="",
                    source_file=filename,
                    chunk_index=0,
                )
            )

        return chunks

    def _chunk_pdf(
        self, text: str, filename: str, metadata: Optional[Dict] = None
    ) -> List[DocumentChunk]:
        """Chunk PDF by pages and sections"""
        chunks = []

        # Try to split by page markers first
        page_pattern = r"Page\s*\d+:"
        pages = re.split(page_pattern, text, flags=re.IGNORECASE)

        if len(pages) > 1:
            # Process by pages
            for i, page_content in enumerate(pages):
                if not page_content.strip():
                    continue

                page_metadata = {
                    "page_number": i,
                    "type": "pdf_page",
                    **(metadata or {}),
                }

                # Check if page needs further chunking
                page_tokens = self._count_tokens(page_content)
                if page_tokens > self.max_tokens:
                    page_chunks = self._chunk_by_sections(page_content, page_metadata)
                    for chunk_text, chunk_meta in page_chunks:
                        chunks.append(
                            DocumentChunk(
                                content=chunk_text,
                                metadata=chunk_meta,
                                token_count=self._count_tokens(chunk_text),
                                chunk_id="",
                                source_file=filename,
                                chunk_index=0,
                            )
                        )
                else:
                    chunks.append(
                        DocumentChunk(
                            content=page_content,
                            metadata=page_metadata,
                            token_count=page_tokens,
                            chunk_id="",
                            source_file=filename,
                            chunk_index=0,
                        )
                    )
        else:
            # No clear page markers, chunk by sections
            section_chunks = self._chunk_by_sections(text, metadata or {})
            for chunk_text, chunk_meta in section_chunks:
                chunks.append(
                    DocumentChunk(
                        content=chunk_text,
                        metadata=chunk_meta,
                        token_count=self._count_tokens(chunk_text),
                        chunk_id="",
                        source_file=filename,
                        chunk_index=0,
                    )
                )

        return chunks

    def _chunk_document(
        self, text: str, filename: str, metadata: Optional[Dict] = None
    ) -> List[DocumentChunk]:
        """Chunk document by sections and paragraphs"""
        chunks = []

        # Try to identify sections
        section_chunks = self._chunk_by_sections(text, metadata or {})

        for chunk_text, chunk_meta in section_chunks:
            chunks.append(
                DocumentChunk(
                    content=chunk_text,
                    metadata=chunk_meta,
                    token_count=self._count_tokens(chunk_text),
                    chunk_id="",
                    source_file=filename,
                    chunk_index=0,
                )
            )

        return chunks

    def _chunk_spreadsheet(
        self, text: str, filename: str, metadata: Optional[Dict] = None
    ) -> List[DocumentChunk]:
        """Chunk spreadsheet data intelligently"""
        chunks = []

        # Split by sheet markers
        sheet_pattern = r"Sheet:\s*(.+?)\n={10,}"
        sheets = re.split(sheet_pattern, text)

        for i in range(1, len(sheets), 2):
            if i + 1 < len(sheets):
                sheet_name = sheets[i].strip()
                sheet_content = sheets[i + 1].strip()

                if not sheet_content:
                    continue

                sheet_metadata = {
                    "sheet_name": sheet_name,
                    "type": "spreadsheet_data",
                    **(metadata or {}),
                }

                # Check if we need to split the sheet data
                sheet_tokens = self._count_tokens(sheet_content)

                if sheet_tokens > self.max_tokens:
                    # Split by table sections or summary statistics
                    sections = sheet_content.split("\n\nSummary Statistics:")

                    if len(sections) > 1:
                        # Add main data
                        chunks.append(
                            DocumentChunk(
                                content=f"Sheet: {sheet_name}\n\n{sections[0]}",
                                metadata={**sheet_metadata, "section": "data"},
                                token_count=self._count_tokens(sections[0]),
                                chunk_id="",
                                source_file=filename,
                                chunk_index=0,
                            )
                        )

                        # Add summary
                        chunks.append(
                            DocumentChunk(
                                content=f"Sheet: {sheet_name} - Summary Statistics:\n{sections[1]}",
                                metadata={**sheet_metadata, "section": "summary"},
                                token_count=self._count_tokens(sections[1]),
                                chunk_id="",
                                source_file=filename,
                                chunk_index=0,
                            )
                        )
                    else:
                        # Split by rows if needed
                        rows = sheet_content.split("\n")
                        current_chunk = [f"Sheet: {sheet_name}"]
                        current_tokens = 50  # Approximate header tokens

                        for row in rows:
                            row_tokens = self._count_tokens(row)
                            if (
                                current_tokens + row_tokens > self.target_tokens
                                and len(current_chunk) > 1
                            ):
                                chunks.append(
                                    DocumentChunk(
                                        content="\n".join(current_chunk),
                                        metadata=sheet_metadata,
                                        token_count=current_tokens,
                                        chunk_id="",
                                        source_file=filename,
                                        chunk_index=0,
                                    )
                                )
                                current_chunk = [
                                    f"Sheet: {sheet_name} (continued)",
                                    row,
                                ]
                                current_tokens = 50 + row_tokens
                            else:
                                current_chunk.append(row)
                                current_tokens += row_tokens

                        if current_chunk:
                            chunks.append(
                                DocumentChunk(
                                    content="\n".join(current_chunk),
                                    metadata=sheet_metadata,
                                    token_count=current_tokens,
                                    chunk_id="",
                                    source_file=filename,
                                    chunk_index=0,
                                )
                            )
                else:
                    chunks.append(
                        DocumentChunk(
                            content=f"Sheet: {sheet_name}\n\n{sheet_content}",
                            metadata=sheet_metadata,
                            token_count=sheet_tokens,
                            chunk_id="",
                            source_file=filename,
                            chunk_index=0,
                        )
                    )

        return chunks

    def _chunk_generic(
        self, text: str, filename: str, metadata: Optional[Dict] = None
    ) -> List[DocumentChunk]:
        """Generic chunking for unknown file types"""
        return self._chunk_by_sections(text, metadata or {}, filename)

    def _chunk_by_sections(
        self, text: str, metadata: Dict, filename: str = None
    ) -> List[Tuple[str, Dict]]:
        """Chunk text by identifying sections"""
        chunks = []

        # Try to identify sections
        lines = text.split("\n")
        current_section = []
        current_section_title = None
        current_tokens = 0

        for line in lines:
            # Check if this is a section header
            is_header = False
            header_match = None

            for pattern in self.section_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    is_header = True
                    header_match = match.group(1) if match.groups() else line.strip()
                    break

            if is_header and current_section:
                # Save current section if it has content
                section_text = "\n".join(current_section)
                section_metadata = {
                    "section": current_section_title or "Introduction",
                    "type": "document_section",
                    **metadata,
                }

                if current_tokens >= self.min_tokens:
                    chunks.append((section_text, section_metadata))
                    current_section = [line]
                    current_section_title = header_match
                    current_tokens = self._count_tokens(line)
                else:
                    # Section too small, continue accumulating
                    current_section.append(line)
                    current_section_title = header_match
                    current_tokens += self._count_tokens(line)
            else:
                # Regular content line
                line_tokens = self._count_tokens(line)

                if current_tokens + line_tokens > self.max_tokens and current_section:
                    # Save current chunk
                    section_text = "\n".join(current_section)
                    section_metadata = {
                        "section": current_section_title or "Content",
                        "type": "document_section",
                        **metadata,
                    }
                    chunks.append((section_text, section_metadata))

                    # Start new chunk
                    current_section = [line]
                    current_tokens = line_tokens
                else:
                    current_section.append(line)
                    current_tokens += line_tokens

        # Save final section
        if current_section and current_tokens >= 50:  # Minimum 50 tokens
            section_text = "\n".join(current_section)
            section_metadata = {
                "section": current_section_title or "Content",
                "type": "document_section",
                **metadata,
            }
            chunks.append((section_text, section_metadata))

        return chunks

    def _split_large_text(self, text: str, metadata: Dict) -> List[Tuple[str, Dict]]:
        """Split text that exceeds max tokens into smaller chunks"""
        chunks = []

        # Split by paragraphs first
        paragraphs = text.split("\n\n")
        current_chunk = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self._count_tokens(para)

            if para_tokens > self.max_tokens:
                # Paragraph itself is too large, split by sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)

                for sent in sentences:
                    sent_tokens = self._count_tokens(sent)

                    if current_tokens + sent_tokens > self.max_tokens and current_chunk:
                        chunks.append(
                            (
                                "\n\n".join(current_chunk),
                                {**metadata, "split_type": "sentence"},
                            )
                        )
                        current_chunk = [sent]
                        current_tokens = sent_tokens
                    else:
                        current_chunk.append(sent)
                        current_tokens += sent_tokens
            elif current_tokens + para_tokens > self.max_tokens and current_chunk:
                chunks.append(
                    (
                        "\n\n".join(current_chunk),
                        {**metadata, "split_type": "paragraph"},
                    )
                )
                current_chunk = [para]
                current_tokens = para_tokens
            else:
                current_chunk.append(para)
                current_tokens += para_tokens

        if current_chunk:
            chunks.append(
                ("\n\n".join(current_chunk), {**metadata, "split_type": "paragraph"})
            )

        return chunks

    def _filter_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Filter out low-quality chunks"""
        filtered = []

        for chunk in chunks:
            # Skip very small chunks
            if chunk.token_count < 50:
                continue

            # Skip chunks with very low text density
            density = self.preprocessor.calculate_text_density(chunk.content)
            if density < 0.2:  # Less than 20% meaningful content
                continue

            # Skip chunks that are mostly numbers/tables with no context
            if chunk.metadata.get("type") == "spreadsheet_data":
                # Allow spreadsheet data even with low density
                filtered.append(chunk)
            elif self._is_mostly_numbers(chunk.content):
                continue
            else:
                filtered.append(chunk)

        return filtered

    def _is_mostly_numbers(self, text: str) -> bool:
        """Check if text is mostly numbers with little context"""
        # Remove all numbers and see what's left
        text_no_numbers = re.sub(r"[\d\.,]+", "", text)
        # Remove whitespace and common symbols
        text_no_numbers = re.sub(r"[\s\-\|\/\\\(\)\[\]{}:;%$]", "", text_no_numbers)

        # If very little text remains, it's mostly numbers
        return len(text_no_numbers) < len(text) * 0.2

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
