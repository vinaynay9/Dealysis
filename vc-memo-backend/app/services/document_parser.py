"""
Centralized document parser using LangChain document loaders.
Replaces both document_parser.py and optimized_document_parser.py
"""

import io
import tempfile
import os
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    CSVLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter
import pandas as pd
import asyncio
import tiktoken
from docx import Document as DocxDocument


class LangChainDocumentParser:
    """
    Centralized document parser using LangChain loaders and text splitters.
    Handles PDF, DOCX, PPTX, XLSX, CSV, TXT, and MD files.
    """

    def __init__(
        self,
        chunk_size: int = 3000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 800,
        max_chunk_size: int = 2000,
    ):
        """
        Initialize parser with two-stage text splitter configuration.
        Stage 1: RecursiveCharacterTextSplitter to preserve document structure
        Stage 2: TokenTextSplitter to ensure token budget compliance

        Args:
            chunk_size: Target chunk size in characters (Stage 1)
            chunk_overlap: Overlap between chunks
            min_chunk_size: Minimum chunk size
            max_chunk_size: Maximum chunk size
        """
        self.supported_types = [
            "pdf",
            "docx",
            "doc",
            "pptx",
            "ppt",
            "txt",
            "md",
            "xlsx",
            "xls",
            "csv",
        ]

        # Stage 1: Structure-aware character splitter
        # Splits by logical boundaries (paragraphs, sentences) to preserve meaning
        self.char_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,  # Larger initial chunks
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
        )

        # Stage 2: Token-aware splitter
        # Ensures chunks fit within model token limits
        self.token_splitter = TokenTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",  # GPT-4 tokenizer
            chunk_size=800,  # Target tokens per chunk
            chunk_overlap=120,  # Token overlap for context preservation
        )

        # Initialize tokenizer for observability
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        print("📄 Document Parser initialized with two-stage chunking:")
        print(
            f"   Stage 1: RecursiveCharacterTextSplitter (2000 chars, preserves structure)"
        )
        print(f"   Stage 2: TokenTextSplitter (800 tokens, ensures token budget)")

    async def parse_documents(self, documents: List[Dict[str, Any]]) -> List[Document]:
        """
        Parse all uploaded documents into LangChain Document objects.

        Args:
            documents: List of document dictionaries with 'filename' and 'content' keys

        Returns:
            List of LangChain Document objects with metadata
        """
        all_docs = []

        # Process documents in parallel
        tasks = [self._parse_single_document(doc) for doc in documents]
        docs_lists = await asyncio.gather(*tasks)

        # Flatten the list of lists
        for docs in docs_lists:
            all_docs.extend(docs)

        print(f"\n📄 Parsed {len(documents)} documents into {len(all_docs)} chunks")

        # Print comprehensive statistics
        if all_docs:
            total_chars = sum(len(doc.page_content) for doc in all_docs)
            total_tokens = sum(doc.metadata.get("token_count", 0) for doc in all_docs)
            avg_chars = total_chars / len(all_docs)
            avg_tokens = total_tokens / len(all_docs)

            print(f"\n📊 Parsing Summary:")
            print(f"   Documents processed: {len(documents)}")
            print(f"   Total chunks:        {len(all_docs)}")
            print(
                f"   Avg chunk size:      {avg_chars:.0f} chars / {avg_tokens:.0f} tokens"
            )
            print(f"   Total tokens:        {total_tokens:,}")

            # File type breakdown
            file_types = {}
            for doc in all_docs:
                ftype = doc.metadata.get("file_type", "unknown")
                file_types[ftype] = file_types.get(ftype, 0) + 1
            print(
                f"   Chunk distribution:  {', '.join(f'{k}: {v}' for k, v in file_types.items())}"
            )

        return all_docs

    async def _parse_single_document(self, doc: Dict[str, Any]) -> List[Document]:
        """Parse a single document using appropriate LangChain loader."""
        filename = doc["filename"]
        content = doc["content"]
        file_type = filename.split(".")[-1].lower()
        file_size_kb = len(content) / 1024

        print(f"\n📄 Parsing {filename} ({file_type}, {file_size_kb:.1f} KB)...")

        try:
            # Create temporary file for LangChain loaders that require file paths
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{file_type}"
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            try:
                # Load documents based on file type
                if file_type == "pdf":
                    documents = await self._load_pdf(tmp_path, filename)
                elif file_type in ["docx", "doc"]:
                    documents = await self._load_docx(tmp_path, filename)
                elif file_type in ["pptx", "ppt"]:
                    documents = await self._load_pptx(tmp_path, filename)
                elif file_type in ["txt", "md"]:
                    documents = await self._load_text(tmp_path, filename)
                elif file_type in ["xlsx", "xls"]:
                    documents = await self._load_excel(content, filename)
                elif file_type == "csv":
                    documents = await self._load_csv(tmp_path, filename)
                else:
                    print(f"  ⚠ Unsupported file type: {file_type}")
                    return []

                # Split documents into chunks using two-stage approach
                if documents:
                    # Stage 1: Character-based splitting (preserves structure)
                    stage1_chunks = self.char_splitter.split_documents(documents)
                    stage1_char_count = sum(len(d.page_content) for d in stage1_chunks)
                    avg_stage1_chars = (
                        stage1_char_count / len(stage1_chunks) if stage1_chunks else 0
                    )

                    print(
                        f"  📊 Stage 1 (Structure): {len(stage1_chunks)} chunks (avg {avg_stage1_chars:.0f} chars)"
                    )

                    # Stage 2: Token-based splitting (ensures token limits)
                    chunked_docs = self.token_splitter.split_documents(stage1_chunks)

                    # Calculate token statistics
                    total_tokens = 0
                    for doc in chunked_docs:
                        tokens = len(self.tokenizer.encode(doc.page_content))
                        doc.metadata["token_count"] = tokens
                        total_tokens += tokens

                    avg_tokens = total_tokens / len(chunked_docs) if chunked_docs else 0
                    reduction_pct = (
                        (
                            (len(stage1_chunks) - len(chunked_docs))
                            / len(stage1_chunks)
                            * 100
                        )
                        if stage1_chunks
                        else 0
                    )

                    print(
                        f"  📊 Stage 2 (Tokens):    {len(chunked_docs)} chunks (avg {avg_tokens:.0f} tokens)"
                    )
                    if reduction_pct != 0:
                        print(
                            f"  📉 Chunk optimization:  {abs(reduction_pct):.1f}% {'reduction' if reduction_pct > 0 else 'increase'}"
                        )
                    print(f"  💾 Total tokens:        {total_tokens:,} tokens")

                    # Add chunk metadata
                    for idx, chunk_doc in enumerate(chunked_docs):
                        chunk_doc.metadata["chunk_index"] = idx
                        chunk_doc.metadata["total_chunks"] = len(chunked_docs)
                        chunk_doc.metadata["file_size_chars"] = len(
                            chunk_doc.page_content
                        )

                    # Print sample chunks for verification
                    print(f"  ✓ Generated {len(chunked_docs)} chunks from {filename}")
                    if len(chunked_docs) > 0:
                        print("  📝 Sample chunks:")
                        sample_count = min(2, len(chunked_docs))
                        for idx in range(sample_count):
                            chunk_doc = chunked_docs[idx]
                            tokens = chunk_doc.metadata.get("token_count", 0)
                            preview = chunk_doc.page_content[:100].replace("\n", " ")
                            print(
                                f"     Chunk {idx+1}: {tokens} tokens | '{preview}...'"
                            )

                    return chunked_docs
                else:
                    print(f"  ⚠ No content extracted from {filename}")
                    return []

            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            print(f"  ✗ Error parsing {filename}: {e}")
            return []

    async def _load_pdf(self, file_path: str, filename: str) -> List[Document]:
        """Load PDF using PyPDFLoader."""
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()

            # Add source filename to metadata
            for doc in documents:
                doc.metadata["source_file"] = filename
                doc.metadata["file_type"] = "pdf"

            return documents
        except Exception as e:
            print(f"  ✗ Error loading PDF: {e}")
            return []

    async def _load_docx(self, file_path: str, filename: str) -> List[Document]:
        """Load DOCX using python-docx and chunk by ~500 words."""
        try:
            # Read file content
            with open(file_path, "rb") as f:
                content = f.read()

            # Parse DOCX
            doc = DocxDocument(io.BytesIO(content))
            chunks = []
            current_section = []

            # Extract paragraphs and chunk every ~500 words
            for para in doc.paragraphs:
                if para.text.strip():
                    current_section.append(para.text)
                    # Split into chunks every ~500 words
                    section_text = " ".join(current_section)
                    if len(section_text.split()) > 500:
                        chunks.append(section_text)
                        current_section = []

            # Add remaining text
            if current_section:
                chunks.append(" ".join(current_section))

            # Convert chunks to LangChain Document objects
            documents = []
            for idx, chunk_text in enumerate(chunks):
                doc = Document(
                    page_content=chunk_text,
                    metadata={
                        "source_file": filename,
                        "file_type": "docx",
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                    },
                )
                documents.append(doc)

            return documents
        except Exception as e:
            print(f"  ✗ Error loading DOCX {filename}: {e}")
            return []

    async def _load_pptx(self, file_path: str, filename: str) -> List[Document]:
        """
        Load PPTX using UnstructuredPowerPointLoader with elements mode.
        This extracts text, tables, and visual descriptions from slides.
        """
        try:
            # Use elements mode to preserve slide structure and extract visuals
            loader = UnstructuredPowerPointLoader(file_path, mode="single")
            documents = loader.load()

            # Add source filename and enhance metadata
            for doc in documents:
                doc.metadata["source_file"] = filename
                doc.metadata["file_type"] = "pptx"

                # Preserve element type information (title, text, image, table, etc.)
                # UnstructuredPowerPointLoader provides this in metadata
                element_type = doc.metadata.get("category", "unknown")
                doc.metadata["element_type"] = element_type

                # Add visual context to content if it's an image or chart
                if element_type in ["Image", "Picture", "Chart"]:
                    page_num = doc.metadata.get("page_number", "unknown")
                    doc.page_content = (
                        f"[Slide {page_num} - {element_type}]: {doc.page_content}"
                    )

            return documents
        except Exception as e:
            print(f"  ✗ Error loading PPTX: {e}")
            return []

    async def _load_text(self, file_path: str, filename: str) -> List[Document]:
        """Load plain text or markdown files using TextLoader."""
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            documents = loader.load()

            # Add source filename to metadata
            for doc in documents:
                doc.metadata["source_file"] = filename
                doc.metadata["file_type"] = "txt" if filename.endswith(".txt") else "md"

            return documents
        except Exception as e:
            print(f"  ✗ Error loading text file: {e}")
            return []

    async def _load_excel(self, content: bytes, filename: str) -> List[Document]:
        """
        Load Excel files using pandas.
        Creates structured text representation of sheets.
        """
        try:
            excel_file = io.BytesIO(content)
            excel_data = pd.read_excel(excel_file, sheet_name=None, engine="openpyxl")

            documents = []

            for sheet_name, df in excel_data.items():
                if df.empty:
                    continue

                # Create structured text representation
                text_parts = [
                    f"Excel Sheet: {sheet_name}",
                    "=" * 50,
                    f"Columns: {', '.join(map(str, df.columns))}",
                    f"Data shape: {df.shape[0]} rows × {df.shape[1]} columns",
                ]

                # Add data based on size
                if df.shape[0] > 20:
                    text_parts.append("\nFirst 10 rows:")
                    text_parts.append(df.head(10).to_string())

                    # Add summary statistics
                    numeric_cols = df.select_dtypes(include=["number"]).columns
                    if len(numeric_cols) > 0:
                        text_parts.append("\nSummary Statistics:")
                        text_parts.append(df[numeric_cols].describe().to_string())
                else:
                    text_parts.append("\nData:")
                    text_parts.append(df.to_string())

                doc_content = "\n\n".join(text_parts)

                # Create Document object
                doc = Document(
                    page_content=doc_content,
                    metadata={
                        "source_file": filename,
                        "file_type": "xlsx",
                        "sheet_name": sheet_name,
                        "rows": df.shape[0],
                        "columns": df.shape[1],
                    },
                )
                documents.append(doc)

            return documents

        except Exception as e:
            print(f"  ✗ Error loading Excel file: {e}")
            return []

    async def _load_csv(self, file_path: str, filename: str) -> List[Document]:
        """Load CSV using LangChain CSVLoader."""
        try:
            loader = CSVLoader(file_path=file_path)
            documents = loader.load()

            # Add source filename to metadata
            for doc in documents:
                doc.metadata["source_file"] = filename
                doc.metadata["file_type"] = "csv"

            return documents

        except Exception as e:
            print(f"  ✗ Error loading CSV file: {e}")
            return []
            print(f"  ✗ Error loading CSV file: {e}")
            return []
