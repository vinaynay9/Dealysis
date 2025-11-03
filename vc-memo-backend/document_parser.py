import PyPDF2
from docx import Document as DocxDocument
from pptx import Presentation
import pandas as pd
import io
from typing import List, Dict, Any


class DocumentParser:
    """Parse multiple document formats into text chunks"""

    def __init__(self):
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

    async def parse_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Parse all uploaded documents into text chunks"""
        all_chunks = []

        for doc in documents:
            filename = doc["filename"]
            content = doc["content"]
            file_type = filename.split(".")[-1].lower()

            if file_type == "pdf":
                chunks = self._parse_pdf(content, filename)
            elif file_type in ["docx", "doc"]:
                chunks = self._parse_docx(content, filename)
            elif file_type in ["pptx", "ppt"]:
                chunks = self._parse_pptx(content, filename)
            elif file_type in ["txt", "md"]:
                chunks = self._parse_text(content, filename)
            elif file_type in ["xlsx", "xls"]:
                chunks = self._parse_excel(content, filename)
            elif file_type == "csv":
                chunks = self._parse_csv(content, filename)
            else:
                print(f"Unsupported file type: {file_type}")
                continue

            # Add source metadata
            for chunk in chunks:
                chunk_with_source = f"[SOURCE: {filename}]\n{chunk}\n[END SOURCE]\n"
                all_chunks.append(chunk_with_source)

        return all_chunks

    def _parse_pdf(self, content: bytes, filename: str) -> List[str]:
        """Extract text from PDF"""
        chunks = []
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    # Split long pages into chunks
                    page_chunks = self._split_text(text, max_tokens=1000)
                    for i, chunk in enumerate(page_chunks):
                        chunks.append(f"Page {page_num + 1}: {chunk}")

        except Exception as e:
            print(f"Error parsing PDF {filename}: {e}")

        return chunks

    def _parse_docx(self, content: bytes, filename: str) -> List[str]:
        """Extract text from DOCX"""
        chunks = []
        try:
            doc = DocxDocument(io.BytesIO(content))

            current_section = []
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

        except Exception as e:
            print(f"Error parsing DOCX {filename}: {e}")

        return chunks

    def _parse_pptx(self, content: bytes, filename: str) -> List[str]:
        """Extract text from PPTX"""
        chunks = []
        try:
            prs = Presentation(io.BytesIO(content))

            for slide_num, slide in enumerate(prs.slides):
                slide_texts = []

                # Extract text from shapes (including text boxes)
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_texts.append(shape.text.strip())

                # Extract text from tables
                for shape in slide.shapes:
                    if hasattr(shape, "table"):
                        table_texts = []
                        for row in shape.table.rows:
                            row_texts = []
                            for cell in row.cells:
                                if cell.text.strip():
                                    row_texts.append(cell.text.strip())
                            if row_texts:
                                table_texts.append(" | ".join(row_texts))
                        if table_texts:
                            slide_texts.append("\n".join(table_texts))

                # Combine all text from the slide
                if slide_texts:
                    slide_content = f"Slide {slide_num + 1}:\n" + "\n".join(slide_texts)
                    # Split long slides into chunks
                    slide_chunks = self._split_text(slide_content, max_tokens=1000)
                    chunks.extend(slide_chunks)

        except Exception as e:
            print(f"Error parsing PPTX {filename}: {e}")

        return chunks

    def _parse_text(self, content: bytes, filename: str) -> List[str]:
        """Parse plain text file"""
        try:
            text = content.decode("utf-8", errors="ignore")
            return self._split_text(text, max_tokens=1000)
        except Exception as e:
            print(f"Error parsing text file {filename}: {e}")
            return []

    def _parse_excel(self, content: bytes, filename: str) -> List[str]:
        """Extract data from Excel files and format as text"""
        chunks = []
        try:
            excel_file = io.BytesIO(content)

            # Read all sheets
            excel_data = pd.read_excel(excel_file, sheet_name=None, engine="openpyxl")

            for sheet_name, df in excel_data.items():
                if df.empty:
                    continue

                # Create a structured text representation
                sheet_header = f"Sheet: {sheet_name}\n"
                sheet_header += "=" * 50 + "\n\n"

                # Convert DataFrame to markdown-like table
                table_text = df.to_string(index=True)

                # Add summary statistics for numeric columns
                numeric_cols = df.select_dtypes(include=["number"]).columns
                if len(numeric_cols) > 0:
                    summary = "\n\nSummary Statistics:\n"
                    summary += df[numeric_cols].describe().to_string()
                    table_text += summary

                sheet_content = sheet_header + table_text

                # Split into chunks if too large
                sheet_chunks = self._split_text(sheet_content, max_tokens=1000)
                chunks.extend(sheet_chunks)

        except Exception as e:
            print(f"Error parsing Excel {filename}: {e}")
            # Try to extract at least basic info
            try:
                excel_file = io.BytesIO(content)
                df = pd.read_excel(excel_file, engine="openpyxl")
                if not df.empty:
                    chunks.append(
                        f"Excel file: {filename}\nData preview:\n{df.head(10).to_string()}"
                    )
            except:
                pass

        return chunks if chunks else [f"[Excel file: {filename} - could not parse]"]

    def _parse_csv(self, content: bytes, filename: str) -> List[str]:
        """Extract data from CSV files and format as text"""
        chunks = []
        try:
            csv_file = io.BytesIO(content)

            # Try different encodings
            encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
            df = None

            for encoding in encodings:
                try:
                    csv_file.seek(0)
                    df = pd.read_csv(csv_file, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None or df.empty:
                return [f"[CSV file: {filename} - empty or could not parse]"]

            # Create structured text representation
            csv_header = f"CSV File: {filename}\n"
            csv_header += "=" * 50 + "\n\n"

            # Convert DataFrame to text
            table_text = df.to_string(index=True)

            # Add summary statistics for numeric columns
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                summary = "\n\nSummary Statistics:\n"
                summary += df[numeric_cols].describe().to_string()
                table_text += summary

            csv_content = csv_header + table_text

            # Split into chunks if too large
            csv_chunks = self._split_text(csv_content, max_tokens=1000)
            chunks.extend(csv_chunks)

        except Exception as e:
            print(f"Error parsing CSV {filename}: {e}")
            chunks.append(f"[CSV file: {filename} - parsing error: {str(e)}]")

        return chunks if chunks else [f"[CSV file: {filename} - could not parse]"]

    def _split_text(self, text: str, max_tokens: int = 1000) -> List[str]:
        """Split text into chunks respecting sentence boundaries"""
        sentences = text.replace("\n", " ").split(". ")
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence.split())

            if current_length + sentence_length > max_tokens and current_chunk:
                chunks.append(". ".join(current_chunk) + ".")
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        if current_chunk:
            chunks.append(". ".join(current_chunk))

        return [chunk for chunk in chunks if chunk.strip()]
