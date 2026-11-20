"""Tool management and document upload routes for Illusion AI."""

import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.core.config import settings
from app.core.logging import logger
from app.tools.registry import tool_registry
from app.tools.base import ToolDefinition, ToolResult
from app.tools.file_reader.tool import FileReaderTool

router = APIRouter(prefix="/tools", tags=["Tools"])


from pydantic import BaseModel, Field

class DirectToolExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


@router.get("/", response_model=List[ToolDefinition])
async def list_available_tools() -> List[ToolDefinition]:
    """
    Returns the catalogue of all registered AI tools with descriptions and parameters.
    """
    return tool_registry.list_tools()


@router.post("/execute", response_model=Dict[str, Any])
async def execute_tool_direct(req: DirectToolExecuteRequest) -> Dict[str, Any]:
    """
    Direct tool execution endpoint for the Tools Studio GUI Console.
    Allows testing web_search, rag_search, calculator, etc. directly with instant output.
    """
    tool = tool_registry.get(req.tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{req.tool_name}' not found in registry.",
        )

    try:
        res: ToolResult = await tool.execute(**req.arguments)
        return {
            "tool_name": res.tool_name,
            "success": res.success,
            "data": res.data,
            "error": res.error,
            "metadata": res.metadata,
        }
    except Exception as e:
        logger.error(f"Error executing tool {req.tool_name} directly: {e}")
        return {
            "tool_name": req.tool_name,
            "success": False,
            "data": None,
            "error": str(e),
            "metadata": {},
        }


@router.post("/upload", response_model=Dict[str, Any])
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Securely uploads and extracts text from a PDF, DOCX, or TXT file using FileReaderTool.
    Performs file extension validation, size cap checks, and sanitized extraction.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a valid filename.",
        )

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    try:
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size ({max_mb} MB).",
            )

        reader: FileReaderTool = tool_registry.get("file_reader")
        if not reader:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="File reader tool is not initialized.",
            )

        result: ToolResult = await reader.execute(
            file_bytes=contents,
            file_name=file.filename,
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result.error or "Failed to extract text from document.",
            )

        return {
            "status": "success",
            "file_name": file.filename,
            "format": ext.replace(".", ""),
            "size_bytes": len(contents),
            "data": result.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error handling file upload '{file.filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file upload: {str(e)}",
        )
