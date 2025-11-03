import PyPDF2
from docx import Document as DocxDocument
from pptx import Presentation
import pandas as pd
import io
from typing import List, Dict, Any
from smart_chunker import SmartChunker, DocumentChunk
from text_preprocessor import TextPreprocessor
import asyncio


class OptimizedDocumentParser:
    """Optimized document parser with smart chunking and preprocessing"""
    
    def __init__(self):
        self.supported_types = [
            "pdf", "docx", "doc", "pptx", "ppt", "txt", "md", "xlsx", "xls", "csv"
        ]
        self.chunker = SmartChunker(min_tokens=800, max_tokens=2000, target_tokens=1200)
        self.preprocessor = TextPreprocessor()
        
    async def parse_documents(self, documents: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """Parse all uploaded documents into optimized chunks"""
        all_chunks = []
        
        # Process documents in parallel where possible
        tasks = []
        for doc in documents:
            task = self._parse_single_document(doc)
            tasks.append(task)
            
        chunks_lists = await asyncio.gather(*tasks)
        
        # Flatten the list of lists
        for chunks in chunks_lists:
            all_chunks.extend(chunks)
            
        print(f"Parsed {len(documents)} documents into {len(all_chunks)} chunks")
        
        # Print chunk statistics
        if all_chunks:
            avg_tokens = sum(c.token_count for c in all_chunks) / len(all_chunks)
            print(f"Average chunk size: {avg_tokens:.0f} tokens")
            
        return all_chunks
    
    async def _parse_single_document(self, doc: Dict[str, Any]) -> List[DocumentChunk]:
        """Parse a single document"""
        filename = doc["filename"]
        content = doc["content"]
        file_type = filename.split(".")[-1].lower()
        
        print(f"Parsing {filename} ({file_type})...")
        
        try:
            # Extract raw text based on file type
            if file_type == "pdf":
                raw_text = await self._extract_pdf_text(content, filename)
            elif file_type in ["docx", "doc"]:
                raw_text = await self._extract_docx_text(content, filename)
            elif file_type in ["pptx", "ppt"]:
                raw_text = await self._extract_pptx_text(content, filename)
            elif file_type in ["txt", "md"]:
                raw_text = await self._extract_plain_text(content, filename)
            elif file_type in ["xlsx", "xls"]:
                raw_text = await self._extract_excel_text(content, filename)
            elif file_type == "csv":
                raw_text = await self._extract_csv_text(content, filename)
            else:
                print(f"Unsupported file type: {file_type}")
                return []
            
            # Apply smart chunking
            chunks = self.chunker.chunk_document(
                raw_text,
                filename,
                file_type,
                additional_metadata={
                    'original_size': len(content),
                    'file_type': file_type
                }
            )
            
            print(f"  ✓ Generated {len(chunks)} chunks from {filename}")
            return chunks
            
        except Exception as e:
            print(f"  ✗ Error parsing {filename}: {e}")
            return []
    
    async def _extract_pdf_text(self, content: bytes, filename: str) -> str:
        """Extract text from PDF with better handling"""
        text_parts = []
        
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        # Add page marker for chunking
                        text_parts.append(f"\nPage {page_num + 1}:\n{page_text}")
                except Exception as e:
                    print(f"Error extracting page {page_num + 1} from {filename}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error reading PDF {filename}: {e}")
            return ""
            
        return "\n".join(text_parts)
    
    async def _extract_docx_text(self, content: bytes, filename: str) -> str:
        """Extract text from DOCX with structure preservation"""
        text_parts = []
        
        try:
            doc = DocxDocument(io.BytesIO(content))
            
            for para in doc.paragraphs:
                if para.text.strip():
                    # Check if it's a heading
                    if para.style and para.style.name.startswith('Heading'):
                        text_parts.append(f"\n## {para.text}\n")
                    else:
                        text_parts.append(para.text)
                        
            # Also extract text from tables
            for table in doc.tables:
                table_text = self._extract_table_text(table)
                if table_text:
                    text_parts.append(f"\n{table_text}\n")
                    
        except Exception as e:
            print(f"Error parsing DOCX {filename}: {e}")
            return ""
            
        return "\n\n".join(text_parts)
    
    async def _extract_pptx_text(self, content: bytes, filename: str) -> str:
        """Extract text from PPTX with slide structure"""
        text_parts = []
        
        try:
            prs = Presentation(io.BytesIO(content))
            
            for slide_num, slide in enumerate(prs.slides):
                slide_texts = [f"\nSlide {slide_num + 1}:"]
                
                # Extract text from shapes
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_texts.append(shape.text.strip())
                        
                    # Extract text from tables
                    if hasattr(shape, "table"):
                        table_text = self._extract_pptx_table_text(shape.table)
                        if table_text:
                            slide_texts.append(table_text)
                            
                # Extract notes
                if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                    notes = slide.notes_slide.notes_text_frame.text.strip()
                    if notes:
                        slide_texts.append(f"[Notes: {notes}]")
                        
                if len(slide_texts) > 1:  # More than just the slide number
                    text_parts.append("\n".join(slide_texts))
                    
        except Exception as e:
            print(f"Error parsing PPTX {filename}: {e}")
            return ""
            
        return "\n\n".join(text_parts)
    
    async def _extract_plain_text(self, content: bytes, filename: str) -> str:
        """Extract plain text with encoding detection"""
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
                
        # Fallback with error handling
        return content.decode('utf-8', errors='ignore')
    
    async def _extract_excel_text(self, content: bytes, filename: str) -> str:
        """Extract data from Excel with better formatting"""
        text_parts = []
        
        try:
            excel_file = io.BytesIO(content)
            excel_data = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
            
            for sheet_name, df in excel_data.items():
                if df.empty:
                    continue
                    
                text_parts.append(f"\nSheet: {sheet_name}")
                text_parts.append("=" * 50)
                
                # Include column descriptions if available
                if not df.columns.empty:
                    text_parts.append(f"Columns: {', '.join(map(str, df.columns))}")
                    
                # Add shape info
                text_parts.append(f"Data shape: {df.shape[0]} rows × {df.shape[1]} columns")
                
                # For large dataframes, include sample and statistics
                if df.shape[0] > 20:
                    # First few rows
                    text_parts.append("\nFirst 10 rows:")
                    text_parts.append(df.head(10).to_string())
                    
                    # Summary statistics for numeric columns
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        text_parts.append("\nSummary Statistics:")
                        text_parts.append(df[numeric_cols].describe().to_string())
                        
                    # Key insights
                    text_parts.append(f"\nTotal rows: {df.shape[0]}")
                else:
                    # Include all data for small sheets
                    text_parts.append(df.to_string())
                    
        except Exception as e:
            print(f"Error parsing Excel {filename}: {e}")
            return f"[Excel file: {filename} - parsing error]"
            
        return "\n\n".join(text_parts)
    
    async def _extract_csv_text(self, content: bytes, filename: str) -> str:
        """Extract CSV data with encoding detection"""
        text_parts = []
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                csv_file = io.BytesIO(content)
                df = pd.read_csv(csv_file, encoding=encoding)
                break
            except (UnicodeDecodeError, pd.errors.EmptyDataError):
                continue
                
        if df is None or df.empty:
            return f"[CSV file: {filename} - could not parse]"
            
        text_parts.append(f"CSV File: {filename}")
        text_parts.append("=" * 50)
        
        # Include column info
        text_parts.append(f"Columns: {', '.join(df.columns)}")
        text_parts.append(f"Data shape: {df.shape[0]} rows × {df.shape[1]} columns")
        
        # Handle based on size
        if df.shape[0] > 20:
            # Sample for large files
            text_parts.append("\nFirst 10 rows:")
            text_parts.append(df.head(10).to_string())
            
            # Statistics
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                text_parts.append("\nSummary Statistics:")
                text_parts.append(df[numeric_cols].describe().to_string())
        else:
            # Full data for small files
            text_parts.append(df.to_string())
            
        return "\n\n".join(text_parts)
    
    def _extract_table_text(self, table) -> str:
        """Extract text from a Word table"""
        rows = []
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text:
                    row_text.append(cell_text)
            if row_text:
                rows.append(" | ".join(row_text))
        return "\n".join(rows)
    
    def _extract_pptx_table_text(self, table) -> str:
        """Extract text from a PowerPoint table"""
        rows = []
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                if cell.text.strip():
                    row_text.append(cell.text.strip())
            if row_text:
                rows.append(" | ".join(row_text))
        return "\n".join(rows)
