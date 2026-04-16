#!/usr/bin/env python3
"""
MCP (Model Context Protocol) server for the AI Cockpit Modernization API.

This server exposes tools for agents to interact with the modernization API,
enabling documentation generation, project management, and task tracking.

Available tools:
    create_project           – Create a new project
    list_projects            – List all projects
    get_project              – Get project details
    upload_project_zip       – Upload and index sources
    generate_docs            – Create a documentation task
    get_docs_status          – Get documentation task status
    get_docs_results         – Get documentation task results
    list_docs_tasks          – List project documentation tasks

Usage:
    # Set environment variables:
    export MODERNIZATION_API_KEY=your-api-key-here     # required
    export MODERNIZATION_ORG_ID=686                    # required
    export MODERNIZATION_API_URL=http://localhost:3000 # optional
    export MODERNIZATION_LLM_PROVIDER=awsbedrockai     # optional
    export MODERNIZATION_LLM_MODEL=claude-3-5-sonnet   # optional
    export MODERNIZATION_OUTPUT_LANGUAGE=en_US         # optional, default en_US

    # Run the MCP server:
    python mcp_client.py

Dependencies (install separately if not present):
    pip install mcp requests
"""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

import requests

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_modernization")

# ---------------------------------------------------------------------------
# Configuration – read from environment variables
# ---------------------------------------------------------------------------
API_BASE_URL: str = os.environ.get("MODERNIZATION_API_URL", "https://aic-modernization-api.compass.uol/").rstrip("/")
API_KEY: str = os.environ.get("MODERNIZATION_API_KEY", "")
_org_id_raw: str = os.environ.get("MODERNIZATION_ORG_ID", "")
ORG_ID: Optional[int] = int(_org_id_raw) if _org_id_raw.strip() else None
LLM_PROVIDER: Optional[str] = os.environ.get("MODERNIZATION_LLM_PROVIDER") or None
LLM_MODEL: Optional[str] = os.environ.get("MODERNIZATION_LLM_MODEL") or None
OUTPUT_LANGUAGE: str = os.environ.get("MODERNIZATION_OUTPUT_LANGUAGE") or "en_US"
POLL_INTERVAL_MS: int = int(os.environ.get("MODERNIZATION_POLL_INTERVAL_MS", "30000"))

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _headers() -> Dict[str, str]:
    """Return common request headers including API key authentication."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-API-Key": API_KEY,
    }


def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Perform a synchronous GET request and return parsed JSON (or text)."""
    url = f"{API_BASE_URL}{path}"
    logger.debug("GET %s params=%s", url, params)
    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=60)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return resp.json()
        return resp.text
    except requests.HTTPError as exc:
        body = exc.response.text if exc.response is not None else str(exc)
        raise RuntimeError(f"HTTP {exc.response.status_code if exc.response is not None else '?'}: {body}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc


def _post(path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    """Perform a synchronous POST request and return parsed JSON."""
    url = f"{API_BASE_URL}{path}"
    logger.debug("POST %s body=%s", url, payload)
    try:
        resp = requests.post(url, headers=_headers(), json=payload or {}, timeout=60)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
    except requests.HTTPError as exc:
        body = exc.response.text if exc.response is not None else str(exc)
        raise RuntimeError(f"HTTP {exc.response.status_code if exc.response is not None else '?'}: {body}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc


def _put_binary(url: str, data: bytes, content_type: str = "application/zip") -> None:
    """Upload binary data to a presigned URL (no auth headers needed)."""
    logger.debug("PUT (presigned) %s content_type=%s size=%d", url, content_type, len(data))
    try:
        resp = requests.put(url, data=data, headers={"Content-Type": content_type, "x-amz-server-side-encryption": "aws:kms"}, timeout=300)
        resp.raise_for_status()
    except requests.HTTPError as exc:
        body = exc.response.text if exc.response is not None else str(exc)
        raise RuntimeError(f"Upload failed – HTTP {exc.response.status_code if exc.response is not None else '?'}: {body}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Upload request failed: {exc}") from exc


# ---------------------------------------------------------------------------
# MCP server definition
# ---------------------------------------------------------------------------
try:
    from mcp.server.fastmcp import FastMCP
except ImportError as _exc:
    print(
        "ERROR: The 'mcp' package is not installed.\n"
        "Install it with:  pip install mcp\n"
        f"Original error: {_exc}",
        file=sys.stderr,
    )
    sys.exit(1)

mcp = FastMCP(
    "modernization-api",
    instructions=(
        "Tools for interacting with the AI Cockpit Modernization API. "
        "Use these tools to manage projects, trigger documentation generation tasks, "
        "monitor task progress, and retrieve generated documentation."
    ),
)


# ---------------------------------------------------------------------------
# Tool: create_project
# ---------------------------------------------------------------------------
@mcp.tool()
def create_project(
    name: str,
    description: Optional[str] = None
) -> str:
    """Create a new modernization project.

    Args:
        name: Human-readable project name (must be unique within the organization).
        description: Optional free-text description of the project.

    Returns:
        JSON string with the created project details including its ``id``.
    """
    payload: Dict[str, Any] = {
        "name": name,
        "organization_id": ORG_ID,
    }
    if description:
        payload["description"] = description
    
    payload["languages"] = ["generic"]

    try:
        result = _post("/projects", payload)
        logger.info("Created project id=%s name=%s", result.get("id"), name)
        return json.dumps(result, default=str)
    except RuntimeError as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: list_projects
# ---------------------------------------------------------------------------
@mcp.tool()
def list_projects(
    limit: int = 20,
    offset: int = 0,
) -> str:
    """List projects for the configured organization.

    Args:
        limit: Maximum number of projects to return (1–100, default 20).
        offset: Number of projects to skip for pagination (default 0).

    Returns:
        JSON string with ``items`` (list of projects), ``total``, ``has_more``,
        ``limit``, and ``offset`` fields.
    """
    params: Dict[str, Any] = {"limit": limit, "offset": offset, "organization_id": ORG_ID}

    try:
        result = _get("/projects", params=params)
        return json.dumps(result, default=str)
    except RuntimeError as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: get_project
# ---------------------------------------------------------------------------
@mcp.tool()
def get_project(project_id: str) -> str:
    """Retrieve full details for a single project.

    Args:
        project_id: The unique identifier of the project (e.g. ``"abc12345"``).

    Returns:
        JSON string with project details including state, languages, and timestamps.
    """
    try:
        result = _get(f"/projects/{project_id}")
        return json.dumps(result, default=str)
    except RuntimeError as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: upload_project_zip
# ---------------------------------------------------------------------------
@mcp.tool()
def upload_project_zip(
    project_id: str,
    file_path: str,
) -> str:
    """Upload a ZIP file containing project source code and automatically start indexing.

    The tool performs three steps:
    1. Requests a presigned upload URL from the API.
    2. Uploads the local ZIP file directly to object storage using that URL.
    3. Automatically triggers the indexing process so the project transitions
       to ``READY`` state.

    Args:
        project_id: ID of the project to upload files for.
        file_path: Absolute or relative path to the local ``.zip`` file.

    Returns:
        JSON string with ``{"status": "indexed", "key": "<s3-key>", ...}`` on
        success, or ``{"error": "..."}`` on failure.
    """
    import os as _os

    if not _os.path.isfile(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    filename = _os.path.basename(file_path)

    # Step 1 – obtain presigned URL
    try:
        upload_info = _post(
            f"/projects/{project_id}/upload",
            {
                "filename": filename,
                "content_type": "application/zip",
            },
        )
    except RuntimeError as exc:
        return json.dumps({"error": f"Failed to get upload URL: {exc}"})

    presigned_url: Optional[str] = upload_info.get("upload_url")
    key: Optional[str] = upload_info.get("key")

    if not presigned_url:
        return json.dumps({"error": "API did not return a presigned upload URL", "response": upload_info})

    # Step 2 – upload the file
    try:
        with open(file_path, "rb") as fh:
            file_data = fh.read()
        _put_binary(presigned_url, file_data, content_type="application/zip")
        logger.info("Uploaded %s (%d bytes) to key=%s", filename, len(file_data), key)
    except (RuntimeError, OSError) as exc:
        return json.dumps({"error": f"Upload failed: {exc}"})

    # Step 3 – automatically trigger indexing
    try:
        url = f"{API_BASE_URL}/projects/{project_id}/confirm-indexing"
        resp = requests.post(
            url,
            headers=_headers(),
            params={"skip_pre_analysis": "true"},
            timeout=60,
        )
        resp.raise_for_status()
        indexing_result = resp.json() if resp.content else {"status": "ok"}
        logger.info("Indexing triggered for project=%s", project_id)
    except requests.HTTPError as exc:
        body = exc.response.text if exc.response is not None else str(exc)
        return json.dumps({
            "status": "uploaded",
            "key": key,
            "filename": filename,
            "size_bytes": len(file_data),
            "indexing_error": f"HTTP {exc.response.status_code if exc.response is not None else '?'}: {body}",
        })
    except requests.RequestException as exc:
        return json.dumps({
            "status": "uploaded",
            "key": key,
            "filename": filename,
            "size_bytes": len(file_data),
            "indexing_error": f"Indexing request failed: {exc}",
        })

    return json.dumps({
        "status": "indexed",
        "key": key,
        "filename": filename,
        "size_bytes": len(file_data),
        "indexing": indexing_result,
    })


# ---------------------------------------------------------------------------
# Tool: generate_docs
# ---------------------------------------------------------------------------
@mcp.tool()
def generate_docs(
    project_id: str,
    name: str,
) -> str:
    """Create and start a full-documentation generation task for a project.

    The project must be in ``READY`` state (i.e. indexed) before a task can be
    created.  The task runs asynchronously; use ``get_docs_status`` to poll
    progress.

    The organization is determined automatically from the ``MODERNIZATION_ORG_ID``
    environment variable configured at server startup.

    Args:
        project_id: ID of the project to document.
        name: Human-readable name for this task run.

    Returns:
        JSON string with the created task including its ``id`` and initial
        ``status``.
    """
    payload: Dict[str, Any] = {
        "project_id": project_id,
        "organization_id": ORG_ID,
        "name": name,
        "output_language": OUTPUT_LANGUAGE,
        "options": {
            "enrichment": True,
            "overview": True,
            "epics": True,
            "diagrams": False,
            "user_stories": True,
            "business_analysis": True,
            "graph_network": False,
        },
    }
    if LLM_PROVIDER:
        payload["llm_provider"] = LLM_PROVIDER
    if LLM_MODEL:
        payload["llm_model"] = LLM_MODEL

    try:
        result = _post("/tasks/full-documentation", payload)
        logger.info("Created task id=%s project=%s", result.get("id"), project_id)
        return json.dumps(result, default=str)
    except RuntimeError as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: get_docs_status
# ---------------------------------------------------------------------------
@mcp.tool()
def get_docs_status(task_id: str) -> str:
    """Get the current status and step-by-step progress of a documentation task.

    Args:
        task_id: The unique identifier of the task returned by ``generate_docs``.

    Returns:
        JSON string with ``id``, ``status`` (one of ``PENDING``, ``STARTED``,
        ``SUCCESS``, ``FAILURE``, ``REVOKED``), ``steps`` (list of step objects
        with their individual statuses and recent log lines), ``timestamps``, and
        ``pollAfterMs`` (milliseconds to wait before polling again).
    """
    try:
        result = _get(f"/tasks/{task_id}/status")
        if isinstance(result, dict):
            result["pollAfterMs"] = POLL_INTERVAL_MS
        return json.dumps(result, default=str)
    except RuntimeError as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: get_docs_results
# ---------------------------------------------------------------------------
@mcp.tool()
def get_docs_results(task_id: str) -> str:
    """Get a presigned download URL for the completed task's output ZIP archive.

    The task must be in ``SUCCESS`` state.  The returned URL is temporary
    (expires after a short period).

    Args:
        task_id: The unique identifier of a successfully completed task.

    Returns:
        JSON string with ``download_url``, ``filename``, ``key``, and
        ``expires_in`` (seconds).
    """
    try:
        result = _get(f"/tasks/{task_id}/results")
        return json.dumps(result, default=str)
    except RuntimeError as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Tool: list_docs_tasks
# ---------------------------------------------------------------------------
@mcp.tool()
def list_docs_tasks(project_id: str) -> str:
    """List all documentation tasks associated with a project.

    Args:
        project_id: ID of the project whose tasks to list.

    Returns:
        JSON string with ``tasks`` (list of task summaries, each containing
        ``id``, ``name``, ``task_type``, ``status``, ``created_at``, and
        ``has_artifact``) and ``pollAfterMs`` (milliseconds to wait before
        polling again).
    """
    try:
        result = _get(f"/projects/{project_id}/tasks")
        if isinstance(result, dict):
            result["pollAfterMs"] = POLL_INTERVAL_MS
        elif isinstance(result, list):
            result = {"tasks": result, "pollAfterMs": POLL_INTERVAL_MS}
        return json.dumps(result, default=str)
    except RuntimeError as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the MCP server.

    The server communicates over stdio (standard input/output) as required by
    the Model Context Protocol.  Configure it via environment variables:

        MODERNIZATION_API_URL         – Base URL of the modernization API
                                        (default: http://localhost:3000)
        MODERNIZATION_API_KEY         – API key for authentication (required)
        MODERNIZATION_ORG_ID          – Organization ID used by all tools that
                                        need one (``create_project``,
                                        ``list_projects``, ``generate_docs``).
                                        **Required** – the server will not start
                                        without this variable.
        MODERNIZATION_LLM_PROVIDER    – Default LLM provider for task creation
                                        (e.g. ``"anthropic"``, ``"openai"``,
                                        ``"bedrock"``).  Optional; the API
                                        chooses a provider when omitted.
        MODERNIZATION_LLM_MODEL       – Default LLM model for task creation
                                        (e.g. ``"claude-3-5-sonnet"``,
                                        ``"gpt-4"``).  Optional; the API
                                        chooses a model when omitted.
        MODERNIZATION_OUTPUT_LANGUAGE – Language code for generated documentation
                                        (``"en_US"``, ``"pt_BR"``, ``"es_ES"``).
                                        Defaults to ``"en_US"`` when omitted.
        MODERNIZATION_POLL_INTERVAL_MS – Milliseconds that polling tools
                                        (``get_docs_status``, ``list_docs_tasks``)
                                        suggest the caller wait between polls via
                                        the ``pollAfterMs`` response field.
                                        Defaults to ``30000`` (30 seconds).

    Example:
        MODERNIZATION_API_URL=https://api.example.com \\
        MODERNIZATION_API_KEY=sk-... \\
        MODERNIZATION_ORG_ID=42 \\
        MODERNIZATION_LLM_PROVIDER=anthropic \\
        MODERNIZATION_LLM_MODEL=claude-3-5-sonnet \\
        MODERNIZATION_OUTPUT_LANGUAGE=pt_BR \\
        python mcp_client.py
    """
    if not API_KEY:
        logger.warning(
            "MODERNIZATION_API_KEY is not set. "
            "All API calls will fail with 401 Unauthorized."
        )
    if ORG_ID is None:
        logger.error(
            "MODERNIZATION_ORG_ID is not set. "
            "This environment variable is required – the server cannot start without it."
        )
        sys.exit(1)

    logger.info(
        "Starting MCP server 'modernization-api' targeting %s "
        "(org_id=%s, llm_provider=%s, llm_model=%s, output_language=%s)",
        API_BASE_URL,
        ORG_ID,
        LLM_PROVIDER or "<api-default>",
        LLM_MODEL or "<api-default>",
        OUTPUT_LANGUAGE,
    )
    mcp.run()


if __name__ == "__main__":
    main()