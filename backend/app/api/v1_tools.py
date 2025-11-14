"""Security tools execution API routes."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.task import Task, TaskResult
from app.api.deps import get_current_user
from app.services.tool_integration import ToolIntegration
from app.services.tool_result_service import ToolResultService
from app.schemas.task import TaskResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolExecutionRequest:
    """Request model for tool execution."""

    def __init__(
        self,
        tool_name: str,
        target: str,
        options: Optional[Dict[str, Any]] = None,
        poc_file: Optional[str] = None,
        templates: Optional[str] = None,
    ):
        self.tool_name = tool_name
        self.target = target
        self.options = options or {}
        self.poc_file = poc_file
        self.templates = templates


@router.get("/task/{task_id}/results", response_model=dict)
async def get_task_tool_results(
    task_id: int,
    tool_name: Optional[str] = Query(None, description="Filter by tool name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get tool execution results for a specific task.

    Args:
        task_id: Task ID
        tool_name: Optional tool name filter (afrog, dddd, fscan, nuclei, dirsearch)

    Returns:
        List of tool results with statistics
    """
    try:
        # Verify task exists and user has access
        from sqlalchemy import select
        stmt = select(Task).where(Task.id == task_id)
        result = await db.execute(stmt)
        task = result.scalars().first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        # Get tool results
        tool_results = await ToolResultService.get_tool_results(db, task_id, tool_name)

        # Get statistics
        stats = await ToolResultService.get_task_statistics(db, task_id)

        return {
            "code": 0,
            "message": "success",
            "data": {
                "task_id": task_id,
                "task_name": task.name,
                "task_status": task.status,
                "results": tool_results,
                "statistics": stats,
                "total_results": len(tool_results),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task tool results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tool results"
        )


@router.post("/task/{task_id}/execute-and-store", response_model=dict)
async def execute_tool_and_store(
    task_id: int,
    tool_name: str = Query(..., description="Tool name"),
    target: str = Query(..., description="Target"),
    options: Optional[Dict[str, Any]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute a tool and automatically store results in database.

    This endpoint combines tool execution with database storage,
    making it convenient for integrated scanning workflows.

    Args:
        task_id: Task ID to associate with results
        tool_name: Tool to execute
        target: Target address
        options: Tool-specific options

    Returns:
        Execution and storage result
    """

    # Validate tool
    tool_name = tool_name.lower()
    if tool_name not in ToolIntegration.TOOLS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown tool: {tool_name}"
        )

    # Check tool installed
    if not ToolIntegration.check_tool_installed(tool_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool '{tool_name}' is not installed"
        )

    # Verify task exists
    from sqlalchemy import select
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalars().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    try:
        # Build options
        if options is None:
            options = {}

        # Execute tool
        if tool_name == "afrog":
            tool_result = await ToolIntegration.scan_with_afrog(
                target=target,
                options=options
            )
        elif tool_name == "dddd":
            tool_result = await ToolIntegration.scan_with_dddd(
                target=target,
                options=options
            )
        elif tool_name == "fscan":
            tool_result = await ToolIntegration.scan_with_fscan(
                target=target,
                options=options
            )
        elif tool_name == "nuclei":
            tool_result = await ToolIntegration.scan_with_nuclei(
                target=target,
                options=options
            )
        elif tool_name == "dirsearch":
            tool_result = await ToolIntegration.scan_with_dirsearch(
                target=target,
                options=options
            )
        else:
            raise ValueError(f"Unsupported tool: {tool_name}")

        # Process and store result
        storage_result = await ToolResultService.process_and_store_result(
            db=db,
            task_id=task_id,
            tool_name=tool_name,
            scan_result=tool_result,
        )

        logger.info(f"Tool executed and results stored: {tool_name} on {target}")

        return {
            "code": 0,
            "message": "success",
            "data": {
                "execution": tool_result,
                "storage": storage_result,
                "task_id": task_id,
            }
        }

    except Exception as e:
        logger.error(f"Error executing and storing tool result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution and storage failed: {str(e)}"
        )


@router.get("/available", response_model=dict)
async def get_available_tools(
    current_user: User = Depends(get_current_user),
):
    """
    Get list of available security tools and their installation status.

    Returns:
        Dictionary with tool names and installation status
    """
    try:
        installed_tools = ToolIntegration.get_installed_tools()

        return {
            "code": 0,
            "message": "success",
            "data": {
                "tools": ToolIntegration.TOOLS,
                "installed": installed_tools,
                "summary": {
                    "total": len(installed_tools),
                    "installed_count": sum(1 for v in installed_tools.values() if v),
                    "available_count": sum(1 for v in installed_tools.values() if not v),
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting available tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available tools"
        )


@router.get("/status", response_model=dict)
async def get_tools_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed status of all available tools.

    Returns:
        Dictionary with tool status, version info, and capabilities
    """
    try:
        status_info = {}

        for tool_name, tool_info in ToolIntegration.TOOLS.items():
            is_installed = ToolIntegration.check_tool_installed(tool_name)

            status_info[tool_name] = {
                "name": tool_info.get("name"),
                "description": tool_info.get("description"),
                "installed": is_installed,
                "url": tool_info.get("url"),
                "capabilities": tool_info.get("capabilities", []),
                "output_format": tool_info.get("output_format"),
            }

        return {
            "code": 0,
            "message": "success",
            "data": status_info
        }

    except Exception as e:
        logger.error(f"Error getting tools status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tools status"
        )


@router.post("/execute", response_model=dict)
async def execute_tool(
    tool_name: str = Query(..., description="Tool name (afrog, dddd, fscan, nuclei, dirsearch)"),
    target: str = Query(..., description="Target IP, URL, or CIDR range"),
    poc_file: Optional[str] = Query(None, description="POC file path (for afrog)"),
    templates: Optional[str] = Query(None, description="Template filter (for nuclei)"),
    timeout: Optional[int] = Query(None, description="Command timeout in seconds"),
    threads: Optional[int] = Query(None, ge=1, le=100, description="Number of threads"),
    ports: Optional[str] = Query(None, description="Port specification (for fscan)"),
    wordlist: Optional[str] = Query(None, description="Wordlist path (for dirsearch)"),
    extensions: Optional[str] = Query(None, description="File extensions (for dirsearch)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute a security tool on a target.

    Supported tools:
    - afrog: Vulnerability scanning with POC execution
    - dddd: Advanced vulnerability scanning
    - fscan: Port scanning and service detection
    - nuclei: Template-based vulnerability scanning
    - dirsearch: Directory enumeration

    Args:
        tool_name: Name of the tool to execute
        target: Target IP, URL, or CIDR range
        poc_file: Path to POC file (for afrog)
        templates: Template filter (for nuclei)
        timeout: Command timeout in seconds
        threads: Number of worker threads
        ports: Port specification (for fscan)
        wordlist: Wordlist path (for dirsearch)
        extensions: File extensions (for dirsearch)

    Returns:
        Tool execution results
    """

    # Validate tool name
    tool_name = tool_name.lower()
    if tool_name not in ToolIntegration.TOOLS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown tool: {tool_name}. Supported tools: {', '.join(ToolIntegration.TOOLS.keys())}"
        )

    # Check if tool is installed
    if not ToolIntegration.check_tool_installed(tool_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool '{tool_name}' is not installed. "
                   f"Please install from: {ToolIntegration.TOOLS[tool_name]['url']}"
        )

    # Build options dictionary
    options = {}
    if timeout:
        options["timeout"] = timeout
    if threads:
        options["threads"] = threads
    if ports:
        options["ports"] = ports
    if wordlist:
        options["wordlist"] = wordlist
    if extensions:
        options["extensions"] = extensions

    try:
        # Execute tool based on type
        if tool_name == "afrog":
            result = await ToolIntegration.scan_with_afrog(
                target=target,
                poc_file=poc_file,
                options=options
            )

        elif tool_name == "dddd":
            result = await ToolIntegration.scan_with_dddd(
                target=target,
                options=options
            )

        elif tool_name == "fscan":
            result = await ToolIntegration.scan_with_fscan(
                target=target,
                options=options
            )

        elif tool_name == "nuclei":
            result = await ToolIntegration.scan_with_nuclei(
                target=target,
                templates=templates,
                options=options
            )

        elif tool_name == "dirsearch":
            result = await ToolIntegration.scan_with_dirsearch(
                target=target,
                options=options
            )

        else:
            raise ValueError(f"Unsupported tool: {tool_name}")

        # Log execution
        logger.info(f"Tool execution completed: {tool_name} on {target}, status: {result.get('status')}")

        return {
            "code": 0,
            "message": "success",
            "data": result
        }

    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}"
        )


@router.post("/chain/execute", response_model=dict)
async def execute_tool_chain(
    target: str = Query(..., description="Target IP, URL, or CIDR range"),
    tools: str = Query(..., description="Comma-separated tool names (afrog, dddd, fscan, nuclei, dirsearch)"),
    timeout: Optional[int] = Query(None, description="Command timeout in seconds"),
    threads: Optional[int] = Query(None, ge=1, le=100, description="Number of threads"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute multiple tools in sequence on a target.

    Executes tools in the order specified and aggregates results.

    Args:
        target: Target IP, URL, or CIDR range
        tools: Comma-separated tool names (e.g., "fscan,nuclei,afrog")
        timeout: Command timeout in seconds
        threads: Number of worker threads

    Returns:
        Aggregated results from all tools
    """

    # Parse tool list
    tool_list = [t.strip().lower() for t in tools.split(",")]

    # Validate tool names
    invalid_tools = [t for t in tool_list if t not in ToolIntegration.TOOLS]
    if invalid_tools:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown tools: {', '.join(invalid_tools)}. "
                   f"Supported tools: {', '.join(ToolIntegration.TOOLS.keys())}"
        )

    # Check if all tools are installed
    missing_tools = [t for t in tool_list if not ToolIntegration.check_tool_installed(t)]
    if missing_tools:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tools not installed: {', '.join(missing_tools)}"
        )

    # Build options
    options = {}
    if timeout:
        options["timeout"] = timeout
    if threads:
        options["threads"] = threads

    try:
        # Execute tool chain
        result = await ToolIntegration.execute_tool_chain(
            target=target,
            tools=tool_list,
            options=options
        )

        logger.info(f"Tool chain execution completed: {tool_list} on {target}")

        return {
            "code": 0,
            "message": "success",
            "data": result
        }

    except Exception as e:
        logger.error(f"Tool chain execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool chain execution failed: {str(e)}"
        )


@router.post("/execute-with-task", response_model=dict)
async def execute_tool_with_task(
    task_id: int = Query(..., description="Task ID to associate with tool execution"),
    tool_name: str = Query(..., description="Tool name"),
    target: str = Query(..., description="Target"),
    options: Optional[Dict[str, Any]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute a tool and store results in a task.

    This endpoint integrates tool execution with the task management system,
    allowing results to be tracked and managed alongside other scan results.

    Args:
        task_id: Task ID to store results under
        tool_name: Name of the tool
        target: Target address
        options: Tool-specific options

    Returns:
        Execution result with task integration
    """

    # Validate tool
    tool_name = tool_name.lower()
    if tool_name not in ToolIntegration.TOOLS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown tool: {tool_name}"
        )

    # Check tool installed
    if not ToolIntegration.check_tool_installed(tool_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool '{tool_name}' is not installed"
        )

    # Verify task exists and belongs to user
    from sqlalchemy import select
    stmt = select(Task).where(Task.id == task_id)
    task_result = await db.execute(stmt)
    task = task_result.scalars().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    try:
        # Execute tool
        if options is None:
            options = {}

        if tool_name == "afrog":
            result = await ToolIntegration.scan_with_afrog(
                target=target,
                options=options
            )
        elif tool_name == "dddd":
            result = await ToolIntegration.scan_with_dddd(target=target, options=options)
        elif tool_name == "fscan":
            result = await ToolIntegration.scan_with_fscan(target=target, options=options)
        elif tool_name == "nuclei":
            result = await ToolIntegration.scan_with_nuclei(target=target, options=options)
        elif tool_name == "dirsearch":
            result = await ToolIntegration.scan_with_dirsearch(target=target, options=options)
        else:
            raise ValueError(f"Unsupported tool: {tool_name}")

        # Store result in database
        task_result_record = TaskResult(
            task_id=task_id,
            result_type=f"tool_{tool_name}",
            result_data=result,
            created_at=datetime.utcnow()
        )
        db.add(task_result_record)
        await db.commit()

        logger.info(f"Tool result stored for task {task_id}: {tool_name}")

        return {
            "code": 0,
            "message": "success",
            "data": {
                "task_id": task_id,
                "tool": tool_name,
                "result": result,
                "stored": True
            }
        }

    except Exception as e:
        logger.error(f"Error executing tool with task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}"
        )


@router.get("/{tool_name}/info", response_model=dict)
async def get_tool_info(
    tool_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information about a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool information including description, capabilities, and requirements
    """

    tool_name = tool_name.lower()

    if tool_name not in ToolIntegration.TOOLS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found"
        )

    tool_info = ToolIntegration.TOOLS[tool_name]
    is_installed = ToolIntegration.check_tool_installed(tool_name)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "name": tool_info.get("name"),
            "description": tool_info.get("description"),
            "url": tool_info.get("url"),
            "installed": is_installed,
            "capabilities": tool_info.get("capabilities", []),
            "output_format": tool_info.get("output_format"),
            "usage_examples": get_tool_usage_examples(tool_name)
        }
    }


def get_tool_usage_examples(tool_name: str) -> Dict[str, Any]:
    """Get usage examples for a specific tool."""

    examples = {
        "afrog": {
            "basic": "/api/v1/tools/execute?tool_name=afrog&target=http://example.com",
            "with_poc": "/api/v1/tools/execute?tool_name=afrog&target=http://example.com&poc_file=/path/to/poc.yaml",
            "with_options": "/api/v1/tools/execute?tool_name=afrog&target=http://example.com&timeout=60&threads=10"
        },
        "dddd": {
            "basic": "/api/v1/tools/execute?tool_name=dddd&target=192.168.1.100",
            "with_options": "/api/v1/tools/execute?tool_name=dddd&target=192.168.1.100&timeout=120"
        },
        "fscan": {
            "single_host": "/api/v1/tools/execute?tool_name=fscan&target=192.168.1.100",
            "cidr_range": "/api/v1/tools/execute?tool_name=fscan&target=192.168.1.0/24",
            "specific_ports": "/api/v1/tools/execute?tool_name=fscan&target=192.168.1.100&ports=22,80,443,3306"
        },
        "nuclei": {
            "basic": "/api/v1/tools/execute?tool_name=nuclei&target=http://example.com",
            "cves": "/api/v1/tools/execute?tool_name=nuclei&target=http://example.com&templates=cves",
            "osint": "/api/v1/tools/execute?tool_name=nuclei&target=http://example.com&templates=osint"
        },
        "dirsearch": {
            "basic": "/api/v1/tools/execute?tool_name=dirsearch&target=http://example.com",
            "custom_wordlist": "/api/v1/tools/execute?tool_name=dirsearch&target=http://example.com&wordlist=/path/to/wordlist.txt",
            "specific_extensions": "/api/v1/tools/execute?tool_name=dirsearch&target=http://example.com&extensions=php,html,txt"
        }
    }

    return examples.get(tool_name, {})
