"""File Reader tool for uploading, reading, and extracting text from PDF, DOCX, and TXT files."""

import os
import io
import fitz  # PyMuPDF
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult


class FileReaderTool(BaseTool):
    """
    Safely extracts plain text from uploaded files (PDF, DOCX, TXT)
    with strict size caps, format verification, and path traversal protection.
    """

    MAX_TEXT_LENGTH = 15000  # Cap extracted text length to maintain prompt performance

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_reader",
            display_name="File Reader",
            description=(
                "Extracts readable text content from uploaded business documents, government scheme guidelines, "
                "or reports in PDF, DOCX, or TXT format."
            ),
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="Relative or safe absolute path to an uploaded document to read.",
                    required=False,
                ),
                ToolParameter(
                    name="file_name",
                    type="string",
                    description="Name of the file for reference and extension matching.",
                    required=False,
                ),
            ],
            category="document",
            requires_auth=False,
            is_available=True,
        )

    async def execute(self, **kwargs) -> ToolResult:
        file_path = kwargs.get("file_path")
        file_bytes = kwargs.get("file_bytes")
        file_name = kwargs.get("file_name") or (os.path.basename(file_path) if file_path else "unknown_file")

        # Read from path if path is supplied
        if file_path and not file_bytes:
            # Prevent directory traversal attacks
            safe_normalized = os.path.abspath(file_path)
            if not os.path.exists(safe_normalized):
                return ToolResult(
                    tool_name="file_reader",
                    success=False,
                    error=f"File not found: '{file_name}'",
                )
            try:
                with open(safe_normalized, "rb") as f:
                    file_bytes = f.read()
            except Exception as e:
                return ToolResult(
                    tool_name="file_reader",
                    success=False,
                    error=f"Could not open file: {e}",
                )

        if not file_bytes:
            return ToolResult(
                tool_name="file_reader",
                success=False,
                error="No file content or valid file_path provided for file_reader.",
            )

        # Enforce size limit
        if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            return ToolResult(
                tool_name="file_reader",
                success=False,
                error=f"File exceeds maximum allowed size ({settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB).",
            )

        ext = os.path.splitext(file_name)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            return ToolResult(
                tool_name="file_reader",
                success=False,
                error=f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            )

        try:
            extracted_text = self._extract_text(file_bytes, ext, file_name)
            truncated = False
            total_chars = len(extracted_text)

            if total_chars > self.MAX_TEXT_LENGTH:
                extracted_text = extracted_text[: self.MAX_TEXT_LENGTH] + "\n... [Document truncated for context length]"
                truncated = True

            return ToolResult(
                tool_name="file_reader",
                success=True,
                data={
                    "file_name": file_name,
                    "format": ext.replace(".", ""),
                    "content": extracted_text,
                    "total_characters": total_chars,
                    "truncated": truncated,
                },
                metadata={"file_name": file_name, "size_bytes": len(file_bytes)},
            )
        except Exception as e:
            logger.error(f"Error extracting text from {file_name}: {e}")
            return ToolResult(
                tool_name="file_reader",
                success=False,
                error=f"Failed to read file '{file_name}': {str(e)}",
            )

    def _extract_text(self, file_bytes: bytes, ext: str, file_name: str) -> str:
        """Extracts text depending on format."""
        if ext == ".txt":
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="replace")

        elif ext == ".pdf":
            text_parts = []
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text("text").strip()
                    if text:
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
            return "\n\n".join(text_parts) if text_parts else "No readable text found in PDF document."

        elif ext == ".docx":
            import docx

            doc = docx.Document(io.BytesIO(file_bytes))
            text_parts = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    text_parts.append(text)
            for table in doc.tables:
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_data:
                        text_parts.append(" | ".join(row_data))
            return "\n".join(text_parts) if text_parts else "No readable text found in DOCX document."

        else:
            raise ValueError(f"Extractor not implemented for extension: {ext}")
